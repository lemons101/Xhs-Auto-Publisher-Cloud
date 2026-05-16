from __future__ import annotations

from pathlib import Path
from typing import Any


class BrowserSession:
    def __init__(
        self,
        *,
        profile_dir: Path,
        headless: bool,
        slow_mo_ms: int = 80,
    ) -> None:
        self.profile_dir = profile_dir
        self.headless = headless
        self.slow_mo_ms = slow_mo_ms
        self.playwright: Any = None
        self.context: Any = None
        self.page: Any = None

    async def __aenter__(self) -> "BrowserSession":
        try:
            from playwright.async_api import async_playwright
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "playwright is not installed. Install it with: pip install playwright && python -m playwright install chromium"
            ) from exc

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.playwright = await async_playwright().start()
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            headless=self.headless,
            slow_mo=self.slow_mo_ms,
            viewport={"width": 1440, "height": 1000},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
