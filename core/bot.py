import re
from io import BytesIO
from openpyxl import Workbook
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder,\
                         ContextTypes, CommandHandler,\
                         CallbackQueryHandler, MessageHandler,\
                         filters
from telegram.error import BadRequest
from core.base_api import API
from core.utils import ADMIN_START_MENU_KEYBOARD, USER_START_MENU_KEYBOARD,\
                       QUIZZES_MENU_KEYBOARD, ADMIN_PANEL_KEYBOARD
from core.filters import StartFilter, RealNameFilter, QuizCreationFilter, AdminFilter
from core.quiz_builder import QuizBuilder, QuizCreationError
from core.logger import Logger


class QuizBot:
    __slots__ = ('_api', '_app')

    def __init__(self,
                 token, api: API,
                 admin_key: str) -> None:
        self._app = ApplicationBuilder().token(token).build()
        self._api = api
        self._add_handlers(admin_key)
    
    def _add_handlers(self, admin_key: str) -> None:
        start_filter = StartFilter(self._api)
        real_name_filter = RealNameFilter(self._api)
        admin_filter = AdminFilter(self._api)
        quiz_creation_filter = QuizCreationFilter(self._api)

        self._app.add_handlers([
            CommandHandler(admin_key, self._make_user_admin),
            CommandHandler('menu', self._start_menu),
            CommandHandler('start', self._authorize_user, start_filter),
            MessageHandler(filters.TEXT & real_name_filter, self._set_user_real_name),
            MessageHandler(admin_filter & filters.TEXT & quiz_creation_filter, self._create_quiz),
            CallbackQueryHandler(self._create_quiz, pattern='cancel'),
            CallbackQueryHandler(self._show_quizzes_to_pass, pattern='choose_quiz'),
            CallbackQueryHandler(self._toggle_quiz_activity, pattern='toggle:*'),
            CallbackQueryHandler(self._delete_confirmation, pattern='request_deletion:*'),
            CallbackQueryHandler(self._delete_quiz, pattern='delete:*'),
            CallbackQueryHandler(self._init_user_quiz, pattern='choose:*'),
            CallbackQueryHandler(self._manage_quiz, pattern='manage:*'),
            CallbackQueryHandler(self._download_quiz_results, pattern='download:*'),
            CallbackQueryHandler(self._get_quiz_results, pattern='results:*'),
            CallbackQueryHandler(self._submit_quiz_answer, pattern='quize:*'),
            CallbackQueryHandler(self._change_user_real_name, pattern='edit_real_name'),
            CallbackQueryHandler(self._quizzes_menu, pattern='quizzes_menu'),
            CallbackQueryHandler(self._init_quiz_creation, pattern='create_quiz'),
            CallbackQueryHandler(self._return, pattern='return:*'),
            CallbackQueryHandler(self._show_quizzes_to_manage, pattern='show_quizzes_to_manage'),
            CallbackQueryHandler(self._show_admin_panel, pattern='admin_panel'),
            CallbackQueryHandler(self._show_users_list, pattern='users_list'),
            CallbackQueryHandler(self._show_logs, pattern='logs:*'),
            CallbackQueryHandler(self._clear_logs, pattern='clear_logs:*')
        ])

    async def _show_users_list(self,
                               update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        users = self._api.get_all_users()

        message = '\n'.join(f'[{x[0]}]({x[1]}) - {x[2]}{" (admin)" if x[3] else ""}'\
                             for x in users)

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('🔄 Обновить', callback_data='users_list')],
                [InlineKeyboardButton('↩️ Назад', callback_data='return:admin_panel')],
                [InlineKeyboardButton('🏠 Домой', callback_data='return:menu')]
            ]
        )

        try:
            await context.bot.edit_message_text(
                text=message,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        except BadRequest:
            pass

    async def _clear_logs(self,
                         update: Update,
                         context: ContextTypes.DEFAULT_TYPE):
        log_type = update.callback_query.data.split(':')[1]

        Logger.clear_logs(log_type)

        await self._show_logs(update, context)

    async def _show_logs(self,
                         update: Update,
                         context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        log_type = update.callback_query.data.split(':')[1]

        with open(f'logs/{log_type}_logs.txt', 'r') as f:
            message = '\n'.join(f.readlines())

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('🔄 Обновить', callback_data=f'logs:{log_type}')],
                [InlineKeyboardButton('🧹 Очистить', callback_data=f'clear_logs:{log_type}')],
                [InlineKeyboardButton('↩️ Назад', callback_data='return:admin_panel')],
                [InlineKeyboardButton('🏠 Домой', callback_data='return:menu')]
            ]
        )    

        try:
            await context.bot.edit_message_text(
                text=message,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard
            )
        except BadRequest:
            pass

    async def _show_admin_panel(self,
                               update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        keyboard = ADMIN_PANEL_KEYBOARD

        await context.bot.edit_message_text(
            text='Панель администратора',
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )

    async def _make_user_admin(self,
                               update: Update,
                               context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self._api.make_user_admin(user_id)

        await self._start_menu(update, context)

    async def _init_quiz_creation(self,
                                  update: Update,
                                  context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message_id = update.effective_message.id
        self._api.init_quiz_creation(user_id)

        message = ("Ожидается сообщение следующего формата:\n\n"
                    "Название квиза\n"
                    "Количество вопросов\n"
                    "Номера правильных ответов (пробел в качестве разделителя)\n"
                    "[$Формулировка вопросов$] (Начало и конец секции - знак \"$\", точка с запятой в качестве разделителя формулировок)\n"
                    "[~Формулировка вариантов ответов~] (Начало и конец секции - знак \"~\", разделитель между вариантами - двоеточие, между вопросами - точка с запятой)]\n"        
                    "Каждый из параметров вводится с новой строки.\n\n"
                    "Параметры помещенные в квадратные скобки являются опциональными. Если их не задавать, будут использованы значения по умолчанию:\n"
                    "*для вопросов - \"Вопрос №1\", \"Вопрос №2\"... и так далее по указанному количеству вопросов;\n"
                    "*для формулировок вариантов ответов - для всех вопрос будут заданые значения от 1 до 4.\n"
                    "Ввиду ограничений Telegram, не рекомендуется делать варианты ответов длинее 35-40 символов."
                    "Если формулировка варианта ответа будет слишком длинной, то текст не будет переноситься в пределах кнопки,"
                    " а будет обрезан многоточием.")
        
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('↩️ Отмена', callback_data='cancel')]
            ]
        )

        await context.bot.edit_message_text(
            text=message,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard
        )

    async def _return(self,
                     update: Update,
                     context: ContextTypes.DEFAULT_TYPE):
        return_type = update.callback_query.data.split(":")[1]
        message_id = update.effective_message.id

        if return_type == 'menu':
            await self._start_menu(update, context, message_id)
        elif return_type == 'quizzes_menu':
            await self._quizzes_menu(update, context)
        elif return_type == 'quizzes_to_manage':
            await self._show_quizzes_to_manage(update, context)
        elif return_type == 'admin_panel':
            await self._show_admin_panel(update, context)

    async def _toggle_quiz_activity(self,
                                    update: Update,
                                    context: ContextTypes.DEFAULT_TYPE):
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        self._api.toggle_quiz_activity(quiz_id)

        await self._manage_quiz(update, context)
    
    async def _delete_quiz(self,
                           update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        self._api.delete_quiz(quiz_id)

        quizzes = self._api.get_all_quizzes()

        if not quizzes:
            await self._start_menu(update, context)
        else:
            await self._show_quizzes_to_manage(update, context)

    async def _download_quiz_results(self,
                                     update: Update,
                                     context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        results = self._api.get_quiz_results(quiz_id)

        wb = Workbook()
        sheet = wb.active
        sheet['A1'] = 'ФИО'
        sheet['B1'] = 'Телеграм'
        sheet['C1'] = 'Результат'

        for i, res in enumerate(results):
            sheet[f'A{i+2}'] = res[0]
            sheet[f'B{i+2}'] = res[1]
            sheet[f'C{i+2}'] = res[2]
        
        excel_file = BytesIO()
        wb.save(excel_file)

        quiz_name = str(self._api.fetch_quiz(quiz_id)['name'])
        await context.bot.send_document(
                    chat_id,
                    document=excel_file.getvalue(),
                    filename=f'{quiz_name}.xlsx'
        )

    async def _get_quiz_results(self,
                                update: Update,
                                context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        results = self._api.get_quiz_results(quiz_id)

        if not results:
            await context.bot.answer_callback_query(
                update.callback_query.id,
                text='Нет результатов для данного квиза',
                show_alert=True
            )
        else:
            message = '\n'.join(f'[{x[0]}]({x[1]}) - {x[2]}' for x in results)
            if message == update.effective_message.text:
                return
            keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton('⬇️ Скачать xlsx документ', callback_data=f'download:{quiz_id}')],
                    [InlineKeyboardButton('🔄 Обновить', callback_data=f'results:{quiz_id}')],
                    [InlineKeyboardButton('↩️ Назад', callback_data=f'manage:{quiz_id}'),
                    InlineKeyboardButton('🏠 Домой', callback_data='return:menu')]
                ]
            )

            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            except BadRequest:
                pass

    async def _delete_confirmation(self,
                                  update: Update,
                                  context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quiz_id = update.callback_query.data.split(':')[1]
        
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('✅ Да', callback_data=f'delete:{quiz_id}')],
                [InlineKeyboardButton('❌ Нет', callback_data=f'manage:{quiz_id}')]
            ]
        )

        await context.bot.edit_message_text(
            chat_id=chat_id,
            text='Уверен?',
            message_id=message_id,
            reply_markup=keyboard
        )

    async def _manage_quiz(self,
                           update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        quiz_info = self._api.fetch_quiz(quiz_id)

        message = f'*Название*: {quiz_info["name"]}\n\n*Вопросы*:\n'
        for i, (x, y) in enumerate(zip(quiz_info['qa_pairs'], quiz_info['right_answers'])):
            question, answers = next(iter((x.items())))
            message += f'{i+1}. {question}\nВарианты ответов:\n•'
            message += '\n•'.join(answers)
            message += f'\n(Правильный ответ - {y})\n' 
        message += '\n*Статус*: '
        message += '🟩 (активен)' if quiz_info['is_active'] else '🟥 (неактивен)'

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('🔄 Сменить статус', callback_data=f'toggle:{quiz_id}')],
                [InlineKeyboardButton('📋 Получить результаты', callback_data=f'results:{quiz_id}')],
                [InlineKeyboardButton('🗑️ Удалить', callback_data=f'request_deletion:{quiz_id}')],
                [InlineKeyboardButton('↩️ Назад', callback_data='return:quizzes_to_manage'),
                 InlineKeyboardButton('🏠 Домой', callback_data='return:menu')],
            ]
        )

        await context.bot.edit_message_text(
            text=message,
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )

    async def _show_quizzes_to_manage(self,
                                      update: Update,
                                      context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quizzes = self._api.get_all_quizzes()

        if not quizzes:
            await context.bot.answer_callback_query(
                update.callback_query.id,
                text='Нет созданных квизов',
                show_alert=True
            )
        else:
            keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(
                        name, callback_data='manage:'+id
                    )] for id, name, _  in quizzes
                    ] + 
                    [[InlineKeyboardButton('↩️ Назад', callback_data='return:quizzes_menu'),
                     InlineKeyboardButton('🏠 Домой', callback_data='return:menu')]]
                )
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text='Выбери квиз:',
                reply_markup=keyboard
            )

    async def _quizzes_menu(self,
                            update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quizzes = self._api.get_all_quizzes()

        if quizzes:
            message = 'Доступные квизы:\n-' +\
                      '\n-'.join(f'{name} ({"🟩" if is_active else "🟥"})' \
                        for _, name, is_active in quizzes)
        else:
            message = 'Нет созданных квизов'
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=message,
            reply_markup=QUIZZES_MENU_KEYBOARD
        )

    async def _change_user_real_name(self,
                                     update: Update,
                                     context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        self._api.change_user_real_name(chat_id, None)

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text='Укажите, пожалуйста, Ваше ФИО'
        )

    async def _create_quiz(self,
                           update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        if update.callback_query is not None:
            self._api.cancel_quiz_creation(chat_id)
            await self._quizzes_menu(update, context)
            return

        try:
            quiz_data = QuizBuilder.\
                        create_quiz_from_message(update.effective_message.text)
            self._api.add_quiz(quiz_data)
            await context.bot.send_message(
                chat_id=chat_id,
                text='Квиз успешно добавлен!'
            )
            await self._start_menu(update, context)
        except QuizCreationError as err:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f'{err}. Попробуй еще раз.'
            )
        except Exception as exc:
            Logger.log(exc, 'error')
            await context.bot.send_message(
                chat_id=chat_id,
                text='Ошибка при создании квиза. Попробуй еще раз.'
            )

    async def _start_menu(self,
                          update: Update, 
                          context: ContextTypes.DEFAULT_TYPE,
                          message_id: int = None):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        if message_id is None:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f'Добро пожаловать,\n{self._api.get_user_real_name(user_id)}!',
                reply_markup=ADMIN_START_MENU_KEYBOARD if self._api.is_user_admin(user_id)\
                                                       else USER_START_MENU_KEYBOARD
            )
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id = message_id,
                text=f'Добро пожаловать,\n{self._api.get_user_real_name(chat_id)}!',
                reply_markup=ADMIN_START_MENU_KEYBOARD if self._api.is_user_admin(user_id)\
                                                       else USER_START_MENU_KEYBOARD
            )

    async def _set_user_real_name(self,
                                  update: Update,
                                  context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message_text = update.effective_message.text.strip().lower()

        if not re.match('^([а-я]+ +[а-я]+ +[а-я]+)$', message_text):
            await context.bot.send_message(
                chat_id=chat_id,
                text='Неправильный формат ФИО.'+\
                     ' Необходимо указать данные на кириллице. Попробуй еще раз.'
            )
        else:
            real_name = ' '.join(x.capitalize() for x in message_text.split() if x)
            self._api.change_user_real_name(user_id, real_name)
            await self._start_menu(update, context)

    async def _authorize_user(self,
                              update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        self._api.add_user(
            update.effective_user.id,
            update.effective_user.username,
            update.effective_user.first_name
        )

        await context.bot.send_message(
            chat_id=chat_id,
            text='Укажите, пожалуйста, Ваше ФИО'
        )
    
    async def _show_quizzes_to_pass(self,
                                    update: Update,
                                    context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        active_quizzes = list(filter(lambda x: x[2], self._api.get_all_quizzes()))
        if not active_quizzes:
            await context.bot.answer_callback_query(
                update.callback_query.id,
                text='Нет активных квизов',
                show_alert=True
            )
        else:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    name, callback_data='choose:'+id
                )] for id, name, _ in active_quizzes] +
                [[InlineKeyboardButton('↩️ Назад', callback_data='return:menu')]]
            )

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text='Активные квизы:',
                reply_markup=keyboard
            )

    async def _init_user_quiz(self,
                              update: Update, 
                              context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message_id = update.effective_message.id
        quiz_id = update.callback_query.data.split(':')[1]

        if self._api.is_user_passed_quiz(user_id, quiz_id):
            await context.bot.answer_callback_query(
                update.callback_query.id,
                text='Ты уже проходил этот квиз',
                show_alert=True
            )
        else:
            self._api.init_user_quiz(user_id, quiz_id)
            quiz_info = self._api.get_user_quiz_info(user_id)
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    x, callback_data=f'quize:{quiz_id}:answer:{i+1}'
                )]  for i, x in enumerate(quiz_info[1])]
            )

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=quiz_info[0],
                reply_markup=keyboard
            )

    async def _submit_quiz_answer(self,
                                  update: Update,
                                  context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message_id = update.effective_message.id
        callback_data = update.callback_query.data.split(':')
        quiz_id = callback_data[1]
        answer = int(callback_data[3])

        self._api.update_user_quiz_data(user_id, answer)
        quiz_info = self._api.get_user_quiz_info(user_id)
        if quiz_info is None:
            await context.bot.delete_message(chat_id, message_id)
            await context.bot.send_message(
            chat_id=chat_id,
            text='Спасибо за прохождения опроса! Жди результат :)'
            )
            self._api.submit_user_results(user_id)
            if self._api.is_user_admin(user_id):
                await self._start_menu(update, context)
        else:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    x, callback_data=f'quize:{quiz_id}:answer:{i+1}'
                )]  for i, x in enumerate(quiz_info[1])]
            )

            await context.bot.edit_message_text(
                    quiz_info[0],
                    chat_id,
                    message_id,
                    reply_markup=keyboard
            )

    def run(self) -> None:
        Logger.log('Bot session started', 'info')
        self._app.run_polling()
        Logger.log('Bot session stoped', 'info')
