import os
from playwright.sync_api import Page


class CartPage:
    def __init__(self, page: Page):
        self.page = page

        # Локаторы корзины и чекаута
        self.checkout_button = page.get_by_text("Proceed To Checkout")
        self.place_order_button = page.get_by_role("link", name="Place Order")

        # Локаторы формы оплаты
        self.card_name_input = page.locator('input[name="name_on_card"]')
        self.card_number_input = page.locator('input[name="card_number"]')
        self.card_cvc_input = page.get_by_role("textbox", name="ex.")
        self.card_month_input = page.get_by_role("textbox", name="MM")
        self.card_year_input = page.get_by_role("textbox", name="YYYY")
        self.submit_payment_button = page.get_by_role("button", name="Pay and Confirm Order")

        # Локатор кнопки скачивания инвойса
        self.download_invoice_button = page.get_by_role("link", name="Download Invoice")

    def proceed_to_checkout(self):
        """Переход к оформлению заказа."""
        self.checkout_button.wait_for(state="visible")
        self.page.wait_for_timeout(500)
        self.checkout_button.click()

        self.page.wait_for_url("**/checkout", wait_until="commit")
        self.place_order_button.click()

    def fill_payment_and_submit(self, name="Alegri Tester", card_number="1111222233334444", cvc="123", month="12",
                                year="2030"):
        """Заполнение платежных данных (по умолчанию используются тестовые) и подтверждение заказа."""
        self.card_name_input.fill(name)
        self.card_number_input.fill(card_number)
        self.card_cvc_input.fill(cvc)
        self.card_month_input.fill(month)
        self.card_year_input.fill(year)
        self.submit_payment_button.click()

    def download_invoice(self, target_directory: str = "downloads") -> str:
        """Скачивание инвойса и сохранение его в указанную папку. Возвращает полный путь к файлу."""
        os.makedirs(target_directory, exist_ok=True)

        with self.page.expect_download() as download_info:
            self.download_invoice_button.click()

        download = download_info.value
        file_path = os.path.join(target_directory, download.suggested_filename)
        download.save_as(file_path)

        return file_path

    def clear_cart(self):
        """Проверяет корзину и удаляет из неё все товары, если они там есть."""
        self.page.goto("https://automationexercise.com/view_cart", wait_until="domcontentloaded")
        self.page.wait_for_timeout(1500)
        product_rows = self.page.locator("tbody tr[id^='product-']")
        while product_rows.count() > 0:
            delete_btn = product_rows.first.locator(".cart_quantity_delete")
            if delete_btn.is_visible():
                delete_btn.click()
                product_rows.first.wait_for(state="hidden", timeout=3000)
            else:
                break