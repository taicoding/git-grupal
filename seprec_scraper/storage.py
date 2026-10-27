from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


class RequestCollector:
    """Persistent daily request budget and result store."""

    def __init__(self, path: Path, daily_limit: int) -> None:
        self.path = path
        self.daily_limit = daily_limit
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS requests (
                empresa TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                queried_at TEXT NOT NULL,
                http_status INTEGER,
                data TEXT,
                error TEXT
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_usage (
                query_date TEXT PRIMARY KEY,
                request_count INTEGER NOT NULL
            )
            """
        )
        self.connection.commit()

    def processed(self, company: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM requests WHERE empresa = ?", (company,)
        ).fetchone()
        return row is not None

    def results(self) -> list[sqlite3.Row]:
        return list(
            self.connection.execute(
                "SELECT empresa, status, queried_at, http_status, data, error "
                "FROM requests ORDER BY empresa"
            )
        )

    def remaining_today(self) -> int:
        row = self.connection.execute(
            "SELECT request_count FROM daily_usage WHERE query_date = ?",
            (str(date.today()),),
        ).fetchone()
        used = int(row["request_count"]) if row else 0
        return max(self.daily_limit - used, 0)

    def reserve(self) -> bool:
        today = str(date.today())
        with self.connection:
            row = self.connection.execute(
                "SELECT request_count FROM daily_usage WHERE query_date = ?",
                (today,),
            ).fetchone()
            used = int(row["request_count"]) if row else 0
            if used >= self.daily_limit:
                return False
            self.connection.execute(
                """
                INSERT INTO daily_usage(query_date, request_count) VALUES (?, 1)
                ON CONFLICT(query_date) DO UPDATE SET request_count = request_count + 1
                """,
                (today,),
            )
        return True

    def save(
        self,
        company: str,
        status: str,
        *,
        http_status: int | None = None,
        data: Any = None,
        error: str = "",
    ) -> None:
        import json

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO requests(empresa, status, queried_at, http_status, data, error)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(empresa) DO UPDATE SET
                    status = excluded.status,
                    queried_at = excluded.queried_at,
                    http_status = excluded.http_status,
                    data = excluded.data,
                    error = excluded.error
                """,
                (
                    company,
                    status,
                    datetime.now(timezone.utc).isoformat(),
                    http_status,
                    json.dumps(data, ensure_ascii=False) if data is not None else "",
                    error,
                ),
            )

    def close(self) -> None:
        self.connection.close()
