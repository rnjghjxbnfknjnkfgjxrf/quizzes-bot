from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


USER_START_MENU_KEYBOARD = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton('✍️ Редактировать ФИО', callback_data='edit_real_name')],
                        [InlineKeyboardButton('🧩 Пройти квиз', callback_data='choose_quiz')]
                    ]
                )
        
ADMIN_START_MENU_KEYBOARD = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton('✍️ Редактировать ФИО', callback_data='edit_real_name')],
                        [InlineKeyboardButton('🧩 Пройти квиз', callback_data='choose_quiz')],
                        [InlineKeyboardButton('🛠 Меню квизов', callback_data='quizzes_menu')],
                        [InlineKeyboardButton('⚙️ Панель администратора', callback_data='admin_panel')]
                    ]
                )

QUIZZES_MENU_KEYBOARD = InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton('🎛️ Управление квизами', callback_data='show_quizzes_to_manage')],
                        [InlineKeyboardButton('🏗️ Создать квиз', callback_data='create_quiz')],
                        [InlineKeyboardButton('↩️ Назад', callback_data='return:menu')]
                    ]
                )

ADMIN_PANEL_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton('📝 Список пользователей', callback_data='users_list')],
        [InlineKeyboardButton('ℹ️ Логи с информацией', callback_data='logs:info')],
        [InlineKeyboardButton('⚠️ Логи с ошибками', callback_data='logs:error')],
        [InlineKeyboardButton('↩️ Назад', callback_data='return:menu')]
    ]
)

INIT_DB_QUERY = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username VARCHAR(40) NOT NULL,
        name VARCHAR(40) NOT NULL,
        real_name VARCHAR(127)
    );

    CREATE TABLE IF NOT EXISTS quizzes (
        quiz_id UUID PRIMARY KEY,
        name VARCHAR(40) NOT NULL UNIQUE,
        right_answers INTEGER[] NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT FALSE,
        qa_pairs JSON NOT NULL
    );

    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
        is_busy BOOLEAN NOT NULL DEFAULT FALSE
    );

    CREATE TABLE IF NOT EXISTS results (
        user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
        quiz_id UUID REFERENCES quizzes(quiz_id) ON DELETE CASCADE,
        result VARCHAR(10) NOT NULL
    );
"""