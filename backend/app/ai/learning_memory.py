from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


DEFAULT_DB = os.getenv(
    "AWAREON_LEARNING_DB",
    "backend/awareon_learning.db",
)


@dataclass(frozen=True)
class LearningRecord:
    learning_id: str
    query: str
    lesson: str
    evidence_ids: tuple[str, ...]
    confidence: float
    status: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "learning_id": self.learning_id,
            "query": self.query,
            "lesson": self.lesson,
            "evidence_ids": list(self.evidence_ids),
            "confidence": self.confidence,
            "status": self.status,
            "created_at": self.created_at,
        }


class LearningMemory:
    """
    Controlled learning memory.

    Important:
    - Stores lessons.
    - Never changes AwareOn engine formulas.
    - Never changes risk thresholds.
    - Never changes production policy automatically.
    """

    def __init__(
        self,
        path: str = DEFAULT_DB,
    ) -> None:
        self.path = path
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.path
        )
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        directory = os.path.dirname(
            self.path
        )

        if directory:
            os.makedirs(
                directory,
                exist_ok=True,
            )

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_records (
                    learning_id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    lesson TEXT NOT NULL,
                    evidence_ids TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    @staticmethod
    def _make_id(
        query: str,
        lesson: str,
        evidence_ids: list[str],
    ) -> str:
        payload = json.dumps(
            {
                "query": query,
                "lesson": lesson,
                "evidence_ids": sorted(
                    evidence_ids
                ),
            },
            sort_keys=True,
        )

        digest = hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()[:20]

        return f"LRN-{digest.upper()}"

    def store(
        self,
        query: str,
        lesson: str,
        evidence_ids: list[str],
        confidence: float,
        *,
        status: str = "VALIDATED",
    ) -> LearningRecord:
        learning_id = self._make_id(
            query,
            lesson,
            evidence_ids,
        )

        created_at = datetime.now(
            timezone.utc
        ).isoformat()

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO learning_records
                (
                    learning_id,
                    query,
                    lesson,
                    evidence_ids,
                    confidence,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    learning_id,
                    query,
                    lesson,
                    json.dumps(
                        sorted(
                            evidence_ids
                        )
                    ),
                    float(
                        confidence
                    ),
                    status,
                    created_at,
                ),
            )
            connection.commit()

        return LearningRecord(
            learning_id=learning_id,
            query=query,
            lesson=lesson,
            evidence_ids=tuple(
                sorted(
                    evidence_ids
                )
            ),
            confidence=float(
                confidence
            ),
            status=status,
            created_at=created_at,
        )

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[LearningRecord]:
        terms = [
            term.strip().lower()
            for term in query.split()
            if len(term.strip()) >= 4
        ]

        if not terms:
            return []

        clauses = []
        values: list[Any] = []

        for term in terms[:8]:
            clauses.append(
                "(LOWER(query) LIKE ? OR LOWER(lesson) LIKE ?)"
            )
            like = f"%{term}%"
            values.extend(
                [like, like]
            )

        sql = (
            "SELECT * FROM learning_records "
            "WHERE "
            + " OR ".join(clauses)
            + " ORDER BY confidence DESC, created_at DESC "
            + "LIMIT ?"
        )

        values.append(
            max(1, int(limit))
        )

        with self._connect() as connection:
            rows = connection.execute(
                sql,
                values,
            ).fetchall()

        return [
            LearningRecord(
                learning_id=row["learning_id"],
                query=row["query"],
                lesson=row["lesson"],
                evidence_ids=tuple(
                    json.loads(
                        row["evidence_ids"]
                    )
                ),
                confidence=float(
                    row["confidence"]
                ),
                status=row["status"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM learning_records"
            ).fetchone()

        return int(
            row["count"]
        )


learning_memory = LearningMemory()
