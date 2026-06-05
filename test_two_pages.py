import re
from playwright.sync_api import BrowserContext, expect


def test_two_pages(context: BrowserContext):
    page_one = context.new_page()
    page_two = context.new_page()

    page_one.goto("https://skillbox.ru/")
    page_two.goto('https://google.com')

    expect(page_one).to_have_title(re.compile("Skillbox"))
    expect(page_two).to_have_title(re.compile("Google"))
