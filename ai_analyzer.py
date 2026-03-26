"""AIタスク解析モジュール - Google Gemini APIによるメッセージ解析"""

import json
from datetime import datetime

import google.generativeai as genai


class AIAnalyzer:
    """Google Gemini APIを使ったタスク解析"""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def analyze_message(self, message: str) -> dict:
        """
        ユーザーのメッセージからタスク情報を抽出。

        Returns:
            {
                "tasks": [
                    {
                        "title": "タスク名",
                        "detail": "詳細",
                        "due_date": "2026-03-26 14:00",
                        "remind_times": ["2026-03-26 10:00", "2026-03-26 13:00"]
                    }
                ],
                "response_message": "ユーザーへの応答メッセージ"
            }
        """
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M")
        current_weekday = ["月", "火", "水", "木", "金", "土", "日"][
            now.weekday()
        ]

        prompt = f"""あなたはタスク管理アシスタントです。
ユーザーのメッセージからタスクや予定を抽出し、適切なリマインドタイミングを判断してください。

現在の日時: {current_time}（{current_weekday}曜日）

以下のJSON形式で必ず回答してください。JSON以外のテキストは含めないでください:
{{
    "tasks": [
        {{
            "title": "タスク名（簡潔に）",
            "detail": "詳細情報（あれば）",
            "due_date": "YYYY-MM-DD HH:MM 形式（期限が不明な場合はnull）",
            "remind_times": ["YYYY-MM-DD HH:MM", ...]
        }}
    ],
    "response_message": "ユーザーへの親しみやすい応答メッセージ（登録内容の確認を含む）"
}}

リマインドタイミングの判断基準:
- 会議・MTG: 30分前と当日朝
- 提出物・締切: 前日夕方と当日朝
- 買い物・用事: 出発の1時間前、または当日朝
- 準備が必要なタスク: 準備に必要な時間を考慮して早めに
- 飲み会・イベント: 前日と当日の昼
- 期限が不明確: 翌日朝にリマインド
- 過去の時刻が指定されている場合: 翌日の同時刻として解釈

メッセージにタスクや予定の情報が含まれない場合:
{{
    "tasks": [],
    "response_message": "適切な応答メッセージ"
}}

Googleカレンダーの内容を確認したいと言われた場合:
{{
    "tasks": [],
    "response_message": "申し訳ありません、私は直接カレンダーの中身を見ることはできませんが、「カレンダー」というキーワードを送っていただければ、今日の予定を一覧で表示できますよ！😊"
}}

タスクの内容を詳しく教えてくれた場合:
- AIとしての自然な応答を返しつつ、tasksリストを適切に作成してください。

応答メッセージは絵文字を使って親しみやすく、登録した内容とリマインドタイミングを簡潔に伝えてください。

ユーザーのメッセージ: {message}"""

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )

            result = json.loads(response.text)
            return result

        except json.JSONDecodeError:
            return {
                "tasks": [],
                "response_message": "🙏 メッセージの解析に失敗しました。もう一度送ってみてください。",
            }
        except Exception as e:
            print(f"AI解析エラー: {e}")
            return {
                "tasks": [],
                "response_message": "⚠️ エラーが発生しました。しばらくしてからもう一度お試しください。",
            }
