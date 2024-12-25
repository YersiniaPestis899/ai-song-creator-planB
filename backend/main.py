import os
import requests
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import boto3
from google.cloud import speech
from dotenv import load_dotenv
from typing import Dict, List
import logging
import sounddevice as sd
import soundfile as sf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def play_audio_simple(audio_data):
    """Simple audio playback function"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(audio_data)
            temp_audio_path = temp_audio.name

        data, samplerate = sf.read(temp_audio_path)
        sd.play(data, samplerate)
        sd.wait()
        logger.info("Audio playback completed")
        
        os.unlink(temp_audio_path)
        
    except Exception as e:
        logger.error(f"Error in play_audio_simple: {str(e)}")

async def synthesize_voicevox(text: str):
    """Synthesize voice using VOICEVOX"""
    url = "http://localhost:50021"
    
    try:
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
        query_data.update({
            "volumeScale": 1.0,
            "outputSamplingRate": 48000,
            "outputStereo": True,
            "intonationScale": 1.0,
            "speedScale": 1.0,
            "prePhonemeLength": 0.1,
            "postPhonemeLength": 0.1
        })
        
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

        await play_audio_simple(synthesis_response.content)
        return True
            
    except Exception as e:
        logger.error(f"Error in synthesize_voicevox: {str(e)}")
        return None

def check_system_setup():
    """Check VOICEVOX status"""
    logger.info("\nSystem Setup Check:")
    
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

# Interview questions
QUESTIONS = [
    "あなたの青春時代を一言で表すと？",
    "その時期にあなたが最も夢中になっていたものは？",
    "青春時代の挫折や失敗を乗り越えた時の気持ちを一言で？",
    "その頃のあなたにとって最も大切だったものは？",
    "今、あの頃の自分に伝えたい言葉を一つ挙げるとしたら？"
]

@app.post("/start")
async def start_interview():
    """Start the interview process"""
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
    """Get a specific interview question"""
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
    """Synthesize text to speech"""
    try:
        await synthesize_voicevox(text["message"])
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in speech synthesis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/submit-answer")
async def submit_answer(answer_data: dict):
    """Submit an interview answer"""
    try:
        logger.info(f"Received answer: {answer_data}")
        return {
            "status": "success",
            "message": "Answer received"
        }
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_lyrics(request: Dict[str, List[str]]):
    """Generate lyrics based on answers"""
    try:
        answers = request.get("answers", [])
        
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

            await synthesize_voicevox(
                "歌詞の生成が完了しました。"
            )

            return {
                "status": "success",
                "message": "歌詞が生成されました",
                "data": {
                    "lyrics": lyrics,
                    "title": "Generated Lyrics"
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
    """Convert audio to text"""
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

if __name__ == "__main__":
    import uvicorn
    check_system_setup()
    uvicorn.run(app, host="0.0.0.0", port=8000)
