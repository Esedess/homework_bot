import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

import bot_exceptions

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    filename='main.log',
    filemode='a',
    encoding='utf-8',
    format='%(asctime)s [%(levelname)s] %(message)s',
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_RETRY_TIME = 600

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправка сообщения в телеграмм.
    Функция send_message() отправляет сообщение в Telegram чат,
    определяемый переменной окружения TELEGRAM_CHAT_ID.
    Принимает на вход два параметра:
    - экземпляр класса Bot и строку с текстом сообщения.
    """
    logger.debug(
        f'send_message.bot = {bot}\nsend_message.message = {message}'
    )
    logger.info(f'Сообщение отправлено. --->>> "{message}"')
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp: int) -> dict:
    """Получение ответа от API.
    Функция get_api_answer() делает запрос к единственному эндпоинту
    API-сервиса. В качестве параметра функция получает временную метку.
    В случае успешного запроса должна вернуть ответ API,
    преобразовав его из формата JSON к типам данных Python.
    """
    timestamp: int = current_timestamp or int(time.time())
    logger.debug(f'get_api_answer.timestamp = {timestamp}')
    params: dict = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            params=params,
            headers=HEADERS,
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        raise err

    # if response.status_code != 200:
    #     raise bot_exceptions.WrongAPIStatusCodeError(
    #         'Сервер API вернул код отличный от 200.'
    #     )

    logger.debug('-- response.json успешно получен и возвращен')
    logger.debug(f'{response.json()}')
    return response.json()


def check_response(response) -> list:
    """Проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python. Если ответ API соответствует ожиданиям,
    то функция должна вернуть список домашних работ (он может быть и пустым),
    доступный в ответе API по ключу 'homeworks'.
    """
    logger.debug(f'check_response.response = {response}')
    API_KEY_1: str = 'homeworks'
    API_KEY_2: str = 'current_date'

    if not isinstance(response, dict):
        raise bot_exceptions.WrongAPIResponseTypeError(
            'Ответ от API имеет некорректный тип.'
        )
    if API_KEY_1 in response and API_KEY_2 in response:
        if not isinstance(response.get(API_KEY_1), list):
            raise bot_exceptions.WrongAPIResponseTypeError(
                'Ответ от API имеет некорректный тип.'
            )
        logger.debug('-- response успешно проверен и возвращен')
        return response.get(API_KEY_1)

    raise bot_exceptions.WrongAPIResponseError(
        'API вернул не верный ответ.'
    )


def parse_status(homework: dict) -> str:
    """Проверка статуса работы.
    Функция parse_status() извлекает из информации о конкретной
    домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент
    из списка домашних работ.
    В случае успеха, функция возвращает подготовленную для отправки в
    Telegram строку, содержащую один из вердиктов словаря HOMEWORK_STATUSES.
    """
    logger.debug(f'parse_status.homework = {homework}')

    homework_name: str = homework.get('homework_name')
    homework_status: str = homework.get('status')

    if homework_status not in HOMEWORK_STATUSES:
        raise bot_exceptions.WrongHomeworkStatusError(
            'Неожиданный статус домашней работы.'
        )
    verdict: str = HOMEWORK_STATUSES.get(homework_status)
    logger.debug('-- вернули подготовленное сообщение')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверка токенов.
    Проверяет доступность переменных окружения,
    которые необходимы для работы программы.
    Если отсутствует хотя бы одна переменная окружения —
    функция должна вернуть False, иначе — True.
    """
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID and PRACTICUM_TOKEN:
        logger.debug('check_tokens = True')
        return True
    logger.debug('check_tokens = False')
    logger.critical(
        f'\n>>> TELEGRAM_TOKEN = {bool(TELEGRAM_TOKEN)}'
        f'\n>>> TELEGRAM_CHAT_ID = {bool(TELEGRAM_CHAT_ID)}'
        f'\n>>> PRACTICUM_TOKEN = {bool(PRACTICUM_TOKEN)}'
    )
    return False


def logic(bot: telegram.Bot, current_timestamp: int) -> None:
    """Основная логика работы бота."""
    logger.debug(
        f'-- logic.current_timestamp = {current_timestamp}'
    )
    response: dict = get_api_answer(current_timestamp)
    homeworks: list = check_response(response)
    if homeworks:
        logger.debug('Есть новые данные о работах!')
        for homework in homeworks:
            message = parse_status(homework)
            send_message(bot, message)
    else:
        logger.debug(
            f'{current_timestamp} | Новых данных о работах нет.'
        )


def main():
    """Основная логика работы бота.
    В ней описана основная логика работы программы.
    Все остальные функции должны запускаться из неё.
    Последовательность действий должна быть примерно такой:
    - Сделать запрос к API.
    - Проверить ответ.
    - Если есть обновления — получить статус работы из обновления и
    отправить сообщение в Telegram.
    - Подождать некоторое время и сделать новый запрос.
    """
    logger.debug('\n\n<<<------------- New run ------------->>>\n')
    logger.debug('main')

    current_timestamp: int = int(time.time())

    if not check_tokens():
        raise SystemExit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    telegramm_send_an_error_message = True
    while True:
        logger.debug('\n<-------- New iteration -------->')
        try:
            logic(bot, current_timestamp)
        except Exception as error:
            logger.debug('-- main.while.except')
            message = f'Сбой в работе программы:\n{error}'
            logger.error(message)
            if telegramm_send_an_error_message:
                send_message(bot, message)
                telegramm_send_an_error_message = False
        else:
            current_timestamp = int(time.time())
        finally:
            time.sleep(TELEGRAM_RETRY_TIME)
        logger.debug('\n<-------- Iteration done-------->')


if __name__ == '__main__':
    main()
