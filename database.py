"""SQLite support with an optional PostgreSQL adapter."""
import os
import re
import sqlite3
import threading
import atexit
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path

_pool = None
_pool_lock = threading.Lock()


class Record(Mapping):
    def __init__(self, keys, values):
        self.data = dict(zip(keys, values))
        self.values_tuple = tuple(values)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.values_tuple[key]
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)


class Cursor:
    def __init__(self, cursor):
        self.c = cursor

    @property
    def rowcount(self):
        return self.c.rowcount if self.c else 0

    def fetchone(self):
        if not self.c:
            return None
        row = self.c.fetchone()
        if row is None:
            return None
        return Record([d.name for d in self.c.description], row)

    def fetchall(self):
        return list(self)

    def __iter__(self):
        while (row := self.fetchone()) is not None:
            yield row


class PgConnection:
    def __init__(self, connection):
        self.c = connection

    def execute(self, sql, params=()):
        import psycopg

        sql = sql.strip()
        if sql.upper().startswith("PRAGMA"):
            return Cursor(None)

        if sql.upper() == "BEGIN IMMEDIATE":
            return Cursor(
                self.c.execute(
                    "SELECT pg_advisory_xact_lock(3840261101)"
                )
            )

        ignore = bool(re.match(r"INSERT\s+OR\s+IGNORE", sql, re.I))
        sql = re.sub(
            r"INSERT\s+OR\s+IGNORE", "INSERT", sql, flags=re.I
        )
        sql = re.sub(
            r"\bINTEGER PRIMARY KEY\b",
            "BIGSERIAL PRIMARY KEY",
            sql,
            flags=re.I,
        )
        sql = re.sub(r"\bBLOB\b", "BYTEA", sql, flags=re.I)
        sql = re.sub(
            r"\bREAL\b", "DOUBLE PRECISION", sql, flags=re.I
        )
        sql = sql.replace("%", "%%").replace("?", "%s")

        if ignore:
            sql = sql.rstrip(";") + " ON CONFLICT DO NOTHING"

        try:
            return Cursor(self.c.execute(sql, params))
        except psycopg.IntegrityError as exc:
            raise sqlite3.IntegrityError(
                "Database constraint violation"
            ) from exc

    def executescript(self, script):
        for statement in script.split(";"):
            if statement.strip():
                self.execute(statement)

    def commit(self):
        self.c.commit()

    def rollback(self):
        self.c.rollback()


def postgres_pool():
    global _pool

    with _pool_lock:
        if _pool is None:
            from psycopg_pool import ConnectionPool
            from urllib.parse import urlparse, parse_qs

            url = os.environ["DATABASE_URL"]
            if not url.startswith(("postgres://", "postgresql://")):
                raise ValueError(
                    "DATABASE_URL must be a PostgreSQL connection string."
                )

            kwargs = {"connect_timeout": 15}
            parsed = urlparse(url)
            sslmode = parse_qs(parsed.query).get("sslmode", [""])[0]
            local_hosts = ("localhost", "127.0.0.1", "::1")

            if (
                parsed.hostname not in local_hosts
                and sslmode not in ("require", "verify-ca", "verify-full")
            ):
                kwargs["sslmode"] = "require"

            _pool = ConnectionPool(
                url,
                min_size=0,
                max_size=6,
                max_idle=60,
                timeout=30,
                kwargs=kwargs,
                open=True,
            )

    return _pool


@contextmanager
def connect(path):
    if os.getenv("DATABASE_URL"):
        with postgres_pool().connection() as connection:
            with connection.transaction():
                yield PgConnection(connection)
    else:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=20)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")

        try:
            with connection:
                yield connection
        finally:
            connection.close()


def close_pool():
    global _pool

    with _pool_lock:
        pool, _pool = _pool, None

    if pool is not None:
        pool.close(timeout=5)


atexit.register(close_pool)
