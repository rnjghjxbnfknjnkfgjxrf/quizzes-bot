from datetime import datetime
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

def log(message: str):
    print(message)
    with open('logs.txt', 'a') as f:
        f.write(f'|{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}| ~ {message}\n')


USER_KEYBOARD = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton('✍️ Редактировать ФИО', callback_data='edit_real_name')],
                        [InlineKeyboardButton('🔢 Выбрать квиз', callback_data='choose_quiz')]
                    ]
                )
        
ADMIN_KEYBOARD = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton('✍️ Редактировать ФИО', callback_data='edit_real_name')],
                        [InlineKeyboardButton('🔢 Пройти квиз', callback_data='choose_quiz')],
                        [InlineKeyboardButton('🛠 Меню квизов', callback_data='quizzes_menu')]                    ]
                )

QUIZZES_MENU_KEYBOARD = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton('🛠 Управление квизами', callback_data='show_quizzes_to_manage')],
                        [InlineKeyboardButton('🛠 Создать квиз', callback_data='create_quiz')],
                        [InlineKeyboardButton('↩️ Назад', callback_data='return:menu')]
                    ]
                )
