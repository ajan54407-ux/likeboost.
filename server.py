import os
from pathlib import Path

if os.getenv("RENDER_EXTERNAL_URL") and not os.getenv("APP_BASE_URL"):
    os.environ["APP_BASE_URL"] = os.environ["RENDER_EXTERNAL_URL"].rstrip("/")

default_database = (
    "/tmp/likeboost/likeboost.sqlite3"
    if os.getenv("RENDER")
    else str(Path(__file__).parent / "likeboost.sqlite3")
)
os.environ.setdefault("DATABASE_PATH", default_database)
Path(os.environ["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)

os.environ.setdefault(
    "COOKIE_SECURE",
    "true" if os.getenv("APP_BASE_URL", "").startswith("https://") else "false",
)

if os.getenv("RENDER"):
    os.environ.setdefault("EPHEMERAL_STORAGE", "true")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "3000")),
        workers=1,
        access_log=False,
    )
