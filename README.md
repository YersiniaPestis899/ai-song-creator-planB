# AI Song Creator

AI Song Creator is an interactive web application that generates personalized songs based on user input. It combines computer vision, speech recognition, natural language processing, and music generation to create a unique song creation experience.

## Features

- Face detection to start the interview process
- Voice-based questions and answers
- Text-to-speech for questions
- Speech-to-text for user responses
- AI-powered lyrics generation
- AI-generated music composition

## Technologies Used

- Frontend: React.js
- Backend: FastAPI (Python)
- AI Services:
  - AWS Bedrock (Claude AI) for natural language processing
  - Google Cloud Speech-to-Text for speech recognition
  - VOICEVOX for text-to-speech
  - SOUNDRAW for music generation
- WebSockets for real-time communication

## Prerequisites

- Node.js and npm
- Python 3.7+
- FFmpeg (for audio processing)
- VOICEVOX (running locally)
- AWS account with Bedrock access
- Google Cloud account with Speech-to-Text API enabled
- SOUNDRAW API access

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/ai-song-creator.git
   cd ai-song-creator
   ```

2. Set up the backend:
   ```
   cd backend
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   Create a `.env` file in the `backend` directory with the following content:
   ```
   AWS_REGION=your_aws_region
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   CLAUDE_MODEL_ID=anthropic.claude-3-sonnet-20240620-v1:0
   GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google-credentials.json
   ```

4. Set up the frontend:
   ```
   cd ../frontend
   npm install
   ```

5. Start VOICEVOX on your local machine.

## Running the Application

1. Start the backend server:
   ```
   cd backend
   python main.py
   ```

2. In a new terminal, start the frontend development server:
   ```
   cd frontend
   npm start
   ```

3. Open your browser and navigate to `http://localhost:3000`.

## Usage

1. Allow camera and microphone access when prompted.
2. Click "Start Camera" to begin the interview process.
3. Answer the questions either by speaking or typing.
4. After answering all questions, the application will generate lyrics and music based on your responses.
5. Listen to your personalized song and download it if desired.

## Note

This project uses trial versions of some APIs, which may have limitations. For full functionality, consider upgrading to paid versions of these services.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the [MIT License](LICENSE).