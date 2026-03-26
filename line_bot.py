"""LINE Bot モジュール - メッセージ受信・送信"""

import re

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    MessagingApi,
    PushMessageRequest,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from google_calendar import GoogleCalendarClient
from message_formatter import (
    format_calendar_events,
    format_task_completed,
    format_task_deleted,
    format_task_list,
    format_task_registered,
)
from task_store import TaskStore


class LineBot:
    """LINE Messaging API クライアント"""

    def __init__(
        self,
        channel_secret: str,
        channel_access_token: str,
        user_id: str,
        task_store: TaskStore,
        ai_analyzer: AIAnalyzer,
        calendar_client: GoogleCalendarClient = None,
    ):
        self.user_id = user_id
        self.task_store = task_store
        self.ai_analyzer = ai_analyzer
        self.calendar_client = calendar_client

        # Webhook Handler
        self.handler = WebhookHandler(channel_secret)

        # Messaging API
        configuration = Configuration(
            access_token=channel_access_token
        )
        self.api_client = ApiClient(configuration)
        self.messaging_api = MessagingApi(self.api_client)

        # メッセージハンドラー登録
        self._register_handlers()

    def _register_handlers(self):
        """Webhookイベントハンドラーを登録"""

        @self.handler.add(MessageEvent, message=TextMessageContent)
        def handle_text_message(event: MessageEvent):
            text = event.message.text.strip()

            # コマンド判定
            if text in ("タスク一覧", "タスク", "一覧", "リスト"):
                response = self._handle_task_list()
            elif text in ("カレンダー", "今日の予定", "予定"):
                response = self._handle_calendar()
            elif re.match(r"^(完了|done)\s*(\d+)$", text, re.IGNORECASE):
                match = re.match(
                    r"^(完了|done)\s*(\d+)$", text, re.IGNORECASE
                )
                task_num = int(match.group(2))
                response = self._handle_complete_task(task_num)
            elif re.match(r"^(削除|delete)\s*(\d+)$", text, re.IGNORECASE):
                match = re.match(
                    r"^(削除|delete)\s*(\d+)$", text, re.IGNORECASE
                )
                task_num = int(match.group(2))
                response = self._handle_delete_task(task_num)
            elif text in ("ヘルプ", "help", "使い方"):
                response = self._handle_help()
            else:
                # AI解析でタスク登録
                response = self._handle_ai_task(text)

            # 返信
            self.messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=response)],
                )
            )

    def _handle_task_list(self) -> str:
        """タスク一覧コマンド"""
        tasks = self.task_store.get_pending_tasks()
        return format_task_list(tasks)

    def _handle_complete_task(self, task_num: int) -> str:
        """タスク完了コマンド"""
        tasks = self.task_store.get_pending_tasks()
        if task_num < 1 or task_num > len(tasks):
            return f"⚠️ タスク番号 {task_num} は見つかりません。「タスク一覧」で確認してね。"

        task = tasks[task_num - 1]
        title = self.task_store.complete_task(task["id"])
        if title:
            return format_task_completed(title)
        return "⚠️ タスクの完了に失敗しました。"

    def _handle_delete_task(self, task_num: int) -> str:
        """タスク削除コマンド"""
        tasks = self.task_store.get_pending_tasks()
        if task_num < 1 or task_num > len(tasks):
            return f"⚠️ タスク番号 {task_num} は見つかりません。「タスク一覧」で確認してね。"

        task = tasks[task_num - 1]
        title = self.task_store.delete_task(task["id"])
        if title:
            return format_task_deleted(title)
        return "⚠️ タスクの削除に失敗しました。"

    def _handle_calendar(self) -> str:
        """カレンダー予定表示コマンド"""
        if not self.calendar_client:
            return "⚠️ カレンダー連携が設定されていません。"

        try:
            events = self.calendar_client.get_today_events()
            return format_calendar_events(events)
        except Exception as e:
            print(f"⚠️ カレンダー取得エラー: {e}")
            return "⚠️ カレンダー予定の取得に失敗しました。"

    def _handle_help(self) -> str:
        """ヘルプコマンド"""
        return (
            "📖 使い方ガイド\n"
            "\n"
            "📝 タスク登録:\n"
            "  用事やタスクをそのまま送るだけ！\n"
            "  AIが内容を理解してリマインドしてくれます\n"
            "\n"
            "📋 タスク一覧:\n"
            "  「リスト」と送信\n"
            "\n"
            "📅 カレンダー予定:\n"
            "  「カレンダー」と送信\n"
            "  Googleカレンダーの今日の予定を表示します\n"
            "\n"
            "✅ タスク完了:\n"
            "  「完了 番号」と送信\n"
            "\n"
            "🗑️ タスク削除:\n"
            "  「削除 番号」と送信"
        )

    def _handle_ai_task(self, message: str) -> str:
        """AIでメッセージを解析しタスク登録"""
        result = self.ai_analyzer.analyze_message(message)
        tasks = result.get("tasks", [])

        if tasks:
            for task_data in tasks:
                self.task_store.add_task(
                    title=task_data.get("title", ""),
                    detail=task_data.get("detail", ""),
                    due_date=task_data.get("due_date"),
                    remind_times=task_data.get("remind_times", []),
                    source="line",
                )

        return format_task_registered(
            result.get("response_message", "📝 登録しました！")
        )

    def push_message(self, text: str):
        """ユーザーにプッシュメッセージを送信"""
        self.messaging_api.push_message(
            PushMessageRequest(
                to=self.user_id,
                messages=[TextMessage(text=text)],
            )
        )
