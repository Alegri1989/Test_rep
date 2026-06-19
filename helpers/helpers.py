from datetime import datetime


def calculate_expected_age(birth_date_str: str) -> str:
    """Динамически считает возраст на сегодняшний день по дате формата ДД.ММ.ГГГГ."""
    birth_date = datetime.strptime(birth_date_str, "%d.%m.%Y")
    today = datetime.today()

    age = today.year - birth_date.year

    # Корректируем, если день рождения в текущем году ещё не наступил
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    # Правильное склонение слова год/года/лет
    if 11 <= age % 100 <= 19:
        return f"{age} лет"
    elif age % 10 == 1:
        return f"{age} год"
    elif age % 10 in (2, 3, 4):
        return f"{age} года"
    else:
        return f"{age} лет"


def generate_test_date(birth_date_str: str, years_diff: int = -5) -> str:
    """Берет дату ДД.ММ.ГГГГ и сдвигает год на указанное количество лет."""
    day, month, year = birth_date_str.split(".")
    test_year = str(int(year) + years_diff)
    return f"{day}.{month}.{test_year}"

def format_phone_to_mask(digits: str) -> str:
    """Переводит строку цифр 375294445566 в формат маски +375 (29) 444-55-66."""
    if len(digits) != 12:
        return digits  # Если пришло что-то не то, возвращаем как есть
    return f"+{digits[:3]} ({digits[3:5]}) {digits[5:8]}-{digits[8:10]}-{digits[10:]}"