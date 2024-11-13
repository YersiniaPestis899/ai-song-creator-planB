import React, { useState, useEffect, useRef } from 'react';
import { RefreshCw, XSquare, Mic } from 'lucide-react';
import axios from 'axios';

// GenerationProgress コンポーネント
const GenerationProgress = ({ status }) => {
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

const App = () => {
  // State管理
  const [isInterviewStarted, setIsInterviewStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [musicError, setMusicError] = useState('');
  const [notification, setNotification] = useState({ type: '', message: '' });
  const [generationStatus, setGenerationStatus] = useState(null);
  const [musicData, setMusicData] = useState(null);
  const [isQRModalOpen, setIsQRModalOpen] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState([]);

  // 通知の自動非表示
  useEffect(() => {
    let timeoutId;
    if (notification.message) {
      timeoutId = setTimeout(() => {
        setNotification({ type: '', message: '' });
      }, 3000); // 3秒後に通知を消す
    }
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [notification.message]);

  // 録音関連の設定
  const mediaRecorder = useRef(null);

  // 質問リストをコンポーネント内で定義
  const QUESTIONS = [
    "あなたの青春時代を一言で表すと？",
    "その時期にあなたが最も夢中になっていたものは？",
    "青春時代の挫折や失敗を乗り越えた時の気持ちを一言で？",
    "その頃のあなたにとって最も大切だったものは？",
    "今、あの頃の自分に伝えたい言葉を一つ挙げるとしたら？"
  ];

  // インタビュー開始
  const startInterview = async () => {
    try {
      const response = await axios.post('http://localhost:8000/start');
      if (response.data.status === 'success') {
        setCurrentQuestion(response.data.message);
        setIsInterviewStarted(true);
        setNotification({ type: 'success', message: 'インタビューを開始します' });
        
        await axios.post('http://localhost:8000/speak', {
          message: response.data.message
        });
        
        await getNextQuestion(0);
      }
    } catch (error) {
      console.error('Error starting interview:', error);
      setNotification({ type: 'error', message: 'インタビューの開始に失敗しました' });
    }
  };

  // 次の質問を取得
  const getNextQuestion = async (index) => {
    try {
      const response = await axios.get(`http://localhost:8000/questions/${index}`);
      if (response.data.status === 'success') {
        setCurrentQuestion(response.data.message);
        await axios.post('http://localhost:8000/speak', {
          message: response.data.message
        });
      }
    } catch (error) {
      setNotification({ type: 'error', message: '質問の取得に失敗しました' });
    }
  };

  // 回答送信
  const sendAnswer = async () => {
    try {
      if (!answer.trim()) {
        setNotification({ type: 'warning', message: '回答を入力してください' });
        return;
      }

      // 現在の回答を一時保存
      const currentAnswer = answer;
      
      // すぐに入力欄をクリアし、回答を配列に追加
      setAnswer('');
      const newAnswers = [...answers, currentAnswer];
      setAnswers(newAnswers);

      // バックグラウンドで回答を送信
      await axios.post('http://localhost:8000/submit-answer', {
        answer: currentAnswer,
        questionIndex: currentQuestionIndex
      });
      
      if (currentQuestionIndex < QUESTIONS.length - 1) {
        const nextIndex = currentQuestionIndex + 1;
        setCurrentQuestionIndex(nextIndex);
        await getNextQuestion(nextIndex);
      } else {
        // 完了メッセージの音声合成と表示
        const completionMessage = "ありがとうございます。楽曲の生成を開始します。";
        setCurrentQuestion(completionMessage);
        await axios.post('http://localhost:8000/speak', {
          message: completionMessage
        });

        // 作詞状態を表示
        setGenerationStatus('generating_lyrics');
        
        // 3秒後に作曲状態に変更
        setTimeout(() => {
          setGenerationStatus('generating_music');
        }, 3000);

        // 音楽生成APIを呼び出し
        const response = await axios.post('http://localhost:8000/generate', {
          answers: newAnswers
        });
        
        if (response.data.video_url) {
          setGenerationStatus('complete');
          setMusicData({
            video_url: response.data.video_url
          });
          window.open(response.data.video_url, '_blank');
          
          // QRコードモーダルを表示
          setIsQRModalOpen(true);
        }
      }
      
    } catch (error) {
      console.error('Error sending answer:', error);
      setNotification({ type: 'error', message: '回答の送信中にエラーが発生しました' });
      setGenerationStatus(null); // エラー時は生成状態をリセット
    }
  };

  // useEffect for music data
  useEffect(() => {
    if (musicData && musicData.video_url) {
      setIsQRModalOpen(true);
    }
  }, [musicData]);

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

  // アプリケーションのリセット
  const resetApplication = () => {
    setIsInterviewStarted(false);
    setCurrentQuestion('');
    setAnswer('');
    setIsRecording(false);
    setMusicError('');
    setGenerationStatus(null);
    setMusicData(null);
    setCurrentQuestionIndex(0);
    setAnswers([]);
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
                        私と一緒に、あなたの
                        <span className="font-bold text-blue-600">青春時代の思い出</span>
                        を探していきましょう！
                      </p>
                      <p className="text-xl font-handwriting text-gray-700 leading-relaxed max-w-2xl mx-auto">
                        <span className="font-bold text-blue-600">5つの質問</span>で、
                        あなたの大切な記憶が素敵な歌になって蘇ります。
                      </p>
                      <p className="text-xl font-handwriting text-gray-700 leading-relaxed max-w-2xl mx-auto">
                        さぁ、世界でたった一つの
                        オリジナルソング
                        を一緒に作りましょう！
                      </p>
                    </div>
                    <button
                      onClick={startInterview}
                      className="px-8 py-4 bg-blue-500 hover:bg-blue-600 
                        text-white rounded-lg font-handwriting text-xl 
                        transition-all duration-200 transform hover:scale-105 
                        shadow-md mt-8"
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