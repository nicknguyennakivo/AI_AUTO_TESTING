# hybrid_agent.py
# Purpose: Combine Stagehand.execute (AI reasoning & navigation)
#          with Playwright (deterministic DOM actions)

from playwright.async_api import Page
from typing import List


class HybridAgent:
    def __init__(self, page: Page, stagehand):
        """
        :param page: Playwright Page instance
        :param stagehand: Stagehand instance (already bound to the page)
        """
        self.page = page
        self.stagehand = stagehand

    async def execute(self, steps: List[str]) -> None:
        """
        Run high-level natural language steps using Stagehand.execute
        Ideal for navigation, reasoning, waits, and verification
        """
        for step in steps:
            await self.stagehand.execute(step)

    async def replace_input(self, selector: str, value: str) -> None:
        """
        Deterministically replace the value of an input using Playwright
        This FORCE-clears the field and avoids Stagehand flakiness
        """
        locator = self.page.locator(selector)
        await locator.wait_for(state="visible")
        await locator.fill("")
        await locator.fill(value)

    async def clear_and_type(self, selector: str, value: str) -> None:
        """
        Keyboard-based clear + type (fallback for very custom inputs)
        Use only if fill() is blocked by the application
        """
        locator = self.page.locator(selector)
        await locator.wait_for(state="visible")
        await locator.click(force=True)
        await locator.press("Control+A")
        await locator.press("Backspace")
        await locator.type(value, delay=50)
