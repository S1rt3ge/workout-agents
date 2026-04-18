"""Ollama HTTP client wrapper."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from workout_agent.core.config import get_settings


class OllamaClient:
    """Minimal async client for Ollama chat and embedding endpoints."""

    def __init__(self, base_url: str, timeout_seconds: float = 60.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout_seconds)

    async def aclose(self) -> None:
        """Close underlying HTTP client."""

        await self._client.aclose()

    async def chat(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
    ) -> str:
        """Call Ollama chat endpoint and return text content."""

        print(f"[OllamaClient] POST {self._base_url}/api/chat model={model}")
        response = await self._client.post(
            "/api/chat",
            json={
                "model": model,
                "stream": False,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "options": {"temperature": temperature},
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("message", {}).get("content", "")

    async def chat_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_payload: dict[str, Any],
        temperature: float = 0.2,
    ) -> dict[str, Any]:
        """Request structured JSON output and parse it from the response."""

        user_prompt = (
            "Return ONLY valid JSON matching the requested schema. "
            "Do not include markdown fences or commentary.\n\n"
            f"Input:\n{json.dumps(user_payload, ensure_ascii=True, indent=2)}"
        )

        retry_suffix = (
            "\n\nYou must respond with valid JSON only. No markdown, no explanation. Raw JSON only."
        )
        last_error: Exception | None = None

        for attempt in range(3):
            prompt = user_prompt if attempt == 0 else f"{user_prompt}{retry_suffix}"
            raw_text = await self.chat(
                model=model,
                system_prompt=system_prompt,
                user_prompt=prompt,
                temperature=temperature,
            )
            try:
                return self._parse_json_from_text(raw_text)
            except ValueError as exc:
                last_error = exc

        raise ValueError(
            f"Unable to parse JSON from Ollama response after 3 attempts: {last_error}"
        )

    async def embed(self, *, model: str, text: str) -> list[float]:
        """Get embedding vector from Ollama embeddings endpoint."""

        print(f"[OllamaClient] POST {self._base_url}/api/embeddings model={model}")
        response = await self._client.post(
            "/api/embeddings",
            json={"model": model, "prompt": text},
        )
        response.raise_for_status()
        payload = response.json()
        embedding = payload.get("embedding", [])
        return [float(x) for x in embedding]

    @staticmethod
    def _parse_json_from_text(text: str) -> dict[str, Any]:
        """Extract JSON object from a potentially noisy LLM response."""

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("Top-level JSON payload is not an object")
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("Unable to locate JSON object in Ollama response")

        parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict):
            raise ValueError("Top-level JSON payload is not an object")
        return parsed


async def test_connection() -> None:
    settings = get_settings()
    url = f"{settings.ollama_base_url}/api/tags"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url)
        print(f"Ollama reachable: {response.status_code}")
        models = [model["name"] for model in response.json().get("models", [])]
        print(f"Available models: {models}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_connection())
