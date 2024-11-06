import React, { useState, useEffect, useRef } from 'react';
import { Settings, RefreshCw, XSquare, Mic } from 'lucide-react';
import axios from 'axios';

// GenerationProgress コンポーネント
const GenerationProgress = ({ status }) => {
  // statusがnullまたは未定義の場合は何も表示しない
  if (!status) return null;

  const getStatusContent = () => {
    switch (status) {
      case 'generating_lyrics':
        return {
          title: '🎨 作詞中...',
          description: 'あなたの回答から歌詞を作成しています',
          color: 'bg-blue-500'
        };
      case 'generating_music':
        return {
          title: '🎵 生成中...',
          description: 'ミュージックビデオを生成しています（3分程度かかります）',
          color: 'bg-purple-500'
        };
      case 'complete':
        return {
          title: '✨ 完成！',
          description: 'ミュージックビデオが生成されました',
          color: 'bg-green-500'
        };
      default:
        return null;
    }
  };

  const content = getStatusContent();
  // statusが不正な値の場合も何も表示しない
  if (!content) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="font-handwriting">
        <h3 className="text-lg font-bold mb-2 chalk-effect">{content.title}</h3>
        <p className="text-gray-600 mb-4">{content.description}</p>
        <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
          <div className={`h-full ${content.color} animate-pulse`} />
        </div>
      </div>
    </div>
  );
};

// AudioSetupDialog コンポーネント
const AudioSetupDialog = ({ open, onClose }) => {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
      <div className="relative bg-white rounded-xl max-w-md w-full mx-4 p-8 shadow-2xl">
        <div className="flex justify-between items-center mb-6 border-b pb-4">
          <h2 className="text-2xl font-handwriting font-bold text-gray-800">
            リップシンクの設定方法
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="閉じる"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="mb-8">
          <div className="bg-blue-50 rounded-lg p-6 mb-6">
            <h3 className="font-handwriting text-lg font-bold text-gray-800 mb-4">
              初期設定手順:
            </h3>
            <ol className="space-y-4 list-decimal list-outside pl-5 font-handwriting text-gray-700">
              <li className="leading-relaxed">
                Audio MIDI設定を開く
                <div className="mt-1 text-sm text-gray-500">
                  ※ アプリケーション → ユーティリティ → Audio MIDI設定
                </div>
              </li>
              <li className="leading-relaxed">
                左下の<span className="text-blue-600 font-semibold">+</span>ボタンから
                「新規マルチ出力デバイス」を作成
              </li>
              <li className="leading-relaxed">
                名前を<span className="font-semibold text-blue-600">「Music Output」</span>に設定
              </li>
              <li className="leading-relaxed">
                以下の出力にチェックを入れる:
                <ul className="mt-2 ml-4 space-y-2 list-disc text-gray-600">
                  <li className="leading-relaxed">
                    MacBook Airのスピーカー
                  </li>
                  <li className="leading-relaxed">
                    VB-Cable
                  </li>
                </ul>
              </li>
              <li className="leading-relaxed">
                システム設定 → サウンド → 出力で
                <span className="font-semibold text-blue-600">「Music Output」</span>を選択
              </li>
              <li className="leading-relaxed">
                3teneの音声入力で
                <span className="font-semibold text-blue-600">「VB-Cable」</span>を選択
              </li>
            </ol>
          </div>

          <div className="bg-yellow-50 rounded-lg p-4 mb-6">
            <p className="text-sm text-yellow-800 font-handwriting leading-relaxed">
              ※ 設定が完了したら、下の「設定完了」ボタンをクリックしてください。
              設定に問題がある場合は、各ステップを再確認してください。
            </p>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            onClick={onClose}
            className="w-full bg-blue-500 hover:bg-blue-600 text-white py-3 px-6 rounded-lg 
              font-handwriting font-bold text-lg transition-colors duration-200 ease-in-out 
              transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 
              focus:ring-opacity-50 shadow-lg"
          >
            設定完了
          </button>
        </div>
      </div>
    </div>
  );
};

// QRコードモーダルコンポーネント
const QRCodeModal = ({ url, isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl max-w-sm w-full mx-auto shadow-2xl transform transition-all">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold font-handwriting">
              スマートフォンで視聴
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XSquare className="w-6 h-6" />
            </button>
          </div>
          
          <div className="text-center">
            <img
              src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(url)}`}
              alt="QR Code"
              className="mx-auto mb-4"
              width="200"
              height="200"
            />
            <p className="text-sm text-gray-600 font-handwriting mb-6">
              QRコードを読み取ってアクセス
            </p>
            
            <button
              onClick={onClose}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded-lg 
                font-handwriting transition-colors shadow-md transform hover:scale-105 duration-200"
            >
              閉じる
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
// メインのAppコンポーネント
const App = () => {
  // State管理
  const [connected, setConnected] = useState(false);
  const [isInterviewStarted, setIsInterviewStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [musicError, setMusicError] = useState('');
  const [notification, setNotification] = useState({ type: '', message: '' });
  const [generationStatus, setGenerationStatus] = useState(null);
  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [musicData, setMusicData] = useState(null);
  const [isQRModalOpen, setIsQRModalOpen] = useState(false);

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
  
      // WebSocketのメッセージハンドラー部分を修正
// WebSocketのメッセージハンドラー
ws.current.onmessage = async (event) => {
  try {
    const message = event.data;
    if (typeof message === 'string') {
      // JSONとしてパースを試みる
      try {
        const data = JSON.parse(message);
        
        switch (data.type) {
          case 'setup_instruction':
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
            // 通知を表示しない
            break;
          
          case 'question':
          case 'message':
            // 質問やメッセージを表示する
            setCurrentQuestion(data.message);
            break;
          
          case 'music_complete':
            setGenerationStatus('complete');
            setMusicData(data.data);
            if (data.data.video_url) {
              window.open(data.data.video_url, '_blank');
            }
            setNotification({ type: 'success', message: 'ミュージックビデオの生成が完了しました！' });
            break;
          
          case 'error':
            setNotification({ type: 'error', message: data.message });
            break;
        }
      } catch (jsonError) {
        // JSONパースに失敗した場合は、直接メッセージとして表示
        // ただし、明らかなJSONっぽい文字列は除外
        if (message && !message.startsWith('{') && !message.includes('"type"')) {
          setCurrentQuestion(message);
        }
        console.log('JSON parse error:', jsonError);
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
  
    // useEffect for WebSocket connection
    useEffect(() => {
      connectWebSocket();
      return () => {
        if (ws.current) ws.current.close();
      };
    }, []);
  
    // useEffect for music data
    useEffect(() => {
      if (musicData && musicData.video_url) {
        setIsQRModalOpen(true);
      }
    }, [musicData]);
  
    // インタビュー開始
    const startInterview = () => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send('start_interview');
        setIsInterviewStarted(true);
        setNotification({ type: 'success', message: 'インタビューを開始します' });
      } else {
        setNotification({ type: 'error', message: 'サーバーに接続されていません' });
      }
    };
  
    // 録音開始
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
  
    // 録音停止
    const stopRecording = () => {
      if (mediaRecorder.current?.state === 'recording') {
        mediaRecorder.current.stop();
        setIsRecording(false);
      }
    };
  
    // 回答送信
    const sendAnswer = () => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(answer);
        setAnswer('');
        setNotification({ type: 'success', message: '回答を送信しました' });
      } else {
        setNotification({ type: 'error', message: 'サーバーに接続されていません' });
      }
    };
  
    // アプリケーションのリセット
  const resetApplication = () => {
    setIsInterviewStarted(false);
    setCurrentQuestion('');
    setAnswer('');
    setIsRecording(false);
    setMusicError('');
    setGenerationStatus(null);
    setMusicData(null);
    setNotification({ type: 'info', message: 'アプリケーションをリセットしました' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-wood-light to-wood-DEFAULT">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-chalkboard rounded-lg shadow-2xl p-8 relative border-8 border-wood-dark chalkboard chalk-dust">
          <div className="absolute left-0 right-0 -bottom-4 h-3 bg-wood-dark"></div>
          
          <div className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-chalk font-bold text-white chalk-effect">
              Your Song Creator
            </h1>
            <div className="flex gap-3">
              <button 
                onClick={() => setSetupDialogOpen(true)}
                className="p-2 rounded-full hover:bg-chalkboard-light transition-colors"
                title="リップシンク設定"
              >
                <Settings className="w-6 h-6 text-white" />
              </button>
              <button 
                onClick={resetApplication}
                className="p-2 rounded-full hover:bg-chalkboard-light transition-colors"
                title="リセット"
              >
                <RefreshCw className="w-6 h-6 text-white" />
              </button>
            </div>
          </div>

          <div className="bg-paper-DEFAULT rounded-lg p-6 shadow-inner paper-texture">
            <div className="space-y-6">
          
            {!isInterviewStarted ? (
  <div className="bg-white/90 backdrop-blur-sm rounded-xl p-8 shadow-lg">
    <div className="text-center space-y-8 py-4">
      <h2 className="text-3xl font-handwriting text-gray-800 font-bold mb-6">
        あなたの特別な一曲を作ります
      </h2>
      <div className="space-y-4">
        <p className="text-xl font-handwriting text-gray-700 leading-relaxed max-w-2xl mx-auto">
          思い出の詰まった青春時代について、
          <span className="font-bold text-blue-600">5つの質問</span>
          にお答えください。
        </p>
        <p className="text-xl font-handwriting text-gray-700 leading-relaxed max-w-2xl mx-auto">
          あなたの回答から、世界にたった一つの
          <br />
          オリジナルソングを作り上げます。
        </p>
      </div>
      <button
        onClick={startInterview}
        disabled={!connected}
        className={`px-8 py-4 ${
          !connected 
            ? 'bg-gray-400 cursor-not-allowed' 
            : 'bg-blue-500 hover:bg-blue-600'
        } text-white rounded-lg font-handwriting text-xl transition-all duration-200 
        transform hover:scale-105 shadow-md mt-8`}
      >
        インタビューを開始する
      </button>
    </div>
  </div>
) : (
  <div className="bg-white/90 backdrop-blur-sm rounded-xl p-8 shadow-lg">
    <div className="space-y-4">
      {/* 質問表示エリア */}
      <div className="bg-gradient-to-r from-green-50 to-green-100 p-6 rounded-lg shadow-md border-l-4 border-green-400">
        <p className="text-gray-700 text-center text-lg font-handwriting">
          {currentQuestion || "準備中..."}
        </p>
      </div>
      
      {/* 回答入力エリア */}
      <div className="relative">
        <input
          type="text"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          disabled={!currentQuestion || isRecording}
          placeholder="回答を入力してください"
          className="w-full px-4 py-3 bg-white rounded-lg 
            font-handwriting text-lg border-2 border-gray-300 
            focus:border-blue-500 focus:ring-2 focus:ring-blue-200 
            transition-all duration-200 shadow-inner
            disabled:bg-gray-100 disabled:cursor-not-allowed
            placeholder:text-gray-400"
        />
      </div>
      
      {/* 操作ボタン */}
      <div className="flex gap-3">
        <button 
          onClick={isRecording ? stopRecording : startRecording}
          disabled={!currentQuestion}
          className={`flex-1 ${
            isRecording 
              ? 'bg-red-500 hover:bg-red-600' 
              : 'bg-blue-500 hover:bg-blue-600'
          } text-white px-4 py-3 rounded-lg font-handwriting transition-colors 
          flex items-center justify-center gap-2 shadow-md 
          disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isRecording ? <XSquare className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          {isRecording ? '録音停止' : '録音開始'}
        </button>
        <button
          onClick={sendAnswer}
          disabled={!answer || isRecording}
          className={`flex-1 ${
            !answer || isRecording
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-green-500 hover:bg-green-600'
          } text-white px-4 py-3 rounded-lg font-handwriting transition-colors shadow-md`}
        >
          回答を送信
        </button>
      </div>
    </div>
  </div>
)}

              {/* 進捗表示 */}
              {generationStatus && (
                <div className="mt-6">
                  <GenerationProgress status={generationStatus} />
                </div>
              )}

              {/* エラー表示 */}
              {musicError && (
                <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-red-400">
                  <p className="text-red-600 font-handwriting">
                    エラーが発生しました: {musicError}
                  </p>
                </div>
              )}

              {/* 完了メッセージ */}
              {musicData && musicData.video_url && (
                <div className="mt-6 space-y-4">
                  <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-green-400">
                    <p className="text-green-600 text-center font-bold mb-4 font-handwriting">
                      ミュージックビデオの生成が完了しました！
                    </p>
                    <div className="flex flex-col items-center gap-4">
                      <button
                        onClick={() => window.open(musicData.video_url, '_blank')}
                        className="w-full max-w-sm bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 
                          rounded-lg font-handwriting transition-colors shadow-md transform 
                          hover:scale-105 duration-200"
                      >
                        ブラウザで視聴する
                      </button>
                      
                      <button
                        onClick={() => setIsQRModalOpen(true)}
                        className="w-full max-w-sm bg-green-500 hover:bg-green-600 text-white px-6 py-3 
                          rounded-lg font-handwriting transition-colors shadow-md transform 
                          hover:scale-105 duration-200"
                      >
                        スマートフォンで視聴
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ダイアログ */}
      <AudioSetupDialog 
        open={setupDialogOpen}
        onClose={() => setSetupDialogOpen(false)}
      />

      {/* QRコードモーダル */}
      {musicData && musicData.video_url && (
        <QRCodeModal
          url={musicData.video_url}
          isOpen={isQRModalOpen}
          onClose={() => setIsQRModalOpen(false)}
        />
      )}

      {/* 通知メッセージ */}
      {notification.message && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50">
          <div className={`px-6 py-3 rounded-lg shadow-lg text-white font-handwriting ${
            notification.type === 'error' ? 'bg-red-500' :
            notification.type === 'success' ? 'bg-green-500' :
            notification.type === 'warning' ? 'bg-yellow-500' :
            'bg-blue-500'
          }`}>
            <p>{notification.message}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;