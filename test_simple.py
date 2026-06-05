import re
from playwright.sync_api import Page, expect


def test_simple(page: Page):
    page.evaluate("window.scrollBy(0,document.body.scrollHeight)")
    import time
    time.sleep(2)

