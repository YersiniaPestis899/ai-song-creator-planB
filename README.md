# AI Song Creator

このプロジェクトは、ユーザーの回答から個人の青春ソングを自動生成するAIアプリケーションです。VOICEVOXによる音声合成、Suno AIによる音楽生成、AWS BedrockのClaude-3.5-sonnetによる歌詞生成を組み合わせて、オリジナルの楽曲を作成します。

## 機能

- カメラによる人物検出
- VOICEVOXを使用した音声対話
- マイク入力による音声認識
- AIによる歌詞生成
- AIによる楽曲生成
- ミュージックビデオの自動生成

## 必要要件

### システム要件
- Windows 11
- Python 3.8以上
- Node.js 16.0以上
- npm 7.0以上

### 必要なAPI/サービス
- AWS Bedrock アカウント
- Suno AI API キー
- Google Cloud Speech-to-Text API キー

### 必要なソフトウェア
- VOICEVOX（Windows版）

## インストール手順

1. リポジトリのクローン
```bash
git clone [リポジトリURL]
cd ai-song-creator
```

2. バックエンド（Python）の設定
```bash
cd backend
pip install -r requirements.txt
```

3. フロントエンド（React）の設定
```bash
cd frontend
npm install
```

4. 環境変数の設定
以下の内容で`.env`ファイルを作成：

```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
CLAUDE_MODEL_ID=your_claude_model_id
SUNO_API_KEY=your_suno_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_credentials.json
```

## 起動方法

1. VOICEVOXの起動
- VOICEVOXアプリケーションを起動し、エンジンが動作していることを確認

2. バックエンドの起動
```bash
cd backend
uvicorn main:app --reload
```

3. フロントエンドの起動
```bash
cd frontend
npm start
```

4. ブラウザでアプリケーションにアクセス
```
http://localhost:3000
```

## 使用方法

1. アプリケーションにアクセスし、「カメラを起動」ボタンをクリック
2. カメラが人物を検出すると、自動的にインタビューが開始
3. 5つの質問に回答（テキスト入力または音声入力が可能）
4. 回答完了後、自動的に歌詞と楽曲の生成を開始
5. 生成完了後、新しいタブでミュージックビデオが表示

## 注意事項

- カメラとマイクのアクセス許可が必要です
- VOICEVOXエンジンは必ずアプリケーション起動前に起動してください
- ブラウザのポップアップブロックを無効にすることを推奨します
- 音楽生成には数分かかる場合があります

## トラブルシューティング

### よくある問題と解決方法

1. カメラが認識されない場合
- ブラウザのカメラ権限を確認
- 他のアプリケーションがカメラを使用していないか確認

2. 音声が再生されない場合
- VOICEVOXエンジンが起動していることを確認
- ブラウザの音声設定を確認

3. APIエラーが発生する場合
- 環境変数が正しく設定されているか確認
- API制限に達していないか確認

### ログの確認方法

- バックエンドのログは`backend/logs/`ディレクトリに保存されます
- フロントエンドのエラーはブラウザのコンソールで確認できます

## アプリのカスタマイズ

### VOICEVOXの話者変更
- `main.py`の`speaker`パラメータを変更することで、異なる話者を選択可能

### インタビューの質問変更
- `main.py`の`QUESTIONS`リストを編集することで、質問内容をカスタマイズ可能

### UIのカスタマイズ
- `App.js`のスタイリングを編集することで、見た目をカスタマイズ可能

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。

## 謝辞

- VOICEVOXプロジェクト
- Suno AI
- AWS Bedrock
- その他、使用しているオープンソースプロジェクトの開発者の皆様

## お問い合わせ

バグ報告や機能リクエストは、GitHubのIssuesにてお願いします。