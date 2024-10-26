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
import soundfile as sf
from PIL import Image
import io
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def play_audio_simple(audio_data):
    """シンプルな音声再生関数"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        # 音声データを読み込み
        data, samplerate = sf.read(temp_audio_path)
        
        # デフォルトデバイスで再生
        sd.play(data, samplerate)
        sd.wait()  # 再生完了まで待機
        logger.info("Audio playback completed")
        
        # 一時ファイルの削除
        os.unlink(temp_audio_path)
        
    except Exception as e:
        logger.error(f"Error in play_audio_simple: {str(e)}")

async def synthesize_voicevox(text: str):
    """VOICEVOXを使用して音声合成を行い、直接再生"""
    url = "http://localhost:50021"
    
    try:
        # VOICEVOXで音声合成
        query_response = requests.post(
            f"{url}/audio_query",
            params={
                "text": text,
                "speaker": 2
            }
        )
        
        if query_response.status_code != 200:
            logger.error(f"Audio query failed: {query_response.status_code}")
            return None
            
        query_data = query_response.json()
        
        # 音声パラメータ設定
        query_data.update({
            "volumeScale": 1.0,
            "outputSamplingRate": 48000,  # 標準的なサンプリングレート
            "outputStereo": True,         # ステレオ出力
            "intonationScale": 1.0,
            "speedScale": 1.0,
            "prePhonemeLength": 0.1,
            "postPhonemeLength": 0.1
        })
        
        # 音声合成を実行
        synthesis_response = requests.post(
            f"{url}/synthesis",
            params={"speaker": 2},
            headers={
                "accept": "audio/wav",
                "Content-Type": "application/json"
            },
            json=query_data
        )
        
        if synthesis_response.status_code != 200:
            logger.error(f"Synthesis failed: {synthesis_response.status_code}")
            return None

        # 直接再生
        await play_audio_simple(synthesis_response.content)
        return True
            
    except Exception as e:
        logger.error(f"Error in synthesize_voicevox: {str(e)}")
        return None

def check_system_setup():
    """VOICEVOXの起動確認"""
    logger.info("\nSystem Setup Check:")
    
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
        
        # リップシンク準備の確認メッセージを送信
        await websocket.send_text(json.dumps({
            "type": "setup_instruction",
            "message": "3teneの準備ができたら開始します"
        }))
        
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
        cap = cv2.VideoCapture(0)
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
        detection_timeout = 30
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
        # リップシンク準備の確認を送信
        await websocket.send_text(json.dumps({
            "type": "lip_sync_ready",
            "message": "インタビューを開始します"
        }))
        
        # Greeting
        greeting = "こんにちは！青春ソングを作るためのインタビューを始めましょう。各質問に一言で答えてください。"
        await synthesize_voicevox(greeting)
        await websocket.send_text(greeting)
        await asyncio.sleep(0.5)

        # Questions and answers with lip sync
        for i, question in enumerate(QUESTIONS):
            await asyncio.sleep(0.5)
            
            # Ask question
            await synthesize_voicevox(question)
            await websocket.send_text(question)
            await asyncio.sleep(0.5)
            
            # Get response
            response = await websocket.receive_text()
            answers[f"answer_{i+1}"] = response
        
        # Final message
        end_message = "ありがとうございます。ミュージックビデオの生成を開始します。"
        await synthesize_voicevox(end_message)
        await websocket.send_text(end_message)
        await asyncio.sleep(0.5)
        
        # Generate song and video
        await generate_song(websocket)
        
    except Exception as e:
        logger.error(f"Interview error: {str(e)}")
        raise

async def generate_song(websocket: WebSocket):
    """Handle the song generation process and websocket communication"""
    try:
        themes = list(answers.values())
        
        # Start lyrics generation
        await websocket.send_text(json.dumps({
            "type": "status_update",
            "status": "generating_lyrics"
        }))

        lyrics = await generate_lyrics({"info": " ".join(themes)})
        
        # Start music generation
        await websocket.send_text(json.dumps({
            "type": "status_update",
            "status": "generating_music"
        }))

        # Generate music
        music = await generate_music({
            "themes": themes,
            "lyrics": lyrics["lyrics"]
        })

        if "error" in music:
            # Handle error case
            await websocket.send_text(json.dumps({
                "type": "music_error",
                "data": music["error"]
            }))
        else:
            # Handle success case
            await synthesize_voicevox("楽曲が完成しました。別タブで自動的に再生されます。")
            
            # Send completion message with video URL
            await websocket.send_text(json.dumps({
                "type": "music_complete",
                "data": {
                    "video_url": music["video_url"]
                }
            }))

            logger.info("Song generation and notification completed successfully")

    except Exception as e:
        logger.error(f"Song generation error: {str(e)}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Failed to generate song: {str(e)}"
        }))
        raise

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    client = speech.SpeechClient()
    temp_audio_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            temp_audio_path = temp_audio.name
            temp_audio.write(await file.read())

        with open(temp_audio_path, "rb") as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="ja-JP",
        )

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
    """Generate music using Suno AI with no repeats"""
    suno_api_url = "https://api.goapi.ai/api/suno/v1/music"
    
    headers = {
        "X-API-Key": SUNO_API_KEY,
        "Content-Type": "application/json"
    }
    
    themes = request.get("themes", [])
    themes_text = " ".join(themes)
    
    # メロディーとセクションの両方についてリピート禁止を指定
    description = (
        f"J-pop about {themes_text}. "
        "One intro, verse, chorus. No melody repeats. No section repeats. Single take. Female JP vocal."
    )
    
    # 文字数チェック
    if len(description) > 200:
        max_themes_length = 100  # より短いテーマ長を確保
        if len(themes_text) > max_themes_length:
            themes_text = themes_text[:max_themes_length] + "..."
            description = (
                f"J-pop about {themes_text}. "
                "One-shot song. No repeats. Female JP vocal."
            )
    
    logger.info(f"Prompt length: {len(description)} characters")
    
    payload = {
        "custom_mode": False,
        "mv": "chirp-v3-5",
        "input": {
            "gpt_description_prompt": description,
            "make_instrumental": False,
            "voice": "female",
            "style": "j-pop",
            "temperature": 0.3,  # さらに決定論的に
            "voice_settings": {
                "gender": "female",
                "language": "japanese",
                "style": "clear",
                "variation": "single"  # バリエーションを制限
            }
        }
    }
    
    try:
        logger.info(f"Starting music generation with no-repeat constraint")
        logger.info(f"Using prompt: {description}")
        
        response = requests.post(suno_api_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            logger.error(f"API Error: Status {response.status_code}")
            logger.error(f"Response: {response.text}")
            response.raise_for_status()
        
        task_data = response.json()
        task_id = task_data['data']['task_id']
        logger.info(f"Task ID: {task_id}")
        
        # 進捗モニタリング
        max_attempts = 120
        current_attempt = 0
        last_progress = -1
        
        while current_attempt < max_attempts:
            try:
                status_response = requests.get(f"{suno_api_url}/{task_id}", headers=headers)
                status_response.raise_for_status()
                status_data = status_response.json()

                if 'data' not in status_data:
                    logger.error("Invalid response structure")
                    logger.debug(f"Response data: {status_data}")
                    raise ValueError("Invalid response format")

                status = status_data['data'].get('status')
                
                if status == 'completed':
                    video_url = None
                    
                    if 'video_url' in status_data['data']:
                        video_url = status_data['data']['video_url']
                    elif 'output' in status_data['data'] and 'video_url' in status_data['data']['output']:
                        video_url = status_data['data']['output']['video_url']
                    elif 'clips' in status_data['data']:
                        clips = status_data['data']['clips']
                        if clips and isinstance(clips, dict):
                            first_clip = next(iter(clips.values()))
                            if 'video_url' in first_clip:
                                video_url = first_clip['video_url']

                    if not video_url:
                        raise ValueError("No video URL found in response")

                    logger.info("Music generation completed successfully")
                    return {
                        "video_url": video_url
                    }

                elif status == 'failed':
                    error_message = status_data['data'].get('error', 'Unknown error')
                    logger.error(f"Generation failed: {error_message}")
                    raise ValueError(f"Generation failed: {error_message}")

                elif status == 'processing':
                    progress = status_data['data'].get('progress', 0)
                    if progress != last_progress:
                        logger.info(f"Progress: {progress}%")
                        last_progress = progress
                    current_attempt += 1
                    await asyncio.sleep(5)

                else:
                    logger.warning(f"Unknown status: {status}")
                    current_attempt += 1
                    await asyncio.sleep(5)

            except requests.RequestException as e:
                logger.error(f"Network error: {e}")
                current_attempt += 1
                await asyncio.sleep(5)
                continue

        logger.error("Generation timed out")
        raise TimeoutError("Music generation timed out")
            
    except Exception as e:
        logger.error(f"Error in music generation: {str(e)}")
        return {"error": f"Failed to generate music: {str(e)}"}
        
    finally:
        logger.debug("Generation attempt completed")

if __name__ == "__main__":
    import uvicorn
    check_system_setup()
    uvicorn.run(app, host="0.0.0.0", port=8000)