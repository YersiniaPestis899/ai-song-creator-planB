# Your Song Creator

このアプリケーションは、ユーザーの思い出や経験に基づいて、AIを使用してオリジナルの音楽を生成するウェブアプリケーションです。

## 機能

- インタラクティブなインタビュー形式で思い出を収集
- 音声入力による回答機能
- リアルタイムの音声合成による質問読み上げ
- AIによる歌詞生成
- AIによる音楽生成
- スマートフォンでの視聴用QRコード生成

## 技術スタック

### フロントエンド
- React
- Tailwind CSS
- Axios
- Lucide React (アイコン)

### バックエンド
- FastAPI
- Python
- VOICEVOX (音声合成)
- AWS Bedrock (歌詞生成)
- Suno AI (音楽生成)
- Google Cloud Speech-to-Text (音声認識)

## セットアップ

### 必要条件
- Node.js
- Python 3.8以上
- VOICEVOX Engine
- AWS アカウント
- Google Cloud アカウント
- Suno AI アカウント

### インストール

1. リポジトリのクローン
```bash
git clone https://github.com/YourUsername/ai-song-creator-sub.git
cd ai-song-creator-sub
```

2. フロントエンド依存関係のインストール
```bash
npm install
```

3. バックエンド依存関係のインストール
```bash
pip install -r requirements.txt
```

4. 環境変数の設定
`.env` ファイルを作成し、必要な環境変数を設定:
```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
SUNO_API_KEY=your_suno_api_key
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_credentials.json
```

### 起動方法

1. VOICEVOXの起動
VOICEVOXエンジンを起動し、ポート50021で待ち受けていることを確認

2. バックエンドの起動
```bash
python main.py
```

3. フロントエンドの起動
```bash
npm start
```

## 使用方法

1. アプリケーションにアクセス（デフォルトで http://localhost:3000）
2. 「インタビューを開始する」ボタンをクリック
3. 質問に対して、テキスト入力または音声入力で回答
4. すべての質問に回答後、AIが歌詞と音楽を生成
5. 生成された楽曲は自動的にブラウザで開かれ、QRコードでスマートフォンでも視聴可能

## ライセンス

このプロジェクトは [MITライセンス](LICENSE) の下で公開されています。

## 謝辞

- VOICEVOXプロジェクト
- Suno AI
- AWS Bedrock
- その他、使用しているオープンソースプロジェクトの開発者の皆様

## お問い合わせ

バグ報告や機能リクエストは、GitHubのIssuesにてお願いします。