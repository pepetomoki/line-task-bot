"""タスクストア - SQLiteによるタスク永続管理"""

import sqlite3
from datetime import datetime
from typing import Optional


class TaskStore:
    """SQLiteベースのタスク管理"""

    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """DB接続を取得（Row型で返す）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """テーブル初期化"""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                detail TEXT DEFAULT '',
                due_date TEXT,
                remind_at TEXT,
                remind_sent INTEGER DEFAULT 0,
                source TEXT DEFAULT 'line',
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT DEFAULT (datetime('now', 'localtime'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                remind_at TEXT NOT NULL,
                sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        conn.close()

    def add_task(
        self,
        title: str,
        detail: str = "",
        due_date: Optional[str] = None,
        remind_times: Optional[list[str]] = None,
        source: str = "line",
    ) -> int:
        """タスクを追加し、リマインドも登録"""
        conn = self._get_conn()
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, detail, due_date, source)
            VALUES (?, ?, ?, ?)
            """,
            (title, detail, due_date, source),
        )
        task_id = cursor.lastrowid

        # リマインド時刻を登録
        if remind_times:
            for rt in remind_times:
                conn.execute(
                    """
                    INSERT INTO reminders (task_id, remind_at)
                    VALUES (?, ?)
                    """,
                    (task_id, rt),
                )

        conn.commit()
        conn.close()
        return task_id

    def get_pending_tasks(self) -> list[dict]:
        """未完了タスクを取得"""
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT * FROM tasks
            WHERE status = 'pending'
            ORDER BY
                CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
                due_date ASC,
                created_at ASC
            """
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_due_reminders(self) -> list[dict]:
        """送信すべきリマインドを取得（現在時刻以前かつ未送信）"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT r.id AS reminder_id, r.remind_at, r.task_id,
                   t.title, t.detail, t.due_date, t.status
            FROM reminders r
            JOIN tasks t ON r.task_id = t.id
            WHERE r.sent = 0
              AND r.remind_at <= ?
              AND t.status = 'pending'
            ORDER BY r.remind_at ASC
            """,
            (now,),
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def mark_reminder_sent(self, reminder_id: int):
        """リマインドを送信済みにする"""
        conn = self._get_conn()
        conn.execute(
            "UPDATE reminders SET sent = 1 WHERE id = ?",
            (reminder_id,),
        )
        conn.commit()
        conn.close()

    def complete_task(self, task_id: int) -> Optional[str]:
        """タスクを完了にする。タスク名を返す。"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT title FROM tasks WHERE id = ? AND status = 'pending'",
            (task_id,),
        ).fetchone()

        if not row:
            conn.close()
            return None

        title = row["title"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "UPDATE tasks SET status = 'done', updated_at = ? WHERE id = ?",
            (now, task_id),
        )
        conn.commit()
        conn.close()
        return title

    def delete_task(self, task_id: int) -> Optional[str]:
        """タスクを削除する。タスク名を返す。"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT title FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        if not row:
            conn.close()
            return None

        title = row["title"]
        conn.execute("DELETE FROM reminders WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return title

    def get_task_count(self) -> dict:
        """タスク数のサマリーを取得"""
        conn = self._get_conn()
        pending = conn.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'pending'"
        ).fetchone()["cnt"]
        done_today = conn.execute(
            """
            SELECT COUNT(*) as cnt FROM tasks
            WHERE status = 'done'
              AND date(updated_at) = date('now', 'localtime')
            """
        ).fetchone()["cnt"]
        conn.close()
        return {"pending": pending, "done_today": done_today}
