"""メッセージフォーマッター - 通知メッセージの整形"""

from datetime import datetime


def format_calendar_events(events: list[dict]) -> str:
    """Googleカレンダーの予定を通知メッセージに整形"""
    today = datetime.now()
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    date_str = today.strftime(f"%Y/%m/%d（{weekdays[today.weekday()]}）")

    if not events:
        return (
            f"📅 {date_str} の予定\n"
            f"\n"
            f"🎉 今日の予定はありません！\n"
            f"自由な1日を楽しみましょう✨"
        )

    lines = [f"📅 {date_str} の予定\n"]

    # 終日イベントを先に
    all_day = [e for e in events if e.get("is_all_day")]
    timed = [e for e in events if not e.get("is_all_day")]

    for event in all_day:
        lines.append(f"📌 終日　　   {event['title']}")
        if event.get("location"):
            lines.append(f"   📍{event['location']}")

    if all_day and timed:
        lines.append("")

    for event in timed:
        lines.append(f"⏰ {event['time_str']}  {event['title']}")
        if event.get("location"):
            lines.append(f"   📍{event['location']}")

    total = len(events)
    lines.append(f"\n合計: {total}件の予定")
    lines.append("今日も頑張りましょう！💪")

    return "\n".join(lines)


def format_task_list(tasks: list[dict]) -> str:
    """タスク一覧を整形"""
    if not tasks:
        return (
            "📋 タスク一覧\n"
            "\n"
            "✨ タスクはありません！\n"
            "新しいタスクはメッセージで送ってね📝"
        )

    lines = ["📋 現在のタスク一覧\n"]

    for i, task in enumerate(tasks, 1):
        emoji = _get_number_emoji(i)
        lines.append(f"{emoji} {task['title']}")

        if task.get("due_date"):
            try:
                due = datetime.strptime(task["due_date"], "%Y-%m-%d %H:%M")
                due_str = due.strftime("%m/%d %H:%M")
                lines.append(f"   📅 {due_str}")
            except ValueError:
                lines.append(f"   📅 {task['due_date']}")

        if task.get("detail"):
            lines.append(f"   📝 {task['detail']}")

    lines.append(f"\n完了したら「完了 番号」と送ってね！")
    lines.append(f"削除は「削除 番号」だよ🗑️")

    return "\n".join(lines)


def format_reminder(task: dict) -> str:
    """リマインド通知を整形"""
    lines = ["⏰ リマインド\n"]
    lines.append(f"📌 {task['title']}")

    if task.get("due_date"):
        try:
            due = datetime.strptime(task["due_date"], "%Y-%m-%d %H:%M")
            due_str = due.strftime("%m/%d %H:%M")
            lines.append(f"📅 期限: {due_str}")
        except ValueError:
            lines.append(f"📅 期限: {task['due_date']}")

    if task.get("detail"):
        lines.append(f"📝 {task['detail']}")

    lines.append("\n忘れずに対応してね！🙌")

    return "\n".join(lines)


def format_task_registered(response_message: str) -> str:
    """タスク登録完了メッセージ"""
    return response_message


def format_task_completed(title: str) -> str:
    """タスク完了メッセージ"""
    return f"✅ 「{title}」を完了にしました！\nお疲れさまです🎉"


def format_task_deleted(title: str) -> str:
    """タスク削除メッセージ"""
    return f"🗑️ 「{title}」を削除しました。"


def format_morning_greeting(
    events: list[dict], task_count: dict
) -> str:
    """朝の挨拶メッセージ（カレンダー予定 + タスクサマリー）"""
    today = datetime.now()
    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
    date_str = today.strftime(f"%Y/%m/%d（{weekdays[today.weekday()]}）")

    lines = [f"🌅 おはようございます！\n📅 {date_str}\n"]

    # カレンダー予定
    if events:
        lines.append("━━━ 今日の予定 ━━━")
        all_day = [e for e in events if e.get("is_all_day")]
        timed = [e for e in events if not e.get("is_all_day")]

        for event in all_day:
            lines.append(f"📌 終日 {event['title']}")

        for event in timed:
            lines.append(f"⏰ {event['time_str']} {event['title']}")
            if event.get("location"):
                lines.append(f"   📍{event['location']}")
    else:
        lines.append("📅 今日の予定はありません")

    # タスクサマリー
    lines.append("")
    pending = task_count.get("pending", 0)
    if pending > 0:
        lines.append(f"━━━ タスク ━━━")
        lines.append(f"📋 未完了: {pending}件")
        lines.append('「タスク一覧」で詳細を確認できます')
    else:
        lines.append("✨ 未完了タスクはありません！")

    lines.append("\n今日も1日頑張りましょう！💪")

    return "\n".join(lines)


def _get_number_emoji(n: int) -> str:
    """数字を絵文字に変換"""
    emojis = {
        1: "1️⃣",
        2: "2️⃣",
        3: "3️⃣",
        4: "4️⃣",
        5: "5️⃣",
        6: "6️⃣",
        7: "7️⃣",
        8: "8️⃣",
        9: "9️⃣",
    }
    return emojis.get(n, f"🔹")
