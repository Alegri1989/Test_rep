from playwright.sync_api import Page

class ProductPage:
    def __init__(self, page: Page):
        self.page = page
        # Локатор кнопки корзины в верхнем меню сайта
        self.cart_link = page.get_by_role("link", name=" Cart")

    def open_brand(self, brand_name: str):
        """Открывает страницу и кликает по указанному бренду в левом меню."""
        self.page.goto("https://automationexercise.com/products", wait_until="commit")
        # Ищем бренд динамически по его имени, например, "Polo" или "Biba"
        self.page.get_by_role("link", name=f" {brand_name}").click()

    def add_first_product_to_cart(self):
        """Наводит мышь на первый товар бренда и добавляет его в корзину."""
        self.page.locator(".product-image-wrapper").first.hover()
        self.page.locator(".product-overlay").first.get_by_text("Add to cart").click()
        continue_btn = self.page.get_by_role("button", name="Continue Shopping")
        continue_btn.click()
        continue_btn.wait_for(state="hidden")

    def go_to_cart(self):
        """Переходит в корзину через верхнее навигационное меню."""
        self.cart_link.click()