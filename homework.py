import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

import bot_exceptions as e

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

RETRY_TIME = 10  # 600
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
    response = requests.get(
        ENDPOINT,
        params=params,
        headers=HEADERS,
    )

    if response.status_code == 200:
        logger.debug('-- response.json успешно получен и возвращен')
        logger.debug(f'{response.json()}')
        return response.json()

    logger.error('Сервер API вернул код отличный от 200.')
    raise e.WrongAPIStatusCodeError(
        'Сервер API вернул код отличный от 200.'
    )


def check_response(response) -> list:
    """Проверяет ответ API на корректность.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python. Если ответ API соответствует ожиданиям,
    то функция должна вернуть список домашних работ (он может быть и пустым),
    доступный в ответе API по ключу 'homeworks'.
    """
    logger.debug(f'check_response.response = {response}')
    API_key1: str = 'homeworks'
    API_key2: str = 'current_date'

    if not isinstance(response, dict):
        logger.error('Ответ от API имеет некорректный тип.')
        raise e.WrongAPIResponseTypeError(
            'Ответ от API имеет некорректный тип.'
        )
    if API_key1 in response and API_key2 in response:
        if not isinstance(response.get(API_key1), list):
            logger.error('Ответ от API имеет некорректный тип.')
            raise e.WrongAPIResponseTypeError(
                'Ответ от API имеет некорректный тип.'
            )
        logger.debug('-- response успешно проверен и возвращен')
        return response.get(API_key1)

    logger.error('API вернул не верный ответ')
    raise e.WrongAPIResponseError(
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

    verdict: str = HOMEWORK_STATUSES.get(homework_status)
    if verdict:
        logger.debug('-- вернули подготовленное сообщение')
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'

    logger.error('Неожиданный статус домашней работы.')
    raise e.WrongHomeworkStatusError(
        'Неожиданный статус домашней работы.'
    )


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
        logger.debug('Новых данных о работах нет.')


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
        message = 'Нет одного из токенов'
        try:
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
            send_message(bot, message)
            logger.critical('Отсутствует токен! Отправлена Телеграмма!')
        except Exception as error:
            logger.critical(
                f'Отсутствует токен! Телеграмма не отправилась!\n{error}'
            )
        logger.critical('Работа бота остановлена!')
        raise SystemExit(1)
    else:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)

    try:
        get_api_answer(current_timestamp)
    except Exception as error:
        message = f'Ошибка проверки доступа к АПИ!\n{error}'
        logger.error(message)
        send_message(bot, message)

    while True:
        logger.debug('\n<-------- New iteration -------->')
        try:
            logic(bot, current_timestamp)
        except Exception as error:
            logger.debug('-- main.while.except')
            message = f'Сбой в работе программы: {error}'
            logger.error(error)
            time.sleep(RETRY_TIME)
        else:
            current_timestamp = int(time.time())
            time.sleep(RETRY_TIME)
        logger.debug('\n<-------- Iteration done-------->')


if __name__ == '__main__':
    main()
