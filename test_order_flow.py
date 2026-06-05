import os
from playwright.sync_api import Page, expect
from product_page import ProductPage  # Импортируем новую страницу
from cart_page import CartPage


def test_order_single_brand_product_and_verify_invoice(auth_page: Page):
    """Тест-кейс 1: Заказ товара бренда Polo, оплата и проверка текста инвойса."""
    product_page = ProductPage(auth_page)
    cart = CartPage(auth_page)
    cart.clear_cart()
    product_page.open_brand("Polo")
    product_page.add_first_product_to_cart()
    product_page.go_to_cart()
    cart.proceed_to_checkout()
    cart.fill_payment_and_submit()
    expect(auth_page.get_by_text("Order Placed!")).to_be_visible()
    invoice_path = cart.download_invoice()
    assert os.path.exists(invoice_path), "Критическая ошибка: файл инвойса не скачался!"
    with open(invoice_path, "r", encoding="utf-8") as file:
        invoice_text = file.read()

    assert "Hi 1 1" in invoice_text, f"Неверное имя в инвойсе! Текст: {invoice_text}"
    assert "Your total purchase amount is 500" in invoice_text, f"Неверная сумма! Текст: {invoice_text}"


def test_order_multiple_brands_and_verify_invoice(auth_page: Page):
    """Тест-кейс 2: Заказ товаров разных брендов (Polo и Biba), оплата и проверка инвойса."""
    product_page = ProductPage(auth_page)
    cart = CartPage(auth_page)
    cart.clear_cart()
    product_page.open_brand("Polo")
    product_page.add_first_product_to_cart()
    product_page.open_brand("Biba")
    product_page.add_first_product_to_cart()
    product_page.go_to_cart()
    expect(auth_page.locator("tbody tr[id^='product-']")).to_have_count(2)
    cart.proceed_to_checkout()
    cart.fill_payment_and_submit()
    expect(auth_page.get_by_text("Order Placed!")).to_be_visible()
    invoice_path = cart.download_invoice()
    assert os.path.exists(invoice_path), "Критическая ошибка: файл инвойса не скачался!"
    with open(invoice_path, "r", encoding="utf-8") as file:
        invoice_text = file.read()
    assert "Hi 1 1" in invoice_text, f"Неверное имя в инвойсе! Текст: {invoice_text}"
    assert "Your total purchase amount is 2030" in invoice_text, f"Неверная общая сумма товаров! Текст: {invoice_text}"