import os
import requests
import json
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import boto3
from google.cloud import speech
from dotenv import load_dotenv
from typing import List, Dict, Any
import asyncio
import cv2
import numpy as np
import wave
import logging
import sounddevice as sd
from PIL import Image
import io
import soundfile as sf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_audio_setup():
    """Check VOICEVOX and audio device setup"""
    logger.info("Checking system setup...")
    
    # Check VOICEVOX
    try:
        response = requests.get("http://localhost:50021/speakers")
        if response.status_code == 200:
            logger.info("✓ VOICEVOX engine is running")
            speakers = response.json()
            logger.info(f"✓ Found {len(speakers)} speakers")
        else:
            logger.error(f"× VOICEVOX engine error: {response.status_code}")
    except Exception as e:
        logger.error(f"× VOICEVOX connection error: {str(e)}")

    # List audio devices
    try:
        devices = sd.query_devices()
        logger.info("\nAudio Devices:")
        
        for idx, device in enumerate(devices):
            logger.info(f"[{idx}] {device['name']}")
            if device['max_output_channels'] > 0:
                logger.info(f"   ✓ Output device found (ID: {idx})")
            if device['max_input_channels'] > 0:
                logger.info(f"   ✓ Input device found (ID: {idx})")
                
    except Exception as e:
        logger.error(f"× Error checking audio devices: {str(e)}")

async def play_audio(audio_data):
    """クロスプラットフォーム対応の音声再生関数"""
    try:
        # 一時ファイルを作成して音声データを書き込む
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        # soundfileを使用して音声を読み込む
        data, samplerate = sf.read(temp_audio_path)
        
        # sounddeviceを使用して音声を再生
        sd.play(data, samplerate)
        sd.wait()  # 再生が終わるまで待機
        
        # 一時ファイルを削除
        os.unlink(temp_audio_path)
        
    except Exception as e:
        logger.error(f"Error playing audio: {str(e)}")

def get_vb_cable_device():
    """VB-Cable出力デバイスのインデックスを取得（MacOS対応）"""
    try:
        devices = sd.query_devices()
        for idx, device in enumerate(devices):
            # MacOSでの完全一致検出
            if device['name'] == 'VB-Cable' and device['max_output_channels'] > 0:
                logger.info(f"✓ Using VB-Cable device at index {idx} for audio output")
                return idx
        
        logger.warning("VB-Cable device not found, using default output device")
        return sd.default.device[1]  # デフォルト出力デバイス
    except Exception as e:
        logger.error(f"Error finding VB-Cable device: {str(e)}")
        return sd.default.device[1]  # エラー時もデフォルトデバイスを返す

def check_system_audio():
    """システムの音声設定を確認（MacOS対応）"""
    try:
        devices = sd.query_devices()
        logger.info("\nSystem Audio Configuration:")
        
        vb_cable_found = False
        
        # オーディオデバイスの確認
        for idx, device in enumerate(devices):
            logger.info(f"[{idx}] {device['name']}")
            
            # MacOSでのVB-Cable検出に対応
            if any(name in device['name'] for name in ['VB-Cable', 'CABLE Input']):
                vb_cable_found = True
                logger.info(f"   ✓ VB-Cable device found (ID: {idx})")
                logger.info(f"   Channels: {device['max_input_channels']} in, {device['max_output_channels']} out")
            
            if device['max_output_channels'] > 0:
                logger.info(f"   ✓ Output device detected (ID: {idx})")
            if device['max_input_channels'] > 0:
                logger.info(f"   ✓ Input device detected (ID: {idx})")
        
        if not vb_cable_found:
            logger.warning("× VB-Cable not found - 3tene lip sync may not work")
        
        # VOICEVOXの確認
        response = requests.get("http://localhost:50021/speakers")
        if response.status_code == 200:
            logger.info("✓ VOICEVOX engine is running")
            logger.info("✓ API endpoint is accessible")
        
    except Exception as e:
        logger.error(f"Error checking system audio setup: {str(e)}")

async def play_audio_to_vb_cable(audio_data):
    """VB-Cable経由で音声を再生（MacOS対応）"""
    try:
        # VB-Cableデバイスのインデックスを取得
        device_idx = get_vb_cable_device()
        logger.info(f"Selected audio output device ID: {device_idx}")

        # 一時ファイルを作成して音声データを書き込む
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        # soundfileを使用して音声を読み込む
        data, samplerate = sf.read(temp_audio_path)
        
        # VB-Cable経由で音声を再生
        try:
            devices = sd.query_devices()
            logger.info(f"Playing audio through: {devices[device_idx]['name']}")
            sd.play(data, samplerate, device=device_idx)
            sd.wait()  # 再生完了まで待機
            logger.info("Audio playback completed successfully")
        except Exception as e:
            logger.error(f"Error during audio playback: {str(e)}")
            # エラー時はデフォルトデバイスで再試行
            logger.info("Retrying with default audio device")
            sd.play(data, samplerate)
            sd.wait()
        
        # 一時ファイルを削除
        os.unlink(temp_audio_path)
        
    except Exception as e:
        logger.error(f"Error in play_audio_to_vb_cable: {str(e)}")

async def synthesize_voicevox(text: str):
    """Synthesize speech using VOICEVOX and play through VB-Cable"""
    url = "http://localhost:50021"
    
    try:
        logger.info(f"Synthesizing text: {text}")
        
        # Step 1: Generate audio query
        query_response = requests.post(
            f"{url}/audio_query",
            params={
                "text": text,
                "speaker": 2  # VOICEVOXのスピーカーID
            }
        )
        if query_response.status_code != 200:
            logger.error(f"Audio query failed: {query_response.status_code}")
            return None
            
        query_data = query_response.json()
        
        # 音声合成のパラメータを調整（3teneのリップシンクに適した設定）
        query_data.update({
            "volumeScale": 1.0,
            "outputSamplingRate": 48000,  # サンプリングレートを48kHzに設定
            "outputStereo": False,  # モノラル出力
            "intonationScale": 1.0,
            "speedScale": 1.0,
            "prePhonemeLength": 0.1,    # 少し長めに設定
            "postPhonemeLength": 0.1    # 少し長めに設定
        })
        
        # Step 2: Synthesize speech
        synthesis_response = requests.post(
            f"{url}/synthesis",
            params={
                "speaker": 2
            },
            headers={
                "accept": "audio/wav",
                "Content-Type": "application/json"
            },
            json=query_data
        )
        
        if synthesis_response.status_code != 200:
            logger.error(f"Synthesis failed: {synthesis_response.status_code}")
            return None

        # VB-Cable経由で音声を再生
        await play_audio_to_vb_cable(synthesis_response.content)
        return synthesis_response.content
        
    except Exception as e:
        logger.error(f"Error in synthesize_voicevox: {str(e)}")
        return None

def check_system_audio():
    """システムの音声設定を確認（MacOS対応）"""
    try:
        devices = sd.query_devices()
        logger.info("\nSystem Audio Configuration:")
        
        vb_cable_found = False
        
        # オーディオデバイスの確認
        for idx, device in enumerate(devices):
            logger.info(f"[{idx}] {device['name']}")
            device_info = []
            
            # 出力チャンネルの確認
            if device['max_output_channels'] > 0:
                device_info.append("✓ Output device detected")
            
            # 入力チャンネルの確認
            if device['max_input_channels'] > 0:
                device_info.append("✓ Input device detected")
            
            # MacOS用のVB-Cable検出
            if device['name'] == 'VB-Cable':  # 完全一致で検出
                vb_cable_found = True
                device_info.append(f"✓ VB-Cable detected - IO Channels: {device['max_input_channels']} in, {device['max_output_channels']} out")
            
            # デバイス情報をログ出力
            for info in device_info:
                logger.info(f"   {info}")
        
        if vb_cable_found:
            logger.info("✓ VB-Cable is properly configured")
        else:
            logger.warning("× VB-Cable not found - 3tene lip sync may not work")
        
        # VOICEVOXの確認
        response = requests.get("http://localhost:50021/speakers")
        if response.status_code == 200:
            logger.info("✓ VOICEVOX engine is running")
            logger.info("✓ API endpoint is accessible")
        
    except Exception as e:
        logger.error(f"Error checking system audio setup: {str(e)}")

# 起動時のチェックを実行
check_system_audio()

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure AWS Bedrock
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

# Suno API Key
SUNO_API_KEY = os.getenv('SUNO_API_KEY')

# Interview questions
QUESTIONS = [
    "あなたの青春時代を一言で表すと？",
    "その時期にあなたが最も夢中になっていたものは？",
    "青春時代の挫折や失敗を乗り越えた時の気持ちを一言で？",
    "その頃のあなたにとって最も大切だったものは？",
    "今、あの頃の自分に伝えたい言葉を一つ挙げるとしたら？"
]

# Store answers
answers = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket.accept()
        logger.info("WebSocket connected")
        
        while True:
            try:
                data = await websocket.receive_text()
                if data == "start_camera":
                    await detect_person(websocket)
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected normally")
                break
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                try:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "An error occurred processing your request"
                    }))
                except:
                    pass
                break
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass

async def detect_person(websocket: WebSocket):
    cap = None
    try:
        cap = cv2.VideoCapture(0)  # MacOSでは0がデフォルトのカメラデバイス
        if not cap.isOpened():
            logger.error("Failed to open camera")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to open camera"
            }))
            return

        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            logger.error("Failed to load face cascade classifier")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to initialize face detection"
            }))
            return

        person_detected = False
        detection_timeout = 30  # 30秒のタイムアウト
        start_time = time.time()

        while not person_detected:
            if time.time() - start_time > detection_timeout:
                logger.warning("Face detection timeout")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Face detection timeout. Please try again."
                }))
                break

            ret, frame = cap.read()
            if not ret:
                logger.warning("Failed to read frame from camera")
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                person_detected = True
                logger.info("Person detected successfully")
                await websocket.send_text("person_detected")
                await asyncio.sleep(0.5)
                await start_interview(websocket)
                break

            await asyncio.sleep(0.1)

    except Exception as e:
        logger.error(f"Face detection error: {str(e)}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Face detection error: {str(e)}"
            }))
        except:
            pass
    finally:
        if cap is not None:
            cap.release()
            logger.info("Camera released")

async def start_interview(websocket: WebSocket):
    try:
        # Greeting
        greeting = "こんにちは！青春ソングを作るためのインタビューを始めましょう。各質問に一言で答えてください。"
        await synthesize_voicevox(greeting)
        await websocket.send_text(greeting)
        await asyncio.sleep(0.5)

        # Questions and answers
        for i, question in enumerate(QUESTIONS):
            await asyncio.sleep(0.5)
            
            # Ask question
            await synthesize_voicevox(question)
            await websocket.send_text(question)
            await asyncio.sleep(0.5)
            
            # Get response
            response = await websocket.receive_text()
            answers[f"answer_{i+1}"] = response
        
        # 終了メッセージ
        end_message = "ありがとうございます。音楽の生成を開始します。"
        await synthesize_voicevox(end_message)
        await websocket.send_text(end_message)
        await asyncio.sleep(0.5)
        
        # Generate song
        await generate_song(websocket)
        
    except Exception as e:
        logger.error(f"Interview error: {str(e)}")
        raise

async def generate_song(websocket: WebSocket):
    try:
        themes = list(answers.values())
        
        # 歌詞生成開始を通知
        await websocket.send_text(json.dumps({
            "type": "status_update",
            "status": "generating_lyrics"
        }))

        # Generate lyrics
        lyrics = await generate_lyrics({"info": " ".join(themes)})
        
        # 音楽生成開始を通知
        await websocket.send_text(json.dumps({
            "type": "status_update",
            "status": "generating_music"
        }))

        # Generate music using Suno
        music = await generate_music({
            "themes": themes,
        })

        if "error" in music:
            await websocket.send_text(json.dumps({
                "type": "music_error",
                "data": music["error"]
            }))
        else:
            await websocket.send_text(json.dumps({
                "type": "music_complete",
                "data": {
                    "audio_url": music["audio_url"],
                    "video_url": music["video_url"]
                }
            }))

    except Exception as e:
        logger.error(f"Song generation error: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Failed to generate song: {str(e)}"
        }))
        raise

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe audio using Google Cloud Speech-to-Text"""
    client = speech.SpeechClient()
    temp_audio_path = None

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio_path = temp_audio.name
            temp_audio.write(await file.read())

        # Read audio file
        with open(temp_audio_path, "rb") as audio_file:
            content = audio_file.read()

        # Configure speech recognition
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="ja-JP",
        )

        # Perform transcription
        response = client.recognize(config=config, audio=audio)
        transcription = response.results[0].alternatives[0].transcript if response.results else ""

        return {"transcription": transcription}

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except Exception as e:
                logger.error(f"Failed to delete temp file: {e}")

@app.post("/generate_lyrics")
async def generate_lyrics(request: Dict[str, str]):
    """Generate lyrics using AWS Bedrock"""
    prompt = f"""以下の単語をテーマにして、<Verse>、<Verse 2>、<Chorus>の構造を持つ歌詞を作成してください。各セクションを明確に区別し、以下のフォーマットで記述してください：

<Verse>
(ここに1番の歌詞)

<Verse 2>
(ここに2番の歌詞)

<Chorus>
(ここにサビの歌詞)

テーマ：{request['info']}"""
    
    try:
        response = bedrock.invoke_model(
            modelId=os.getenv('CLAUDE_MODEL_ID'),
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 200000,
                "messages": [{"role": "user", "content": prompt}]
            })
        )
        response_body = json.loads(response['body'].read())
        lyrics = response_body['content'][0]['text']
        return {"lyrics": lyrics}

    except Exception as e:
        logger.error(f"Lyrics generation error: {str(e)}")
        raise

async def generate_music(request: Dict[str, Any]):
    """Generate music using Suno AI with improved handling"""
    suno_api_url = "https://api.goapi.ai/api/suno/v1/music"
    
    headers = {
        "X-API-Key": SUNO_API_KEY,
        "Content-Type": "application/json"
    }
    
    themes = request.get("themes", [])
    description = f"A Japanese pop song with female vocals. The song should be emotional and reflect these themes: {' '.join(themes)}"
    
    payload = {
        "custom_mode": False,
        "mv": "chirp-v3-5",
        "input": {
            "gpt_description_prompt": description,
            "make_instrumental": False,
            "voice": "female",
            "style": "j-pop",
            "temperature": 0.7,
            "top_k": 50,
            "top_p": 0.95,
            "voice_settings": {
                "gender": "female",
                "style": "clear and emotional",
                "language": "japanese"
            },
            "music_settings": {
                "genre": "j-pop",
                "mood": "emotional",
                "tempo": "medium",
                "energy_level": "moderate"
            }
        }
    }
    
    try:
        logger.info(f"Starting music generation with description: {description}")
        response = requests.post(suno_api_url, headers=headers, json=payload)
        response.raise_for_status()
        
        music_data = response.json()
        task_id = music_data['data']['task_id']
        logger.info(f"Music generation task started with ID: {task_id}")
        
        max_attempts = 60
        current_attempt = 0
        
        while current_attempt < max_attempts:
            status_response = requests.get(f"{suno_api_url}/{task_id}", headers=headers)
            status_data = status_response.json()
            
            if status_data['data']['status'] == 'completed':
                clips = status_data['data']['clips']
                if not clips:
                    logger.error("No clips found in completed response")
                    return {"error": "No music clips were generated"}
                
                for clip_id, clip in clips.items():
                    logger.info(f"Clip {clip_id}: Duration = {clip.get('duration', 0)} seconds")
                
                longest_clip = max(clips.values(), key=lambda x: x.get('duration', 0))
                
                logger.info(f"Selected clip duration: {longest_clip.get('duration')} seconds")
                logger.info(f"Audio URL: {longest_clip.get('audio_url')}")
                logger.info(f"Video URL: {longest_clip.get('video_url')}")
                
                return {
                    "audio_url": longest_clip['audio_url'],
                    "video_url": longest_clip['video_url'],
                }
                
            elif status_data['data']['status'] == 'failed':
                error_message = status_data['data'].get('error', 'Unknown error')
                logger.error(f"Music generation failed: {error_message}")
                return {"error": f"Music generation failed: {error_message}"}
            
            elif status_data['data']['status'] == 'processing':
                progress = status_data['data'].get('progress', 0)
                logger.info(f"Generation progress: {progress}%")
            
            current_attempt += 1
            await asyncio.sleep(5)
        
        logger.error("Music generation timed out")
        return {"error": "Music generation timed out after 5 minutes"}

    except requests.RequestException as e:
        logger.error(f"Music generation request error: {str(e)}")
        return {"error": f"Failed to generate music: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error in music generation: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)