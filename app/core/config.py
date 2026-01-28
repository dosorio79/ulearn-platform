"""Environment-backed configuration settings.

All configuration is resolved at import time.
Runtime behavior is controlled exclusively via environment variables.
"""

import os

# ---------------------------
# Database configuration
# ---------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ulearn")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "lesson_runs")
MONGO_FAILURE_COLLECTION = os.getenv(
    "MONGO_FAILURE_COLLECTION", "lesson_failures"
)

# ---------------------------
# Model / execution settings
# ---------------------------
MODEL = os.getenv("MODEL", "gpt-4.1-mini")
USE_LLM_CONTENT = os.getenv("USE_LLM_CONTENT", "false").lower() == "true"
CONTEXT7_API_KEY = os.getenv("CONTEXT7_API_KEY", "")

# Telemetry configuration
TELEMETRY_BACKEND = os.getenv("TELEMETRY_BACKEND", "mongo").lower()
try:
    TELEMETRY_MEMORY_CAP = int(os.getenv("TELEMETRY_MEMORY_CAP", "1000"))
except (TypeError, ValueError):
    TELEMETRY_MEMORY_CAP = 1000
TELEMETRY_INCLUDE_HINT_DETAILS = os.getenv("TELEMETRY_INCLUDE_HINT_DETAILS", "true").lower() == "true"

# Lesson execution modes
STATIC_LESSON_MODE = os.getenv("STATIC_LESSON_MODE", "false").lower() == "true"
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# ---------------------------
# Demo mode override
# ---------------------------
# DEMO_MODE is a convenience flag that forces:
# - static lessons
# - in-memory telemetry
if DEMO_MODE:
    STATIC_LESSON_MODE = True
    TELEMETRY_BACKEND = "memory"

# ---------------------------
# Validation
# ---------------------------
VALID_TELEMETRY_BACKENDS = {"mongo", "memory"}

# Runtime smoke test (advisory only)
RUNTIME_SMOKE_TEST_ENABLED = os.getenv("RUNTIME_SMOKE_TEST_ENABLED", "false").lower() == "true"
try:
    RUNTIME_SMOKE_TEST_TIMEOUT_SECONDS = float(
        os.getenv("RUNTIME_SMOKE_TEST_TIMEOUT_SECONDS", "0.25")
    )
except (TypeError, ValueError):
    RUNTIME_SMOKE_TEST_TIMEOUT_SECONDS = 0.25

if TELEMETRY_BACKEND not in VALID_TELEMETRY_BACKENDS:
    raise ValueError(
        f"Invalid TELEMETRY_BACKEND '{TELEMETRY_BACKEND}'. "
        f"Valid values: {sorted(VALID_TELEMETRY_BACKENDS)}"
    )

# ---------------------------
# Optional runtime summary (useful for /health or logs)
# ---------------------------
def runtime_mode() -> dict:
    return {
        "demo_mode": DEMO_MODE,
        "static_lesson_mode": STATIC_LESSON_MODE,
        "telemetry_backend": TELEMETRY_BACKEND,
        "model": MODEL,
        "runtime_smoke_test_enabled": RUNTIME_SMOKE_TEST_ENABLED,
    }
