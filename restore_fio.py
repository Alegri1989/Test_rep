import json, sys
from pathlib import Path
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))
from playwright.sync_api import sync_playwright, Error as PlaywrightError
from pages.login_page import LoginPage
from pages.profile_page import ProfilePage
from helpers.network_helper import goto_with_retry

PROFILE_URL = "https://gsz.gov.by/registration/job-seeker/personal-info/"

with open(_ROOT / "config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

profile_data = CONFIG["default_profile"]
print("Целевое ФИО:", profile_data["last_name"], profile_data["first_name"], profile_data["middle_name"])

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--lang=ru-RU"], channel="chrome")
    context = browser.new_context(locale="ru-RU")
    page = context.new_page()
    page.set_default_navigation_timeout(45000)
    lp = LoginPage(page)

    authenticated = False
    for attempt in range(1, 4):
        try:
            lp.login(CONFIG['user_email'], CONFIG['user_password'])
            page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2000)
            print(f"Попытка {attempt}: URL = {page.url}")
            if "login_required" in page.url or "/user/login/" in page.url:
                print("  -> не аутентифицирован, повторяю")
                continue
            # Аутентифицированы — проверяем поле ФИО
            page.locator("#id_last_name").wait_for(state="visible", timeout=15000)
            authenticated = True
            break
        except PlaywrightError as e:
            print(f"Попытка {attempt}: {type(e).__name__}: {str(e)[:120]}")
            page.wait_for_timeout(1500 * attempt)
    if not authenticated:
        print("ЛОГИН НЕ УДАЛСЯ после 3 попыток")
        page.screenshot(path="diag_login_fail.png", full_page=True)
        context.close(); browser.close()
        sys.exit(1)

    print("Логин OK")
    prof = ProfilePage(page)
    print("Текущее ФИО до:",
          prof.last_name_input.input_value(),
          prof.first_name_input.input_value(),
          prof.middle_name_input.input_value())

    prof.fill_field_safely(prof.last_name_input, profile_data["last_name"])
    prof.fill_field_safely(prof.first_name_input, profile_data["first_name"])
    prof.fill_field_safely(prof.middle_name_input, profile_data["middle_name"])
    prof.save_changes()
    page.wait_for_timeout(1500)

    goto_with_retry(page, PROFILE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    prof = ProfilePage(page)
    l, f_, m = (prof.last_name_input.input_value(),
                prof.first_name_input.input_value(),
                prof.middle_name_input.input_value())
    print("ФИО после восстановления:", l, f_, m)
    ok = (l == profile_data["last_name"] and f_ == profile_data["first_name"] and m == profile_data["middle_name"])
    print("ВОССТАНОВЛЕНО:", ok)
    context.close()
    browser.close()
