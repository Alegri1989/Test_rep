import os
from playwright.sync_api import Page


def test_download(page: Page):
    page.goto("https://testfiledownload.com/")
    with page.expect_download() as download_info:
        with page.expect_popup():
            page.locator("div:nth-child(12) > a").click()
    download = download_info.value

    assert os.path.exists(download.path())
