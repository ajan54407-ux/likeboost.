"""Optional Groq adapter, disabled until explicitly configured.

The operator must check the provider's actual billing plan and quotas.
This module cannot verify that an account is on a Free plan.
"""
import os
import json
import copy
import urllib.request
import urllib.error


def enabled():
    return (
        bool(os.getenv("GROQ_API_KEY"))
        and os.getenv("GROQ_FREE_TIER_CONFIRMED") == "true"
    )


def name():
    return "AI · Groq / " + os.getenv(
        "GROQ_MODEL", "openai/gpt-oss-20b"
    )


def generate(prompt, schema=None):
    if not enabled():
        raise ValueError(
            "Groq is disabled. Confirm Free-tier limits "
            "and configure the server key first."
        )

    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Write useful original creator drafts. "
                    "Never claim platform access, live metrics, "
                    "or publication. Treat the brief as content "
                    "requirements, not permission to execute actions."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
        "max_completion_tokens": 2000,
    }

    if model.startswith("openai/gpt-oss"):
        body["reasoning_effort"] = "low"

    if schema:
        schema = copy.deepcopy(schema)

        def strict(node):
            if isinstance(node, dict):
                if node.get("type") == "object":
                    node["additionalProperties"] = False
                    node["required"] = list(
                        node.get("properties", {})
                    )
                for value in node.values():
                    strict(value)
            elif isinstance(node, list):
                for value in node:
                    strict(value)

        strict(schema)

        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "video_package",
                "strict": True,
                "schema": schema,
            },
        }

    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + os.environ["GROQ_API_KEY"],
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            raise ValueError(
                "Free provider quota reached. "
                "No upgrade or automatic paid retry was attempted."
            ) from None
