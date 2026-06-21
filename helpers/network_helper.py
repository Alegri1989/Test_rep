import logging
from playwright.sync_api import Page, Error as PlaywrightError


def goto_with_retry(page: Page, url: str, retries: int = 3, wait_until: str = "load", timeout: int = 45000):
    """
    Умный переход по URL с повторными попытками при сетевых сбоях/таймаутах.

    Полезно при нестабильном интернете или подтормаживающем сайте: вместо
    мгновенного падения теста делает до `retries` попыток с нарастающей паузой
    между ними (1с, 2с, 4с...).

    Ловит как TimeoutError (страница не успела загрузиться за отведенное время),
    так и сетевые ошибки уровня соединения (net::ERR_CONNECTION_RESET,
    net::ERR_CONNECTION_TIMED_OUT, net::ERR_CERT_AUTHORITY_INVALID и т.п.) —
    Playwright оборачивает все это в общий класс Error, а TimeoutError является
    его наследником, так что достаточно ловить базовый Error.

    :param page: страница Playwright
    :param url: адрес для перехода
    :param retries: количество попыток (по умолчанию 3)
    :param wait_until: до какого события ждать загрузку ("load", "domcontentloaded", "networkidle")
    :param timeout: таймаут одной попытки в мс (по умолчанию 45с — с запасом против 30с по умолчанию)
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            page.goto(url, wait_until=wait_until, timeout=timeout)
            return
        except PlaywrightError as error:
            last_error = error
            logging.warning(
                f"Попытка {attempt}/{retries} перехода на '{url}' не удалась ({error}), повтор..."
            )
            if attempt < retries:
                page.wait_for_timeout(1000 * (2 ** (attempt - 1)))  # 1с, 2с, 4с...
    # Если все попытки исчерпаны — даём тесту упасть с понятной ошибкой
    raise last_error


def retry_action(action, page: Page, retries: int = 3, label: str = "действие"):
    """
    Повторяет произвольное действие Playwright (клик, выбор из списка и т.п.)
    при таймаутах/сетевых сбоях — с нарастающей паузой между попытками (1с, 2с, 4с...).

    :param action: вызываемый без аргументов callable с самим действием
    :param page: страница Playwright (нужна для пауз между попытками)
    :param retries: количество попыток (по умолчанию 3)
    :param label: название действия для лога при повторе
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return action()
        except PlaywrightError as error:
            last_error = error
            logging.warning(
                f"Попытка {attempt}/{retries} выполнить '{label}' не удалась ({error}), повтор..."
            )
            if attempt < retries:
                page.wait_for_timeout(1000 * (2 ** (attempt - 1)))
    raise last_error
