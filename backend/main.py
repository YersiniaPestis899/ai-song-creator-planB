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
                "speaker": 8
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

# Topmedia API Key
TOPMEDIA_API_KEY = os.getenv('TOPMEDIA_API_KEY')

# Interview questions
QUESTIONS = [
    "あなたの青春時代を一言で表すと？",
    "その時期にあなたが最も夢中になっていたものは？",
    "青春時代の挫折や失敗を乗り越えた時の気持ちを一言で？",
    "その頃のあなたにとって最も大切だったものは？",
    "今、あの頃の自分に伝えたい言葉を一つ挙げるとしたら？"
]

# インタビュー開始エンドポイント
@app.post("/start")
async def start_interview():
    """インタビューを開始する"""
    try:
        greeting = "こんにちは！青春ソングを作るためのインタビューを始めましょう。各質問に一言で答えてください。"
        return {
            "message": greeting,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/questions/{index}")
async def get_question(index: int):
    """質問を取得する"""
    try:
        if index < 0 or index >= len(QUESTIONS):
            raise HTTPException(status_code=400, detail="Invalid question index")
        
        question = QUESTIONS[index]
        return {
            "message": question,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/speak")
async def speak_text(text: dict):
    """テキストを音声合成する"""
    try:
        await synthesize_voicevox(text["message"])
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in speech synthesis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/submit-answer")
async def submit_answer(answer_data: dict):
    """回答を受け取る"""
    try:
        logger.info(f"Received answer: {answer_data}")
        return {
            "status": "success",
            "message": "Answer received"
        }
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# 音楽生成エンドポイント
@app.post("/generate")
async def generate_music_and_lyrics(request: Dict[str, List[str]]):
    """歌詞を生成する"""
    try:
        answers = request.get("answers", [])
        
        # 歌詞生成のプロンプトを作成
        prompt = f"""以下の単語をテーマにして、青春をテーマにしたJ-POPの歌詞を作成してください。
曲の構成は以下のようにしてください。

<Verse 1>
(1番の歌詞。青春時代の情景や感情を描写。4行程度）

<Verse 2>
(2番の歌詞。青春時代の別の側面や展開を描写。4行程度）

<Chorus>
(サビの歌詞。メッセージや感情の高まりを表現。4-6行程度）

テーマの単語：{", ".join(answers)}"""

        try:
            # AWS Bedrockを使用して歌詞を生成
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

            # VOICEVOXで完了メッセージを再生
            await synthesize_voicevox(
                "歌詞の生成が完了しました。表示された歌詞をコピーして、お好みの音楽生成サービスでご利用ください。"
            )

            return {
                "status": "success",
                "message": "歌詞が生成されました",
                "data": {
                    "lyrics": lyrics,
                    "title": "Generated Lyrics"  # タイトルは固定値または空でもOK
                }
            }

        except Exception as e:
            logger.error(f"Error in lyrics generation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate lyrics: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Error in generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    """音声ファイルをテキストに変換する"""
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
    """回答から歌詞を生成する"""
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

async def generate_lyrics(request: Dict[str, str]):
    """回答から歌詞を生成する"""
    base_url = "https://api.topmediai.com"  # 正しいドメイン

    headers = {
        "x-api-key": TOPMEDIA_API_KEY,
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    # テーマに基づいたプロンプトの作成
    prompt = f"Create J-pop lyrics about: {request['info']}"

    # APIドキュメントに基づいたリクエストペイロード
    payload = {
        "prompt": prompt
    }

    try:
        # 歌詞生成リクエストの送信
        lyrics_url = f"{base_url}/v1/lyrics"
        response = requests.post(
            lyrics_url,
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            logger.error(f"Lyrics generation error: Status {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to generate lyrics: {response.text}"
            )

        lyrics_data = response.json()
        return {"lyrics": lyrics_data.get("lyrics", "")}

    except Exception as e:
        logger.error(f"Lyrics generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate lyrics: {str(e)}"
        )

async def generate_music(request: Dict[str, Any]):
    """Generate music using Topmediai API"""
    base_url = "https://api.topmediai.com"
    
    headers = {
        "x-api-key": TOPMEDIA_API_KEY,
        "accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # セッション設定
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        max_retries=3,  # リトライ回数
        pool_connections=10,  # コネクションプール数
        pool_maxsize=10,  # 最大プールサイズ
        pool_block=False  # ブロッキングしない
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    themes = request.get("themes", [])
    lyrics = request.get("lyrics", "")
    themes_text = " ".join(themes)
    
    # 音楽生成リクエストの送信
    submit_url = f"{base_url}/v2/submit"
    
    payload = {
        "is_auto": 1,
        "prompt": f"Create a J-pop song with these themes: {themes_text}",
        "lyrics": lyrics,
        "title": "AI Music",
        "instrumental": 0,
        "model_version": "v3.5",
        "continue_at": 0,
        "continue_song_id": ""
    }
    
    try:
        logger.info("Starting music generation with Topmediai")
        logger.info(f"Using themes: {themes_text}")
        
        # タイムアウト設定
        timeout = (3000, 30000)  # (接続タイムアウト, 読み取りタイムアウト)
        
        # リトライ用の設定
        max_submit_retries = 3
        current_submit_retry = 0
        
        while current_submit_retry < max_submit_retries:
            try:
                # 生成リクエストの送信
                submit_response = session.post(
                    submit_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                    verify=True  # SSL証明書の検証を有効に
                )
                submit_response.raise_for_status()
                submit_data = submit_response.json()
                
                if submit_data.get("status") != 200:
                    error_message = submit_data.get("message", "Unknown error")
                    if "timeout" in error_message.lower():
                        current_submit_retry += 1
                        logger.warning(f"Generation timeout, retry {current_submit_retry} of {max_submit_retries}")
                        await asyncio.sleep(30)
                        continue
                    else:
                        raise ValueError(f"API Error: {error_message}")
                
                break
                
            except (requests.RequestException, ValueError) as e:
                current_submit_retry += 1
                if current_submit_retry < max_submit_retries:
                    logger.warning(f"Request failed, retry {current_submit_retry} of {max_submit_retries}: {str(e)}")
                    await asyncio.sleep(30)
                else:
                    raise
        
        # レスポンスデータの処理
        response_data = submit_data.get("data", [])
        if not response_data:
            raise ValueError("No data received from API")
        
        first_result = response_data[0]
        song_id = first_result.get("song_id")
        
        if not song_id:
            raise ValueError("No song ID received from API")
        
        logger.info(f"Song ID: {song_id}")
        initial_status = first_result.get("status", "").upper()
        
        # 生成状態の監視が必要な場合
        if initial_status == "RUNNING":
            query_url = f"{base_url}/v2/query"
            max_attempts = 360  # 60分のタイムアウト
            current_attempt = 0
            last_progress = -1
            
            while current_attempt < max_attempts:
                try:
                    # ステータス確認
                    status_response = session.get(
                        query_url,
                        headers=headers,
                        params={"song_id": song_id},
                        timeout=(10, 30),  # ステータスチェックは短めのタイムアウト
                        verify=True
                    )
                    status_response.raise_for_status()
                    status_data = status_response.json()
                    
                    if status_data.get("status") != 200:
                        error_message = status_data.get("message", "Unknown error")
                        if "timeout" in error_message.lower():
                            await asyncio.sleep(30)
                            continue
                        else:
                            raise ValueError(f"Status check failed: {error_message}")
                    
                    song_status = status_data.get("data", {}).get("status", "").upper()
                    progress = status_data.get("data", {}).get("progress", 0)
                    
                    if progress != last_progress:
                        logger.info(f"Generation progress: {progress}%")
                        last_progress = progress
                    
                    if song_status == "COMPLETED":
                        return {
                            "video_url": status_data.get("data", {}).get("url")
                        }
                    elif song_status == "FAILED":
                        raise ValueError("Generation failed")
                    
                    current_attempt += 1
                    # 進捗に応じて待機時間を調整
                    if progress < 30:
                        await asyncio.sleep(20)
                    elif progress < 70:
                        await asyncio.sleep(30)
                    else:
                        await asyncio.sleep(15)
                    
                except requests.RequestException as e:
                    logger.error(f"Network error checking status: {e}")
                    await asyncio.sleep(30)
                    continue
            
            raise TimeoutError("Generation timed out after 60 minutes")
        
        # 即時完了の場合
        return {
            "video_url": first_result.get("audio")
        }
        
    except Exception as e:
        logger.error(f"Error in music generation: {str(e)}")
        return {"error": f"Failed to generate music: {str(e)}"}
    
    finally:
        session.close()
        logger.debug("Generation attempt completed")

if __name__ == "__main__":
    import uvicorn
    check_system_setup()
    uvicorn.run(app, host="0.0.0.0", port=8000)