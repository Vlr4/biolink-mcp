#!/usr/bin/env python3
import asyncio
import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import aiohttp

logger = logging.getLogger(__name__)


class BiolinkHTTPError(RuntimeError):
    def __init__(self, status: int, path: str, detail: str):
        super().__init__(f"{status} on {path}: {detail}")
        self.status = status
        self.path = path
        self.detail = detail


class Http:
    """Single-session HTTP helper with retries, timeouts, and compact errors."""

    def __init__(
        self,
        base_url: str = "https://api-v3.monarchinitiative.org/v3/api/",
        timeout_s: float = 30.0,
        retries: int = 3,
        backoff_s: float = 0.75,
    ):
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        self.timeout = aiohttp.ClientTimeout(total=timeout_s)
        self.retries = retries
        self.backoff_s = backoff_s
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET with centralized retry on 429/5xx and compact error mapping."""
        url = path if path.startswith("http") else urljoin(self.base_url, path.lstrip("/"))
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.retries + 1):
            try:
                session = await self._get_session()
                logger.debug("HTTP GET %s params=%s", url, params)
                async with session.get(url, params=params) as resp:
                    if 200 <= resp.status < 300:
                        # Try JSON; if empty, return {}
                        text = await resp.text()
                        if not text:
                            return {}
                        try:
                            return json.loads(text)
                        except json.JSONDecodeError:
                            logger.warning("Non-JSON response from %s", url)
                            return {"raw": text}
                    # Retry on 429/5xx
                    if resp.status in (429, 500, 502, 503, 504):
                        detail_snippet = (await resp.text())[:300]
                        logger.warning("Retryable status %s on %s: %s", resp.status, url, detail_snippet)
                        raise BiolinkHTTPError(resp.status, url, detail_snippet)
                    # Non-retryable: raise immediately
                    detail_snippet = (await resp.text())[:300]
                    raise BiolinkHTTPError(resp.status, url, detail_snippet)
            except (aiohttp.ClientError, asyncio.TimeoutError, BiolinkHTTPError) as e:
                last_exc = e
                if attempt < self.retries:
                    await asyncio.sleep(self.backoff_s * attempt)
                    continue
                break

        # Exhausted retries
        if isinstance(last_exc, BiolinkHTTPError):
            raise last_exc
        raise BiolinkHTTPError(599, url, f"{type(last_exc).__name__}: {last_exc}")
