"""
AgentLens Python SDK — production-grade client
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from functools import wraps
from typing import Any, Callable, Optional

import httpx

logger = logging.getLogger("agentlens")


class AgentLens:
    """
    AgentLens monitoring client.

    Quick start::

        from agentlens import AgentLens

        lens = AgentLens(api_key="ak_...")

        @lens.watch
        def my_agent(user_message: str) -> str:
            return call_llm(user_message)

    Fire-and-forget (non-blocking, safe for production)::

        lens = AgentLens(api_key="ak_...", fire_and_forget=True)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://shraman18-agentlens.hf.space",
        fire_and_forget: bool = True,
        timeout: float = 5.0,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.fire_and_forget = fire_and_forget
        self.timeout = timeout
        self.max_retries = max_retries
        self._headers = {"x-api-key": api_key, "Content-Type": "application/json"}
        # persistent sync client (connection pool)
        self._client = httpx.Client(
            headers=self._headers,
            timeout=httpx.Timeout(timeout),
        )
        # persistent async client (lazy-init)
        self._async_client: Optional[httpx.AsyncClient] = None
        self._lock = threading.Lock()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _post_sync(self, path: str, payload: dict) -> dict:
        last_err = None
        for attempt in range(self.max_retries + 1):
            try:
                r = self._client.post(f"{self.base_url}{path}", json=payload)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    time.sleep(0.5 * (2 ** attempt))
        raise last_err

    async def _post_async(self, path: str, payload: dict) -> dict:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                headers=self._headers,
                timeout=httpx.Timeout(self.timeout),
            )
        last_err = None
        for attempt in range(self.max_retries + 1):
            try:
                r = await self._async_client.post(f"{self.base_url}{path}", json=payload)
                r.raise_for_status()
                return r.json()
            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (2 ** attempt))
        raise last_err

    def _fire(self, path: str, payload: dict) -> None:
        """Send in background thread — never blocks caller."""
        def _run():
            try:
                self._post_sync(path, payload)
            except Exception as e:
                logger.debug(f"[AgentLens] background log failed: {e}")
        threading.Thread(target=_run, daemon=True).start()

    async def _fire_async(self, path: str, payload: dict) -> None:
        """Fire-and-forget in async context."""
        async def _run():
            try:
                await self._post_async(path, payload)
            except Exception as e:
                logger.debug(f"[AgentLens] async fire failed: {e}")
        asyncio.create_task(_run())

    # ── Public API ────────────────────────────────────────────────────────────

    def log(
        self,
        user_message: str,
        agent_response: str,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        latency_ms: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Log a conversation turn.

        If ``fire_and_forget=True`` (default), returns immediately and logs in
        a background thread — safe to call inside tight loops.
        """
        payload = {
            "user_message": user_message,
            "agent_response": agent_response,
            "session_id": session_id or str(uuid.uuid4()),
            "metadata": {**(metadata or {}), **({"model": model} if model else {}), **({"latency_ms": latency_ms} if latency_ms else {})},
        }
        if self.fire_and_forget:
            self._fire("/log", payload)
            return None
        return self._post_sync("/log", payload)

    async def alog(
        self,
        user_message: str,
        agent_response: str,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        latency_ms: Optional[int] = None,
        model: Optional[str] = None,
    ) -> Optional[dict]:
        """Async version of ``log``."""
        payload = {
            "user_message": user_message,
            "agent_response": agent_response,
            "session_id": session_id or str(uuid.uuid4()),
            "metadata": {**(metadata or {}), **({"model": model} if model else {}), **({"latency_ms": latency_ms} if latency_ms else {})},
        }
        if self.fire_and_forget:
            await self._fire_async("/log", payload)
            return None
        return await self._post_async("/log", payload)

    def analyze(self, limit: int = 50) -> dict:
        """Trigger batch analysis of unanalyzed conversations."""
        return self._post_sync("/analyze", {"limit": limit})

    def dashboard(self) -> dict:
        """Fetch dashboard stats."""
        r = self._client.get(f"{self.base_url}/dashboard")
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self._client.close()

    # ── Decorators ────────────────────────────────────────────────────────────

    def watch(
        self,
        func: Optional[Callable] = None,
        *,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        extract_user_message: Optional[Callable] = None,
    ):
        """
        Decorator that auto-logs any agent function.

        Works with positional or keyword ``user_message`` argument::

            @lens.watch
            def agent(user_message: str) -> str: ...

            @lens.watch(model="gpt-4o", session_id="user-123")
            def agent(user_message: str) -> str: ...

        The decorator captures latency automatically.
        """
        def decorator(fn: Callable) -> Callable:
            @wraps(fn)
            def wrapper(*args, **kwargs):
                msg = _extract_message(fn, args, kwargs, extract_user_message)
                t0 = time.monotonic()
                try:
                    response = fn(*args, **kwargs)
                    latency = int((time.monotonic() - t0) * 1000)
                    try:
                        self.log(
                            user_message=msg,
                            agent_response=str(response),
                            session_id=session_id,
                            latency_ms=latency,
                            model=model,
                        )
                    except Exception as e:
                        logger.debug(f"[AgentLens] watch log failed: {e}")
                    return response
                except Exception as exc:
                    latency = int((time.monotonic() - t0) * 1000)
                    try:
                        self.log(
                            user_message=msg,
                            agent_response=f"[ERROR] {exc}",
                            session_id=session_id,
                            latency_ms=latency,
                            model=model,
                            metadata={"error": True, "error_type": type(exc).__name__},
                        )
                    except Exception:
                        pass
                    raise
            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def watch_async(
        self,
        func: Optional[Callable] = None,
        *,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        extract_user_message: Optional[Callable] = None,
    ):
        """Async version of ``watch``."""
        def decorator(fn: Callable) -> Callable:
            @wraps(fn)
            async def wrapper(*args, **kwargs):
                msg = _extract_message(fn, args, kwargs, extract_user_message)
                t0 = time.monotonic()
                try:
                    response = await fn(*args, **kwargs)
                    latency = int((time.monotonic() - t0) * 1000)
                    try:
                        await self.alog(
                            user_message=msg,
                            agent_response=str(response),
                            session_id=session_id,
                            latency_ms=latency,
                            model=model,
                        )
                    except Exception as e:
                        logger.debug(f"[AgentLens] watch_async log failed: {e}")
                    return response
                except Exception as exc:
                    latency = int((time.monotonic() - t0) * 1000)
                    try:
                        await self.alog(
                            user_message=msg,
                            agent_response=f"[ERROR] {exc}",
                            session_id=session_id,
                            latency_ms=latency,
                            model=model,
                            metadata={"error": True, "error_type": type(exc).__name__},
                        )
                    except Exception:
                        pass
                    raise
            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_message(fn, args, kwargs, extractor=None) -> str:
    if extractor:
        try:
            return extractor(*args, **kwargs)
        except Exception:
            pass
    if "user_message" in kwargs:
        return str(kwargs["user_message"])
    import inspect
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    for i, name in enumerate(params):
        if name in ("user_message", "message", "query", "prompt", "input", "text"):
            if i < len(args):
                return str(args[i])
    if args:
        return str(args[0])
    return ""
