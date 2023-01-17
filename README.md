# Простой бот для отслеживания статуса review на Я.Практикуме.

Каждые 600 секунд проверяет изменения в статусах ревью студента.

***

## Описание

Бот различает 3 статуса ревью, в соответствии со статусом в указанный телеграм чат будет отправлено одно из трех сообщений:
- approved - Работа проверена: ревьюеру всё понравилось. Ура!
- reviewing - Работа взята на проверку ревьюером.
- rejected - Работа проверена: у ревьюера есть замечания.

В случае получения неизвестного статуса или любой другой ошибки в работе бота:
- ошибка будет залоггирована
- по возможности будет отправлено сообщение с ошибкой в указанный телеграм чат

Бот работает автоматически до ручной остановки.

***

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/Esedess/homework_bot
```

```bash
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```bash
python -m venv env
```

```bash
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```bash
python -m pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```


Наполнить .env по примеру .env_example.


Запустить как обычный py.

***

## Tech Stack

+ `Python` : <https://github.com/python>
+ `python-dotenv` : <https://github.com/theskumar/python-dotenv>
+ `python-telegram-bot` : <https://github.com/python-telegram-bot/python-telegram-bot>

***

## Авторы

- [@Esedess](https://github.com/Esedess)
