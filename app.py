"""LINE × Googleカレンダー AIタスク管理ツール

Flaskアプリケーション - Webhook受信 + スケジューラー
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, abort, request

from ai_analyzer import AIAnalyzer
from config import Config
from google_calendar import GoogleCalendarClient
from line_bot import LineBot
from scheduler import TaskScheduler
from task_store import TaskStore

# 環境変数バリデーション
Config.validate()

# Flask アプリケーション
app = Flask(__name__)

# コンポーネント初期化
task_store = TaskStore(db_path=Config.DB_PATH)
ai_analyzer = AIAnalyzer(
    api_key=Config.GEMINI_API_KEY, model=Config.GEMINI_MODEL
)
calendar_client = GoogleCalendarClient(
    credentials_path=Config.GOOGLE_CREDENTIALS_PATH,
    token_path=Config.GOOGLE_TOKEN_PATH,
)
line_bot = LineBot(
    channel_secret=Config.LINE_CHANNEL_SECRET,
    channel_access_token=Config.LINE_CHANNEL_ACCESS_TOKEN,
    user_id=Config.LINE_USER_ID,
    task_store=task_store,
    ai_analyzer=ai_analyzer,
    calendar_client=calendar_client,
)

# スケジューラー
task_scheduler = TaskScheduler(
    line_bot=line_bot, task_store=task_store, config=Config
)

# gunicorn 経由でも スケジューラーを起動
task_scheduler.start()
print("🤖 LINE タスク管理Bot 起動完了！")


@app.route("/callback", methods=["POST"])
def callback():
    """LINE Webhookエンドポイント"""
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    print(f"📨 Webhook受信: {body[:100]}...")

    try:
        line_bot.handler.handle(body, signature)
    except Exception as e:
        print(f"⚠️ Webhook処理: {e}")
        return "OK"

    return "OK"


@app.route("/health", methods=["GET"])
def health():
    """ヘルスチェック"""
    return {"status": "ok", "message": "タスク管理Bot稼働中 🤖"}


@app.route("/test", methods=["GET"])
def test_notification():
    """テスト通知送信"""
    try:
        line_bot.push_message(
            "🧪 テスト通知\n\nタスク管理Botが正常に動作しています！✅"
        )
        return {"status": "ok", "message": "テスト通知を送信しました"}
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500


if __name__ == "__main__":
    print("=" * 50)
    print(f"🌐 サーバー: http://localhost:{Config.FLASK_PORT}")
    print(f"📡 Webhook URL: http://localhost:{Config.FLASK_PORT}/callback")
    print("=" * 50)

    try:
        app.run(
            host="0.0.0.0",
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG,
            use_reloader=False,
        )
    finally:
        task_scheduler.stop()
