"""Optional local inference adapter."""
import os
import json
import urllib.request
from urllib.parse import urlparse

import hosted_ai


def configured():
    return bool(
        os.getenv("LOCAL_AI_BASE_URL")
        or os.getenv("OLLAMA_MODEL")
        or hosted_ai.enabled()
    )


def engine_name():
    if hosted_ai.enabled():
        return hosted_ai.name()
    if os.getenv("LOCAL_AI_BASE_URL"):
        return "Local AI · " + os.getenv(
            "LOCAL_AI_LABEL", "Creator model"
        )
    if os.getenv("OLLAMA_MODEL"):
        return "Local AI · " + os.getenv("OLLAMA_MODEL")
    return "Local draft engine"


def completion(prompt, schema=None):
    url = os.getenv("LOCAL_AI_BASE_URL", "").rstrip("/")
    if not url:
        raise ValueError(
            "Local inference endpoint is not configured."
        )

    host = urlparse(url).hostname
