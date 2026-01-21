"""MongoDB client helpers for telemetry persistence."""

from __future__ import annotations

from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection

from app.core import config

# Global variable to hold the MongoDB client instance
_client: MongoClient | None = None
_memory_runs: list[dict] = []
_memory_failures: list[dict] = []


def reset_memory_store() -> None:
    """Reset in-memory telemetry storage (test helper)."""
    _memory_runs.clear()
    _memory_failures.clear()


def get_memory_runs() -> list[dict]:
    """Return in-memory lesson run telemetry (test helper)."""
    return list(_memory_runs)


def get_memory_failures() -> list[dict]:
    """Return in-memory failure telemetry (test helper)."""
    return list(_memory_failures)

# Singleton pattern for MongoDB client
def get_client() -> MongoClient:
    """Return a singleton MongoDB client."""
    global _client
    if _client is None:
        _client = MongoClient(config.MONGO_URI)
    return _client

# Get a specific collection from the database
def get_collection() -> Collection[Any]:
    """Return the configured telemetry collection."""
    client = get_client()
    db = client[config.MONGO_DB_NAME]
    return db[config.MONGO_COLLECTION]


def get_failure_collection() -> Collection[Any]:
    """Return the configured failure collection."""
    client = get_client()
    db = client[config.MONGO_DB_NAME]
    return db[config.MONGO_FAILURE_COLLECTION]

# Insert a document into the lesson_runs collection
def insert_lesson_run(doc: dict) -> None:
    """Insert a telemetry document into MongoDB."""
    if config.TELEMETRY_BACKEND == "memory":
        _memory_runs.append(doc)
        cap = max(config.TELEMETRY_MEMORY_CAP, 0)
        if cap and len(_memory_runs) > cap:
            del _memory_runs[:-cap]
        return
    col = get_collection()
    col.insert_one(doc)


def insert_lesson_failure(doc: dict) -> None:
    """Insert a failure document into MongoDB."""
    if config.TELEMETRY_BACKEND == "memory":
        _memory_failures.append(doc)
        cap = max(config.TELEMETRY_MEMORY_CAP, 0)
        if cap and len(_memory_failures) > cap:
            del _memory_failures[:-cap]
        return
    col = get_failure_collection()
    col.insert_one(doc)
