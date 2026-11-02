"""Standalone service launcher for the ERP backend.

Runs uvicorn headlessly (pythonw / Task Scheduler) with rotating file logs,
independent of any console window or parent session. Environment defaults are
applied BEFORE importing the app so pydantic-settings prefers them over .env.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/warehouse_management",
)
# JWT_SECRET intentionally has no default: app.config requires it (from .env
# or the environment) and refuses the previously published value in production.
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("CACHE_ENABLED", "false")

file_handler = RotatingFileHandler(
    os.path.join(BASE_DIR, "service.log"),
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8",
)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
)
root = logging.getLogger()
root.setLevel(logging.INFO)
root.addHandler(file_handler)

with open(os.path.join(BASE_DIR, "service.pid"), "w", encoding="ascii") as fh:
    fh.write(str(os.getpid()))

if __name__ == "__main__":
    import sys

    # Windows: the default Proactor event loop is prone to killing its
    # listening socket after "Accept failed / WinError 64" glitches under
    # load, which requires a full process restart. The Selector loop is far
    # more stable for this workload (pure HTTP, no subprocesses).
    if sys.platform == "win32":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        log_config=None,
        access_log=True,
    )
