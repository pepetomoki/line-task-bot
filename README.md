# LINE × Googleカレンダー AIタスク管理Bot 🤖

LINEで全てのタスクや予定を管理し、AIがリマインドのタイミングを自動判断してくれるツールです。

## ✨ 機能

- **LINEでタスク登録**: 用事をLINEにそのまま送るだけでAIが内容を理解し登録
- **AIリマインド**: タスクの内容に応じて最適なタイミングでリマインド通知
- **Googleカレンダー連携**: 毎朝、当日の予定を自動通知
- **タスク管理**: 一覧確認・完了・削除をLINEで操作

## 📋 コマンド一覧

| メッセージ | 動作 |
|---|---|
| `用事をそのまま送信` | AIが解析してタスク登録＆リマインド設定 |
| `タスク一覧` | 未完了タスクの一覧を表示 |
| `完了 番号` | タスクを完了にする（例: `完了 1`） |
| `削除 番号` | タスクを削除する（例: `削除 2`） |
| `ヘルプ` | 使い方を表示 |

## 🚀 セットアップ手順

### 1. 必要なアカウント・API Key

| サービス | 取得するもの |
|---|---|
| [LINE Developers](https://developers.line.biz/) | Channel Secret, Channel Access Token |
| [OpenAI](https://platform.openai.com/) | API Key |
| [Google Cloud](https://console.cloud.google.com/) | OAuth認証情報 (credentials.json) |

### 2. LINE Messaging API チャンネル作成

1. [LINE Developers Console](https://developers.line.biz/console/) にログイン
2. **新規プロバイダー** を作成
3. **Messaging API** チャンネルを作成
4. チャンネル設定から以下を取得:
   - **Channel Secret**（チャンネル基本設定）
   - **Channel Access Token**（Messaging API設定 → 発行）
5. **Messaging API設定** → **応答メッセージ**: **無効**
6. **Messaging API設定** → **あいさつメッセージ**: **無効**
7. 自分の **User ID** は「チャンネル基本設定」→「あなたのユーザーID」で確認

### 3. Google Calendar API 設定

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成
2. **APIとサービス** → **ライブラリ** → **Google Calendar API** を有効化
3. **認証情報** → **認証情報を作成** → **OAuth クライアント ID**
   - アプリケーションの種類: **デスクトップアプリ**
4. `credentials.json` をダウンロードしてプロジェクトフォルダに配置

### 4. 環境構築

```bash
# プロジェクトフォルダに移動
cd /Users/pepetomoki/code/タスク管理

# Python仮想環境を作成（推奨）
python3 -m venv venv
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt

# 環境変数ファイルを作成
cp .env.example .env
```

### 5. `.env` ファイルを編集

```env
LINE_CHANNEL_SECRET=取得したChannel Secret
LINE_CHANNEL_ACCESS_TOKEN=取得したChannel Access Token
LINE_USER_ID=あなたのUser ID
OPENAI_API_KEY=取得したOpenAI API Key
```

### 6. 初回起動とGoogle認証

```bash
python app.py
```

初回起動時にブラウザが開き、Googleアカウントの認証を求められます。
認証完了後、`token.json` が保存され、以降は自動認証されます。

### 7. ngrokでWebhookを公開

```bash
# 別のターミナルで実行
ngrok http 5000
```

表示された `https://xxxx.ngrok.io` のURLをコピーし、
LINE Developers Console → **Messaging API設定** → **Webhook URL** に以下を設定:

```
https://xxxx.ngrok.io/callback
```

**Webhookの利用**: **有効** にする

### 8. 動作確認

1. LINE公式アカウントを友だち追加
2. ブラウザで `http://localhost:5000/test` にアクセス → テスト通知が届くか確認
3. LINEで「明日の10時に打ち合わせ」と送信 → タスク登録の応答が返ってくるか確認
4. 「タスク一覧」と送信 → 登録したタスクが表示されるか確認

## 📁 ファイル構成

```
├── app.py                 # Flaskメインアプリ
├── config.py              # 環境変数読み込み
├── line_bot.py            # LINE Bot（受信・送信）
├── ai_analyzer.py         # AI解析（OpenAI）
├── task_store.py          # タスクDB（SQLite）
├── scheduler.py           # スケジューラー
├── message_formatter.py   # メッセージ整形
├── google_calendar.py     # Googleカレンダー連携
├── requirements.txt       # 依存パッケージ
├── .env.example           # 環境変数テンプレート
└── README.md              # この手順書
```

## ⚙️ カスタマイズ

`.env` ファイルで以下を変更できます：

| 項目 | デフォルト | 説明 |
|---|---|---|
| `MORNING_NOTIFY_HOUR` | 7 | 朝の通知時刻（時） |
| `MORNING_NOTIFY_MINUTE` | 0 | 朝の通知時刻（分） |
| `REMIND_CHECK_INTERVAL_MINUTES` | 1 | リマインドチェック間隔（分） |
| `OPENAI_MODEL` | gpt-4o-mini | 使用するAIモデル |
