"""Talk to the LLM engine via HTTP"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol

import httpx


class LLMUnavailable(Exception):
    """Engine unreachable, timed out, HTTP error, error chunk, or output not parseable

    Reasons are fixed short strings: never the engine's body or the prompt, which
    holds the student's answer
    """


@dataclass(frozen=True)
class Usage:
    """Token counts from the model"""

    prompt_tokens: int = 0
    output_tokens: int = 0

    @property
    def total(self) -> int:
        """Sum of prompt and output tokens"""
        return self.prompt_tokens + self.output_tokens


class LLMClient(Protocol):
    """Interface to the language model"""

    model: str

    async def complete_json(
        self, system: str, user: str, schema: dict[str, Any], max_tokens: int
    ) -> tuple[dict[str, Any], Usage]:
        """Get a JSON response with schema validation"""

    def stream_text(
        self, system: str, user: str, max_tokens: int
    ) -> AsyncIterator[str | Usage]:
        """Stream text response as an async generator"""


class OllamaClient:
    """Client for Ollama's native API"""

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        proxy: str | None = None,
        timeout: float = 60.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self._proxy = proxy
        self._timeout = timeout
        self._transport = transport

    async def complete_json(
        self, system: str, user: str, schema: dict[str, Any], max_tokens: int
    ) -> tuple[dict[str, Any], Usage]:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            # think: False — the chosen model returns empty with thinking on,
            # non-thinking models accept the flag
            "think": False,
            "keep_alive": "30m",
            # format constrains decoding to the JSON schema
            "format": schema,
            "options": {
                # temperature 0 — the same answer gets the same grade
                "temperature": 0,
                "num_ctx": 4096,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                proxy=self._proxy or None,
                timeout=httpx.Timeout(
                    self._timeout, connect=5.0  # short connect for fail-fast on switched-off
                ),
                transport=self._transport,
            ) as client:
                response = await client.post("/api/chat", json=body)

            if response.status_code >= 400:
                raise LLMUnavailable(f"engine error {response.status_code}")

            data = response.json()
            content = data.get("message", {}).get("content")
            if not content:
                raise LLMUnavailable("empty engine output")

            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise LLMUnavailable("malformed engine output")

            usage = Usage(
                prompt_tokens=data.get("prompt_eval_count", 0),
                output_tokens=data.get("eval_count", 0),
            )
            return parsed, usage

        except json.JSONDecodeError as exc:
            raise LLMUnavailable("malformed engine output") from exc
        except KeyError as exc:
            raise LLMUnavailable("malformed engine output") from exc
        except httpx.HTTPError as exc:
            raise LLMUnavailable("engine unreachable") from exc

    async def stream_text(
        self, system: str, user: str, max_tokens: int
    ) -> AsyncIterator[str | Usage]:
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": True,
            "think": False,
            "keep_alive": "30m",
            "options": {
                "temperature": 0,
                "num_ctx": 4096,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                proxy=self._proxy or None,
                timeout=httpx.Timeout(
                    self._timeout, connect=5.0
                ),
                transport=self._transport,
            ) as client:
                async with client.stream("POST", "/api/chat", json=body) as response:
                    if response.status_code >= 400:
                        await response.aread()
                        raise LLMUnavailable(f"engine error {response.status_code}")

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError as exc:
                            raise LLMUnavailable("malformed engine output") from exc

                        if "error" in chunk:
                            raise LLMUnavailable("engine error")

                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content

                        if chunk.get("done"):
                            yield Usage(
                                prompt_tokens=chunk.get("prompt_eval_count", 0),
                                output_tokens=chunk.get("eval_count", 0),
                            )

        except httpx.HTTPError as exc:
            raise LLMUnavailable("engine unreachable") from exc
