"""設定モジュール - 環境変数の読み込みとバリデーション"""

import os
import sys
from dotenv import load_dotenv

# .envファイル読み込み
load_dotenv()


class Config:
    """アプリケーション設定"""

    # LINE Messaging API
    LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
    LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    LINE_USER_ID = os.getenv("LINE_USER_ID", "")

    # Google Gemini API
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    # Google Calendar
    GOOGLE_CREDENTIALS_PATH = os.getenv(
        "GOOGLE_CREDENTIALS_PATH", "credentials.json"
    )
    GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

    # スケジューラー設定
    MORNING_NOTIFY_HOUR = int(os.getenv("MORNING_NOTIFY_HOUR", "7"))
    MORNING_NOTIFY_MINUTE = int(os.getenv("MORNING_NOTIFY_MINUTE", "0"))
    REMIND_CHECK_INTERVAL_MINUTES = int(
        os.getenv("REMIND_CHECK_INTERVAL_MINUTES", "1")
    )

    # データベース
    DB_PATH = os.getenv("DB_PATH", "tasks.db")

    # Flask
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    @classmethod
    def validate(cls):
        """必須環境変数のバリデーション"""
        errors = []

        if not cls.LINE_CHANNEL_SECRET:
            errors.append("LINE_CHANNEL_SECRET")
        if not cls.LINE_CHANNEL_ACCESS_TOKEN:
            errors.append("LINE_CHANNEL_ACCESS_TOKEN")
        if not cls.LINE_USER_ID:
            errors.append("LINE_USER_ID")
        if not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY")

        if errors:
            print("❌ 以下の環境変数が設定されていません:")
            for e in errors:
                print(f"   - {e}")
            print("\n.env ファイルを作成して設定してください。")
            print("テンプレート: .env.example")
            sys.exit(1)

        return True
