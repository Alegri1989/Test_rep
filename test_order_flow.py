import os
import json
import allure
from playwright.sync_api import Page, expect
from product_page import ProductPage
from cart_page import CartPage


with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


@allure.feature("Оформление заказов")
@allure.story("Заказ товаров одного бренда")
@allure.title("TC-01: Оформление заказа бренда и проверка инвойса")
@allure.description(
    "Авторизация, очистка корзины, добавление товара первого бренда, "
    "оплата и валидация скачанного файла инвойса."
)
def test_order_single_brand_product_and_verify_invoice(auth_page: Page):
    product_page = ProductPage(auth_page)
    cart = CartPage(auth_page)

    cart.clear_cart()
    product_page.open_brand(CONFIG["brand_first"])
    product_page.add_first_product_to_cart()
    product_page.go_to_cart()
    cart.proceed_to_checkout()
    cart.fill_payment_and_submit()

    with allure.step("Проверить успешность оформления заказа на UI"):
        expect(auth_page.get_by_text("Order Placed!")).to_be_visible()

    invoice_path = cart.download_invoice()

    with allure.step("Проверить, что файл инвойса скачан и содержит верные данные"):
        assert os.path.exists(invoice_path), (
            "Критическая ошибка: файл инвойса не скачался!"
        )
        with open(invoice_path, "r", encoding="utf-8") as file:
            invoice_text = file.read()

        assert CONFIG["invoice_user_name"] in invoice_text, (
            f"Неверное имя в инвойсе! Текст: {invoice_text}"
        )
        assert f"Your total purchase amount is {CONFIG['amount_single_brand']}" in invoice_text, (
            f"Неверная сумма! Текст: {invoice_text}"
        )


@allure.feature("Оформление заказов")
@allure.story("Заказ товаров нескольких брендов")
@allure.title("TC-02: Оформление мультибрендового заказа и проверка инвойса")
@allure.description(
    "Авторизация, очистка корзины, последовательное добавление товаров "
    "от двух разных брендов, проверка общего количества, оплата и валидация инвойса."
)
def test_order_multiple_brands_and_verify_invoice(auth_page: Page):
    product_page = ProductPage(auth_page)
    cart = CartPage(auth_page)

    cart.clear_cart()
    product_page.open_brand(CONFIG["brand_first"])
    product_page.add_first_product_to_cart()
    product_page.open_brand(CONFIG["brand_second"])
    product_page.add_first_product_to_cart()
    product_page.go_to_cart()

    with allure.step("Проверить, что в корзину добавлено 2 товара"):
        expect(auth_page.locator("tbody tr[id^='product-']")).to_have_count(2)

    cart.proceed_to_checkout()
    cart.fill_payment_and_submit()

    with allure.step("Проверить успешность оформления заказа на UI"):
        expect(auth_page.get_by_text("Order Placed!")).to_be_visible()

    invoice_path = cart.download_invoice()

    with allure.step(
        "Проверить, что файл инвойса скачан и содержит верные данные по обоим товарам"
    ):
        assert os.path.exists(invoice_path), (
            "Критическая ошибка: файл инвойса не скачался!"
        )
        with open(invoice_path, "r", encoding="utf-8") as file:
            invoice_text = file.read()

        assert CONFIG["invoice_user_name"] in invoice_text, (
            f"Неверное имя в инвойсе! Текст: {invoice_text}"
        )
        assert f"Your total purchase amount is {CONFIG['amount_multiple_brands']}" in invoice_text, (
            f"Неверная общая сумма товаров! Текст: {invoice_text}"
        )