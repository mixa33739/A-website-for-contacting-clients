import re
from email_validator import validate_email as validate_email_lib, EmailNotValidError

def validate_email(email):
    """Проверка корректности email"""
    try:
        validate_email_lib(email)
        return True
    except EmailNotValidError:
        return False

def validate_password(password):
    """
    Проверка сложности пароля
    Возвращает None если пароль валиден, иначе сообщение об ошибке
    """
    if len(password) < 6:
        return 'Пароль должен содержать минимум 6 символов'
    if len(password) > 20:
        return 'Пароль должен содержать максимум 20 символов'
    if not re.search(r'[A-Za-z]', password):
        return 'Пароль должен содержать хотя бы одну букву'
    if not re.search(r'\d', password):
        return 'Пароль должен содержать хотя бы одну цифру'
    return None