from playwright.sync_api import Page


def test_navigation(page: Page):
    page.goto("https://google.com")
    page.goto("https://skillbox.ru")
    page.go_back()
    page.go_forward()
    page.reload()
