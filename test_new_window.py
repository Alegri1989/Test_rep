from playwright.sync_api import Page, expect


def test_new_window(page: Page):
    page.goto(
        "https://www.encodedna.com/javascript/demo/open-new-window-using-javascript-method.htm"
    )

    with page.expect_popup() as page2_info:
        page.get_by_role("button", name="Open a new window").click()

    page2 = page2_info.value
    expect(page2.get_by_text("The Markup with a Script")).to_be_visible()
    page2.close()
