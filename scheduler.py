"""スケジューラー - リマインド通知と朝の予定通知"""

from apscheduler.schedulers.background import BackgroundScheduler

from google_calendar import GoogleCalendarClient
from message_formatter import format_morning_greeting, format_reminder


class TaskScheduler:
    """APSchedulerによる定期実行"""

    def __init__(self, line_bot, task_store, config):
        self.line_bot = line_bot
        self.task_store = task_store
        self.config = config
        self.scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
        self.calendar_client = None

    def start(self):
        """スケジューラーを開始"""
        # リマインドチェック（毎分）
        self.scheduler.add_job(
            self._check_reminders,
            "interval",
            minutes=self.config.REMIND_CHECK_INTERVAL_MINUTES,
            id="check_reminders",
        )

        # Renderのスリープ回避（14分毎）
        self.scheduler.add_job(
            self._keep_alive_ping,
            "interval",
            minutes=14,
            id="keep_alive_ping",
        )

        # 朝の予定通知
        self.scheduler.add_job(
            self._morning_notification,
            "cron",
            hour=self.config.MORNING_NOTIFY_HOUR,
            minute=self.config.MORNING_NOTIFY_MINUTE,
            id="morning_notify",
        )

        self.scheduler.start()
        print(
            f"📅 スケジューラー開始"
            f"（リマインドチェック: {self.config.REMIND_CHECK_INTERVAL_MINUTES}分毎, "
            f"朝通知: {self.config.MORNING_NOTIFY_HOUR}:"
            f"{self.config.MORNING_NOTIFY_MINUTE:02d}）"
        )

    def stop(self):
        """スケジューラーを停止"""
        if self.scheduler.running:
            self.scheduler.shutdown()

    def _check_reminders(self):
        """リマインド時刻に達したタスクを通知"""
        due_reminders = self.task_store.get_due_reminders()

        for reminder in due_reminders:
            try:
                message = format_reminder(reminder)
                self.line_bot.push_message(message)
                self.task_store.mark_reminder_sent(reminder["reminder_id"])
                print(f"✅ リマインド送信: {reminder['title']}")
            except Exception as e:
                print(f"❌ リマインド送信エラー: {e}")

    def _morning_notification(self):
        """朝の予定・タスク通知"""
        try:
            # Googleカレンダー予定取得
            events = []
            if self.calendar_client is None:
                self.calendar_client = GoogleCalendarClient(
                    credentials_path=self.config.GOOGLE_CREDENTIALS_PATH,
                    token_path=self.config.GOOGLE_TOKEN_PATH,
                )

            try:
                if self.calendar_client.authenticate():
                    events = self.calendar_client.get_today_events()
            except Exception as e:
                print(f"⚠️ カレンダー取得エラー: {e}")

            # タスクサマリー
            task_count = self.task_store.get_task_count()

            # メッセージ送信
            message = format_morning_greeting(events, task_count)
            self.line_bot.push_message(message)
            print("✅ 朝の通知送信完了")

        except Exception as e:
            print(f"❌ 朝の通知エラー: {e}")

    def _keep_alive_ping(self):
        """Renderの無料枠スリープを回避するための自己Ping送信"""
        import os
        import requests
        
        # Render環境にある場合は自動設定される環境変数からURLを取得
        external_url = os.environ.get('RENDER_EXTERNAL_URL')
        if external_url:
            health_url = f"{external_url}/health"
            try:
                # 自身に対してHTTPリクエストを送信して起こしておく
                response = requests.get(health_url, timeout=10)
                print(f"💓 スリープ回避Ping成功: {health_url} (HTTP {response.status_code})")
            except Exception as e:
                print(f"⚠️ スリープ回避Pingエラー: {e}")
