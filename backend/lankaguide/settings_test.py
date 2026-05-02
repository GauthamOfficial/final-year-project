"""
Django settings for `pytest` only.

Import the real project settings, then force SQLite in-memory so tests do not
require MySQL privileges to `CREATE DATABASE test_*`.
"""
# noqa: F401,F403 — re-export full production settings, then override DB
from lankaguide.settings import *  # type: ignore

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
