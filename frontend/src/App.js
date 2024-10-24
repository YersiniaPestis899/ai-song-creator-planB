import React, { useState, useEffect, useRef } from 'react';
import {
  Button,
  TextField,
  Typography,
  Container,
  Box,
  CircularProgress,
  Alert,
  Paper,
  IconButton,
  Stack,
  Snackbar
} from '@mui/material';
import { Mic, Stop, Refresh } from '@mui/icons-material';
import axios from 'axios';

const GenerationProgress = ({ status }) => {
  const getStatusContent = () => {
    switch (status) {
      case 'generating_lyrics':
        return {
          title: '🎨 作詞中...',
          description: 'AIがあなたの回答から歌詞を作成しています',
          color: 'bg-blue-500'
        };
      case 'generating_music':
        return {
          title: '🎵 作曲中...',
          description: '音楽を生成しています（3分程度かかります）',
          color: 'bg-purple-500'
        };
      case 'complete':
        return {
          title: '✨ 完成！',
          description: 'ミュージックビデオを新しいタブで開きます...',
          color: 'bg-green-500'
        };
      default:
        return null;
    }
  };

  const content = getStatusContent();
  if (!content) return null;

  return (
    <div className="w-full max-w-md mx-auto mt-4 p-4 bg-white rounded-lg shadow-lg">
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">{content.title}</h3>
        <p className="text-gray-600">{content.description}</p>
      </div>
      <div className="w-full bg-gray-200 h-2 rounded-full overflow-hidden">
        <div 
          className={`h-full ${content.color} animate-pulse`}
          style={{ 
            width: status === 'complete' ? '100%' : '80%',
            transition: 'width 0.5s ease-in-out'
          }}
        />
      </div>
    </div>
  );
};

function App() {
  // State management
  const [connected, setConnected] = useState(false);
  const [personDetected, setPersonDetected] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [musicError, setMusicError] = useState('');
  const [notification, setNotification] = useState({ type: '', message: '' });
  const [generationStatus, setGenerationStatus] = useState(null);
  
  // Refs
  const ws = useRef(null);
  const mediaRecorder = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // WebSocket connection management
  const connectWebSocket = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    ws.current = new WebSocket('ws://localhost:8000/ws');

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      reconnectAttempts.current = 0;
      setNotification({ type: 'success', message: 'サーバーに接続しました' });
    };

    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
      
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current += 1;
        const timeout = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
        setNotification({ 
          type: 'warning', 
          message: `接続が切断されました。再接続を試みています (${reconnectAttempts.current}/${maxReconnectAttempts})...` 
        });
        setTimeout(connectWebSocket, timeout);
      } else {
        setNotification({ 
          type: 'error', 
          message: '接続を確立できませんでした。ページを更新してください。' 
        });
      }
    };

    ws.current.onmessage = async (event) => {
      try {
        const message = event.data;
        if (typeof message === 'string') {
          try {
            const data = JSON.parse(message);
            if (data.type === 'status_update') {
              setGenerationStatus(data.status);
              setNotification({ 
                type: 'info', 
                message: data.status === 'generating_lyrics' ? '作詞を開始しました' : '作曲を開始しました' 
              });
            } else if (data.type === 'music_complete') {
              setGenerationStatus('complete');
              setMusicError('');
              setNotification({ type: 'success', message: '音楽の生成が完了しました！' });
              // 新しいタブでビデオを開く
              setTimeout(() => {
                window.open(data.data.video_url, '_blank');
              }, 3000); // 3秒後に新しいタブでビデオを開く
            } else if (data.type === 'music_error') {
              setGenerationStatus(null);
              setMusicError(data.data);
              setNotification({ type: 'error', message: `エラーが発生しました: ${data.data}` });
            } else if (data.type === 'error') {
              setNotification({ type: 'error', message: data.message });
            }
          } catch (jsonError) {
            if (message === 'person_detected') {
              setPersonDetected(true);
              setLoading(false);
              setNotification({ type: 'success', message: '人物を検出しました' });
            } else {
              setCurrentQuestion(message);
            }
          }
        }
      } catch (error) {
        console.error('Error processing WebSocket message:', error);
        setNotification({ type: 'error', message: 'メッセージの処理中にエラーが発生しました' });
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setNotification({ type: 'error', message: 'WebSocket接続エラーが発生しました' });
    };
  };

  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  // Camera control
  const startCamera = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send('start_camera');
      setLoading(true);
      setNotification({ type: 'info', message: 'カメラを起動中...' });
    } else {
      setNotification({ type: 'error', message: 'サーバーに接続されていません' });
    }
  };

  // Audio recording management
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      const chunks = [];

      mediaRecorder.current.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.current.onstop = async () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', blob, 'audio.webm');

        try {
          const response = await axios.post('http://localhost:8000/transcribe', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
          setAnswer(response.data.transcription);
          setNotification({ type: 'success', message: '音声を認識しました' });
        } catch (error) {
          console.error('Transcription error:', error);
          setNotification({ type: 'error', message: '音声認識に失敗しました' });
        }
      };

      mediaRecorder.current.start();
      setIsRecording(true);
      setNotification({ type: 'info', message: '録音中...' });
    } catch (error) {
      console.error('Error starting recording:', error);
      setNotification({ type: 'error', message: 'マイクを起動できませんでした' });
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current?.state === 'recording') {
      mediaRecorder.current.stop();
      setIsRecording(false);
    }
  };

  const sendAnswer = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(answer);
      setAnswer('');
      setNotification({ type: 'success', message: '回答を送信しました' });
    } else {
      setNotification({ type: 'error', message: 'サーバーに接続されていません' });
    }
  };

  // Reset application state
  const resetApplication = () => {
    setPersonDetected(false);
    setCurrentQuestion('');
    setAnswer('');
    setLoading(false);
    setIsRecording(false);
    setMusicError('');
    setGenerationStatus(null);
    setNotification({ type: 'info', message: 'アプリケーションをリセットしました' });
  };

  return (
    <Container maxWidth="sm">
      <Box my={4}>
        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h4" component="h1">
              AI Song Creator
            </Typography>
            <IconButton onClick={resetApplication} title="リセット">
              <Refresh />
            </IconButton>
          </Stack>

          <Box my={2} textAlign="center">
            <img
              src="/placeholder-avatar.png"
              alt="Virtual Avatar"
              style={{ 
                width: '200px', 
                height: '200px', 
                borderRadius: '50%',
                border: '2px solid #ccc'
              }}
            />
          </Box>

          {!connected && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              サーバーに接続中です...
            </Alert>
          )}

          {!personDetected ? (
            <Button
              variant="contained"
              color="primary"
              onClick={startCamera}
              disabled={!connected || loading}
              fullWidth
            >
              {loading ? <CircularProgress size={24} /> : 'カメラを起動'}
            </Button>
          ) : (
            <Box>
              <Typography variant="h6" gutterBottom>
                {currentQuestion}
              </Typography>
              
              <TextField
                fullWidth
                variant="outlined"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                disabled={!currentQuestion || isRecording}
                margin="normal"
                placeholder="回答を入力してください"
              />

              <Stack direction="row" spacing={2} my={2}>
                <Button
                  variant="contained"
                  color={isRecording ? "secondary" : "primary"}
                  startIcon={isRecording ? <Stop /> : <Mic />}
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={!currentQuestion}
                >
                  {isRecording ? '録音停止' : '録音開始'}
                </Button>

                <Button
                  variant="contained"
                  color="primary"
                  onClick={sendAnswer}
                  disabled={!answer || isRecording}
                >
                  回答を送信
                </Button>
              </Stack>
            </Box>
          )}

          {generationStatus && (
            <GenerationProgress status={generationStatus} />
          )}

          {musicError && (
            <Alert severity="error" sx={{ my: 2 }}>
              エラーが発生しました: {musicError}
            </Alert>
          )}
        </Paper>
      </Box>

      <Snackbar
        open={!!notification.message}
        autoHideDuration={6000}
        onClose={() => setNotification({ type: '', message: '' })}
      >
        <Alert severity={notification.type || 'info'} onClose={() => setNotification({ type: '', message: '' })}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default App;