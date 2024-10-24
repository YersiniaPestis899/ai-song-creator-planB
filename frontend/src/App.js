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
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  LinearProgress
} from '@mui/material';
import { Mic, Stop, Refresh, Settings } from '@mui/icons-material';
import axios from 'axios';

// 進行状況表示コンポーネント
const GenerationProgress = ({ status }) => {
  const getStatusContent = () => {
    switch (status) {
      case 'generating_lyrics':
        return {
          title: '🎨 作詞中...',
          description: 'AIがあなたの回答から歌詞を作成しています',
          color: 'primary.light'
        };
      case 'generating_music':
        return {
          title: '🎵 生成中...',
          description: 'ミュージックビデオを生成しています（3分程度かかります）',
          color: 'secondary.light'
        };
      case 'complete':
        return {
          title: '✨ 完成！',
          description: 'ミュージックビデオが生成されました',
          color: 'success.light'
        };
      default:
        return null;
    }
  };

  const content = getStatusContent();
  if (!content) return null;

  return (
    <Paper sx={{ p: 2, my: 2 }}>
      <Typography variant="h6" gutterBottom>
        {content.title}
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {content.description}
      </Typography>
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress 
          variant="indeterminate"
          sx={{ 
            height: 8, 
            borderRadius: 1,
            backgroundColor: 'grey.200',
            '& .MuiLinearProgress-bar': {
              backgroundColor: content.color
            }
          }} 
        />
      </Box>
    </Paper>
  );
};

// 音声設定ダイアログコンポーネント
const AudioSetupDialog = ({ open, onClose }) => (
  <Dialog open={open} onClose={onClose}>
    <DialogTitle>リップシンクの設定方法</DialogTitle>
    <DialogContent>
      <DialogContentText>
        <Typography variant="h6" gutterBottom>
          初期設定手順:
        </Typography>
        <ol style={{ paddingLeft: '20px' }}>
          <li>1. Audio MIDI設定を開く</li>
          <li>2. 左下の+ボタンから「新規マルチ出力デバイス」を作成</li>
          <li>3. 名前を「Music Output」に設定</li>
          <li>4. 以下の出力にチェックを入れる:
            <ul style={{ paddingLeft: '20px', marginTop: '8px' }}>
              <li>- MacBook Airのスピーカー</li>
              <li>- VB-Cable</li>
            </ul>
          </li>
          <li>5. システム設定→サウンド→出力で「Music Output」を選択</li>
          <li>6. 3teneの音声入力で「VB-Cable」を選択</li>
        </ol>
      </DialogContentText>
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose} color="primary">
        設定完了
      </Button>
    </DialogActions>
  </Dialog>
);

const App = () => {
  // State管理
  const [connected, setConnected] = useState(false);
  const [personDetected, setPersonDetected] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [musicError, setMusicError] = useState('');
  const [notification, setNotification] = useState({ type: '', message: '' });
  const [generationStatus, setGenerationStatus] = useState(null);
  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [musicData, setMusicData] = useState(null);
  
  // Refs
  const ws = useRef(null);
  const mediaRecorder = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // WebSocket接続管理
  const connectWebSocket = () => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    ws.current = new WebSocket('ws://localhost:8000/ws');

    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
      reconnectAttempts.current = 0;
      setNotification({ type: 'success', message: 'サーバーに接続しました' });
      setSetupDialogOpen(true);
    };

    ws.current.onmessage = async (event) => {
      try {
        const message = event.data;
        if (typeof message === 'string') {
          try {
            const data = JSON.parse(message);
            
            switch (data.type) {
              case 'setup_instruction':
                setNotification({ type: 'info', message: 'リップシンクの設定を確認してください' });
                setSetupDialogOpen(true);
                break;
                
              case 'status_update':
                setGenerationStatus(data.status);
                setNotification({ 
                  type: 'info', 
                  message: data.status === 'generating_lyrics' ? '作詞を開始しました' : 'ミュージックビデオを生成中です' 
                });
                break;
                
              case 'lip_sync_ready':
                setNotification({ type: 'success', message: 'リップシンクの準備が完了しました' });
                break;
                
              case 'music_complete':
                setGenerationStatus('complete');
                setMusicData(data.data);
                if (data.data.video_url) {
                  window.open(data.data.video_url, '_blank');
                }
                setNotification({ type: 'success', message: 'ミュージックビデオの生成が完了しました！' });
                break;
                
              case 'music_error':
                setGenerationStatus(null);
                setMusicError(data.data);
                setNotification({ type: 'error', message: `エラーが発生しました: ${data.data}` });
                break;
                
              case 'error':
                setNotification({ type: 'error', message: data.message });
                break;
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

    ws.current.onclose = () => {
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
        setNotification({ type: 'error', message: '接続を確立できませんでした。ページを更新してください。' });
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setNotification({ type: 'error', message: 'WebSocket接続エラーが発生しました' });
    };
  };

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (ws.current) ws.current.close();
    };
  }, []);

  const startCamera = () => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send('start_camera');
      setLoading(true);
      setNotification({ type: 'info', message: 'カメラを起動中...' });
    } else {
      setNotification({ type: 'error', message: 'サーバーに接続されていません' });
    }
  };

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

  const resetApplication = () => {
    setPersonDetected(false);
    setCurrentQuestion('');
    setAnswer('');
    setLoading(false);
    setIsRecording(false);
    setMusicError('');
    setGenerationStatus(null);
    setMusicData(null);
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
            <Stack direction="row" spacing={1}>
              <IconButton 
                onClick={() => setSetupDialogOpen(true)} 
                title="リップシンク設定"
                color="primary"
              >
                <Settings />
              </IconButton>
              <IconButton 
                onClick={resetApplication} 
                title="リセット"
              >
                <Refresh />
              </IconButton>
            </Stack>
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

          {generationStatus && <GenerationProgress status={generationStatus} />}

          {musicError && (
            <Alert severity="error" sx={{ my: 2 }}>
              エラーが発生しました: {musicError}
            </Alert>
          )}

          {musicData && (
            <Box mt={4}>
              <Alert severity="success" sx={{ mb: 2 }}>
                ミュージックビデオの生成が完了しました！
                {musicData.video_url && "新しいタブで自動的に開かれます"}
              </Alert>

              {musicData.video_url && (
                <Button
                  variant="contained"
                  color="primary"
                  fullWidth
                  onClick={() => window.open(musicData.video_url, '_blank')}
                  sx={{ mt: 2 }}
                >
                  ミュージックビデオを開く
                </Button>
              )}
            </Box>
          )}
        </Paper>
      </Box>

      <AudioSetupDialog 
        open={setupDialogOpen}
        onClose={() => setSetupDialogOpen(false)}
      />

      <Snackbar
        open={!!notification.message}
        autoHideDuration={6000}
        onClose={() => setNotification({ type: '', message: '' })}
      >
        <Alert 
          onClose={() => setNotification({ type: '', message: '' })}
          severity={notification.type || 'info'}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default App;