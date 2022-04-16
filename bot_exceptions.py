class WrongAPIStatusCodeError(Exception):
    """Сервер API вернул код отличный от 200."""

    pass


class WrongAPIResponseError(Exception):
    """API вернул не верный ответ."""

    pass


class WrongAPIResponseTypeError(TypeError):
    """API вернул не верный ответ."""

    pass


class WrongHomeworkStatusError(KeyError):
    """Неожиданный статус домашней работы."""

    pass
