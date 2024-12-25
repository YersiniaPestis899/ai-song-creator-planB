# AI Song Creator

A web application that generates lyrics using AI based on users' memories and experiences.

## Features

1. Interactive Memory Collection
   - Interactive interview-style memory gathering
   - Voice input response capability
   - Real-time text-to-speech question reading

2. AI Content Generation
   - Lyrics generation using AWS Bedrock
   - Voice synthesis using VOICEVOX

3. User Experience
   - Progressive web application design
   - Mobile-responsive interface
   - Real-time voice feedback

## Technical Stack

### Frontend
- React.js
- Tailwind CSS
- Axios
- Audio recording and playback capabilities

### Backend
- FastAPI
- Integration with AI services:
  - AWS Bedrock (lyrics generation)
  - Google Cloud Speech-to-Text (voice recognition)
  - VOICEVOX (voice synthesis)

## Setup

### Prerequisites
- Node.js (LTS version)
- Python 3.8 or higher
- VOICEVOX Engine
- AWS Account with Bedrock access
- Google Cloud Account with Speech-to-Text API enabled

### Installation Steps

1. Clone the repository
```bash
git clone https://github.com/YersiniaPestis899/ai-song-creator-planB.git
cd ai-song-creator-planB
```

2. Frontend Setup
```bash
cd frontend
npm install
```

3. Backend Setup
```bash
cd backend
pip install -r requirements.txt
```

4. Environment Configuration

Create a `.env` file in the backend directory with the following variables:
```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
CLAUDE_MODEL_ID=anthropic.claude-3
GOOGLE_APPLICATION_CREDENTIALS=path_to_credentials.json
```

### Running the Application

1. Start VOICEVOX
```bash
# Ensure VOICEVOX engine is running on port 50021
```

2. Launch Backend
```bash
cd backend
python main.py
```

3. Start Frontend
```bash
cd frontend
npm start
```

The application will be available at `http://localhost:3000` by default.

## API Endpoints

### Core Endpoints
- `POST /start` - Initialize interview session
- `GET /questions/{index}` - Retrieve interview questions
- `POST /speak` - Synthesize speech from text
- `POST /submit-answer` - Process user responses
- `POST /generate` - Generate lyrics based on answers
- `POST /transcribe` - Convert voice input to text

## Development Guidelines

1. Error Handling
- Comprehensive error logging
- Graceful degradation
- User-friendly error messages

2. Performance Optimization
- Efficient file handling
- Connection pooling
- Retry mechanisms for external services

3. Security Considerations
- Environment variable management
- CORS configuration
- Temporary file cleanup

## License

This project is licensed under the MIT License.

## Acknowledgments

- VOICEVOX Project
- AWS Bedrock
- Google Cloud
- All open-source contributors

## Support

For bug reports or feature requests, please use the GitHub Issues section.
