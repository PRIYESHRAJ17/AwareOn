from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
# AWAREON INTELLIGENCE SQLITE CLOSE FIX V2
from typing import Any

from .contracts import EvidenceRecord, FieldObservation, utc_now, validate_evidence, validate_field_observation


DEFAULT_DB = os.getenv(
    "AWAREON_INTELLIGENCE_DB",
    "backend/awareon_intelligence.db",
)


class ProvenanceStore:
    """Append-oriented, evidence-linked operational ledger.

    This store is intentionally separate from model outputs. It records provenance,
    alert transitions, field observations, learning records and execution traces.
    It never changes engine formulas or alert policy automatically.
    """

    def __init__(self, path: str | None = None) -> None:
        self.path = path or DEFAULT_DB
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _session(self):
        """Open a SQLite connection and ALWAYS close it."""
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        directory = Path(self.path).parent
        if str(directory) not in ("", "."):
            directory.mkdir(parents=True, exist_ok=True)
        with self._session() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS evidence_registry (
                    evidence_id TEXT PRIMARY KEY,
                    evidence_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    source_id TEXT,
                    source_timestamp TEXT,
                    ingestion_timestamp TEXT NOT NULL,
                    freshness_seconds REAL,
                    geographic_scope TEXT,
                    dataset_version TEXT,
                    provenance_json TEXT NOT NULL,
                    quality REAL NOT NULL,
                    conflict_state TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    value_json TEXT,
                    checksum TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS alert_events (
                    event_id TEXT PRIMARY KEY,
                    cell_id TEXT NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS field_observations (
                    observation_id TEXT PRIMARY KEY,
                    cell_id TEXT NOT NULL,
                    observed_condition TEXT NOT NULL,
                    severity REAL NOT NULL,
                    observer TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    verification_status TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS knowledge_records (
                    knowledge_id TEXT PRIMARY KEY,
                    lesson TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    retired_at TEXT
                );
                CREATE TABLE IF NOT EXISTS execution_runs (
                    run_id TEXT PRIMARY KEY,
                    capability TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    input_hash TEXT,
                    output_hash TEXT,
                    degraded INTEGER NOT NULL DEFAULT 0,
                    details_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence_registry(source);
                CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence_registry(evidence_type);
                CREATE INDEX IF NOT EXISTS idx_alert_cell ON alert_events(cell_id);
                CREATE INDEX IF NOT EXISTS idx_field_cell ON field_observations(cell_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge_records(status);
                """
            )
            conn.commit()

    def register_evidence(self, record: EvidenceRecord) -> str:
        validate_evidence(record)
        checksum = record.checksum()
        with self._session() as conn:
            existing = conn.execute(
                "SELECT checksum FROM evidence_registry WHERE evidence_id=?",
                (record.evidence_id,),
            ).fetchone()
            if existing and existing["checksum"] != checksum:
                raise ValueError(
                    f"Evidence ID collision with different content: {record.evidence_id}"
                )
            conn.execute(
                """
                INSERT OR IGNORE INTO evidence_registry
                (evidence_id, evidence_type, source, source_id,
                 source_timestamp, ingestion_timestamp, freshness_seconds,
                 geographic_scope, dataset_version, provenance_json,
                 quality, conflict_state, claim, value_json, checksum, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.evidence_id,
                    record.evidence_type,
                    record.source,
                    record.source_id,
                    record.source_timestamp,
                    record.ingestion_timestamp,
                    record.freshness_seconds,
                    record.geographic_scope,
                    record.dataset_version,
                    json.dumps(record.provenance, sort_keys=True, default=str),
                    float(record.quality),
                    record.conflict_state,
                    record.claim,
                    json.dumps(record.value, sort_keys=True, default=str),
                    checksum,
                    utc_now(),
                ),
            )
            conn.commit()
        return record.evidence_id

    def record_alert_event(
        self,
        event_id: str,
        cell_id: str,
        from_state: str,
        to_state: str,
        actor: str,
        reason: str,
        evidence_ids: list[str],
    ) -> None:
        with self._session() as conn:
            conn.execute(
                """
                INSERT INTO alert_events
                (event_id, cell_id, from_state, to_state, actor, reason,
                 evidence_ids_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    cell_id,
                    from_state,
                    to_state,
                    actor,
                    reason,
                    json.dumps(sorted(set(evidence_ids))),
                    utc_now(),
                ),
            )
            conn.commit()

    def add_field_observation(self, observation: FieldObservation) -> str:
        validate_field_observation(observation)
        with self._session() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO field_observations
                (observation_id, cell_id, observed_condition, severity, observer,
                 observed_at, submitted_at, source, verification_status, notes,
                 evidence_ids_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    observation.observation_id,
                    observation.cell_id,
                    observation.observed_condition,
                    float(observation.severity),
                    observation.observer,
                    observation.observed_at,
                    observation.submitted_at,
                    observation.source,
                    observation.verification_status,
                    observation.notes,
                    json.dumps(list(observation.evidence_ids)),
                    json.dumps(observation.metadata, sort_keys=True, default=str),
                ),
            )
            conn.commit()
        return observation.observation_id

    def add_knowledge(
        self,
        knowledge_id: str,
        lesson: str,
        evidence_ids: list[str],
        confidence: float,
        scope: str = "AWAREON",
        status: str = "VALIDATED",
    ) -> None:
        with self._session() as conn:
            previous = conn.execute(
                "SELECT MAX(version) AS v FROM knowledge_records WHERE knowledge_id=?",
                (knowledge_id,),
            ).fetchone()
            version = int(previous["v"] or 0) + 1
            conn.execute(
                "UPDATE knowledge_records SET retired_at=? WHERE knowledge_id=? AND retired_at IS NULL",
                (utc_now(), knowledge_id),
            )
            conn.execute(
                """
                INSERT INTO knowledge_records
                (knowledge_id, lesson, evidence_ids_json, confidence, status,
                 scope, version, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    knowledge_id,
                    lesson,
                    json.dumps(sorted(set(evidence_ids))),
                    float(confidence),
                    status,
                    scope,
                    version,
                    utc_now(),
                ),
            )
            conn.commit()

    def record_run(
        self,
        run_id: str,
        capability: str,
        status: str,
        started_at: str,
        completed_at: str | None,
        input_hash: str | None,
        output_hash: str | None,
        degraded: bool,
        details: dict[str, Any],
    ) -> None:
        with self._session() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO execution_runs
                (run_id, capability, status, started_at, completed_at,
                 input_hash, output_hash, degraded, details_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    capability,
                    status,
                    started_at,
                    completed_at,
                    input_hash,
                    output_hash,
                    int(bool(degraded)),
                    json.dumps(details, sort_keys=True, default=str),
                ),
            )
            conn.commit()

    def list_field_observations(self, cell_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with self._session() as conn:
            rows = conn.execute(
                "SELECT * FROM field_observations WHERE cell_id=? ORDER BY observed_at DESC LIMIT ?",
                (cell_id, max(1, int(limit))),
            ).fetchall()
        return [
            {
                **dict(row),
                "evidence_ids": json.loads(row["evidence_ids_json"]),
                "metadata": json.loads(row["metadata_json"]),
            }
            for row in rows
        ]

    def list_alert_events(self, cell_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self._session() as conn:
            rows = conn.execute(
                "SELECT * FROM alert_events WHERE cell_id=? ORDER BY created_at DESC LIMIT ?",
                (cell_id, max(1, int(limit))),
            ).fetchall()
        return [
            {
                **dict(row),
                "evidence_ids": json.loads(row["evidence_ids_json"]),
            }
            for row in rows
        ]

    def knowledge_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        terms = [t.lower() for t in str(query).split() if len(t) >= 4][:8]
        if not terms:
            return []
        clauses = " OR ".join("LOWER(lesson) LIKE ?" for _ in terms)
        values = [f"%{t}%" for t in terms]
        values.append(max(1, int(limit)))
        with self._session() as conn:
            rows = conn.execute(
                f"SELECT * FROM knowledge_records WHERE retired_at IS NULL AND ({clauses}) ORDER BY confidence DESC, created_at DESC LIMIT ?",
                values,
            ).fetchall()
        return [
            {
                **dict(row),
                "evidence_ids": json.loads(row["evidence_ids_json"]),
            }
            for row in rows
        ]


provenance_store = ProvenanceStore()
