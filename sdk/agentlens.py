"""
AgentLens Python SDK
Usage:
    from agentlens import AgentLens
    lens = AgentLens(api_key="ak_your_key", base_url="http://localhost:8000")
    lens.log(user_message="...", agent_response="...")
"""

import httpx
import asyncio
from typing import Optional
from functools import wraps


class AgentLens:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {"x-api-key": api_key, "Content-Type": "application/json"}

    def log(
        self,
        user_message: str,
        agent_response: str,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """Log a conversation synchronously."""
        with httpx.Client() as client:
            r = client.post(
                f"{self.base_url}/log",
                headers=self.headers,
                json={
                    "user_message": user_message,
                    "agent_response": agent_response,
                    "session_id": session_id,
                    "metadata": metadata or {}
                },
                timeout=5.0
            )
            r.raise_for_status()
            return r.json()

    async def alog(
        self,
        user_message: str,
        agent_response: str,
        session_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        """Log a conversation asynchronously."""
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/log",
                headers=self.headers,
                json={
                    "user_message": user_message,
                    "agent_response": agent_response,
                    "session_id": session_id,
                    "metadata": metadata or {}
                },
                timeout=5.0
            )
            r.raise_for_status()
            return r.json()

    def analyze(self, limit: int = 50) -> dict:
        """Trigger analysis of unanalyzed conversations."""
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                f"{self.base_url}/analyze",
                headers=self.headers,
                json={"limit": limit}
            )
            r.raise_for_status()
            return r.json()

    def dashboard(self) -> dict:
        """Get dashboard data."""
        with httpx.Client() as client:
            r = client.get(f"{self.base_url}/dashboard", headers=self.headers)
            r.raise_for_status()
            return r.json()

    def watch(self, func):
        """Decorator to auto-log any function that takes user_message and returns a string."""
        @wraps(func)
        def wrapper(user_message: str, *args, **kwargs):
            response = func(user_message, *args, **kwargs)
            try:
                self.log(user_message=user_message, agent_response=str(response))
            except Exception as e:
                print(f"[AgentLens] Failed to log: {e}")
            return response
        return wrapper

    def watch_async(self, func):
        """Async decorator version."""
        @wraps(func)
        async def wrapper(user_message: str, *args, **kwargs):
            response = await func(user_message, *args, **kwargs)
            try:
                await self.alog(user_message=user_message, agent_response=str(response))
            except Exception as e:
                print(f"[AgentLens] Failed to log: {e}")
            return response
        return wrapper


# ── Quick usage example ──────────────────────────────────────────────────────
if __name__ == "__main__":
    lens = AgentLens(api_key="ak_demo_123456789")

    # Manual logging
    lens.log(
        user_message="How do I reset my password?",
        agent_response="You can reset your password by clicking 'Forgot Password' on the login page.",
        session_id="user-123"
    )

    # Using the decorator
    @lens.watch
    def my_agent(user_message: str) -> str:
        return f"I can help you with: {user_message}"

    my_agent("What's the weather today?")
    my_agent("I want a refund")
    my_agent("This is broken and I'm angry!")

    print("Logged! Now trigger analysis via POST /analyze")
