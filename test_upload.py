from playwright.sync_api import Page, expect


def test_upload(page: Page):
    page.goto("https://tus.io/demo")
    page.get_by_label("Select a file you want to upload").click()
    page.get_by_label("Select a file you want to upload").set_input_files("for_upload.txt")
    expect(page.get_by_text("The upload is complete!")).to_be_visible()
