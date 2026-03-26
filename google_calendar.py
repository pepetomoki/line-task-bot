"""Google Calendar連携モジュール - 予定の取得"""

import os
from datetime import datetime, timedelta
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendarClient:
    """Google Calendar API クライアント"""

    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
    ):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self) -> bool:
        """OAuth2.0 認証（初回はブラウザ、以降はトークン再利用）"""
        creds = None

        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(
                self.token_path, SCOPES
            )

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print(
                        f"❌ {self.credentials_path} が見つかりません。"
                        "Google Cloud Consoleからダウンロードしてください。"
                    )
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)
        return True

    def get_today_events(
        self, target_date: Optional[datetime] = None
    ) -> list[dict]:
        """指定日（デフォルト：今日）の予定を取得"""
        if not self.service:
            if not self.authenticate():
                return []

        if target_date is None:
            target_date = datetime.now()

        # 日の開始と終了
        start_of_day = target_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_of_day = start_of_day + timedelta(days=1)

        time_min = start_of_day.isoformat() + "+09:00"
        time_max = end_of_day.isoformat() + "+09:00"

        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        parsed = []

        for event in events:
            start = event["start"]
            end = event["end"]

            # 終日イベントか判別
            if "dateTime" in start:
                is_all_day = False
                start_time = datetime.fromisoformat(start["dateTime"])
                end_time = datetime.fromisoformat(end["dateTime"])
                time_str = (
                    f"{start_time.strftime('%H:%M')}"
                    f"-{end_time.strftime('%H:%M')}"
                )
            else:
                is_all_day = True
                time_str = "終日"

            parsed.append(
                {
                    "title": event.get("summary", "(タイトルなし)"),
                    "time_str": time_str,
                    "is_all_day": is_all_day,
                    "location": event.get("location", ""),
                    "description": event.get("description", ""),
                }
            )

        return parsed

    def get_upcoming_events(self, days: int = 7) -> list[dict]:
        """今後N日間の予定を取得"""
        if not self.service:
            if not self.authenticate():
                return []

        now = datetime.now()
        time_min = now.isoformat() + "+09:00"
        time_max = (now + timedelta(days=days)).isoformat() + "+09:00"

        events_result = (
            self.service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        parsed = []

        for event in events:
            start = event["start"]
            if "dateTime" in start:
                start_dt = datetime.fromisoformat(start["dateTime"])
                date_str = start_dt.strftime("%m/%d %H:%M")
            else:
                date_str = start.get("date", "")

            parsed.append(
                {
                    "title": event.get("summary", "(タイトルなし)"),
                    "date_str": date_str,
                    "location": event.get("location", ""),
                }
            )

        return parsed
