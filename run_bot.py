import argparse
from os import path
from dotenv import dotenv_values
from core.bot import QuizBot
from core.base_api import API
from core.db import DBTool
from core.logger import Logger


def main(config: dict) -> None:
    try:
        db = DBTool(
                config['DB_USERNAME'],
                config['DB_PASSWORD'],
                config['DB_HOST'],
                config['DB_PORT'],
                config['DB_NAME'])
    except Exception:
        print('Ошибка при подключении к БД. Проверьте файл error_logs.txt.')

    api = API(db)
    bot = QuizBot(config['TOKEN'], api, config['ADMIN_KEY'])

    bot.run()
    db.close_connection()


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(
        description='Telegram бот для проведения квизов.'
    )
    arg_parser.add_argument(
        '--clear-logs',
        action='store_true',
        help='Очищает файлы с логами перед запуском'
    )

    Logger.check_logs_dir_existence()
    args = arg_parser.parse_args()
    if args.clear_logs:
        Logger.clear_logs()

    if path.exists('.env'):
        config = dotenv_values('.env')
        main(config)
    else:
        print('Нет файла с переменными окружения. Запустите скрипт gen_dot_env.py для его генерации.')
