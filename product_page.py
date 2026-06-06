import allure
import json
from playwright.sync_api import Page

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

class ProductPage:
    def __init__(self, page: Page):
        self.page = page
        self.cart_link = page.get_by_role("link", name=" Cart")

    @allure.step("Открыть страницу бренда '{brand_name}'")
    def open_brand(self, brand_name: str):
        self.page.goto(f"{CONFIG['base_url']}/products", wait_until="commit")
        self.page.get_by_role("link", name=f" {brand_name}").click()

    @allure.step("Добавить первый товар бренда в корзину")
    def add_first_product_to_cart(self):
        self.page.locator(".product-image-wrapper").first.hover()
        self.page.locator(".product-overlay").first.get_by_text("Add to cart").click()
        continue_btn = self.page.get_by_role("button", name="Continue Shopping")
        continue_btn.click()
        continue_btn.wait_for(state="hidden")

    @allure.step("Перейти в корзину через верхнее меню")
    def go_to_cart(self):
        self.cart_link.click()