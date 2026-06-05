import re
from playwright.sync_api import Browser, expect


def test_two_contexts(browser: Browser):
    context_one = browser.new_context()
    context_two = browser.new_context()

    page_one = context_one.new_page()
    page_two = context_two.new_page()

    page_one.goto("https://skillbox.ru/")
    page_two.goto('https://google.com')

    expect(page_one).to_have_title(re.compile("Skillbox"))
    expect(page_two).to_have_title(re.compile("Google"))
