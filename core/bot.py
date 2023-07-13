import re, uuid
from openpyxl import Workbook
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder,\
                         ContextTypes, CommandHandler,\
                         CallbackQueryHandler, MessageHandler,\
                         filters
from core.bot_session import BotSession
from core.utils import ADMIN_KEYBOARD, USER_KEYBOARD, QUIZZES_MENU_KEYBOARD
from core.filters import StartFilter, RealNameFilter, QuizCreationFilter
from core.quiz import QuizBuilder, QuizCreationError

class QuizBot:
    def __init__(self, token, admins) -> None:
        self._app = ApplicationBuilder().token(token).build()
        self._session = BotSession()
        self._admins = admins
        self._add_handlers()
    
    def _add_handlers(self) -> None:
        start_filter = StartFilter(self._session)
        real_name_filter = RealNameFilter(self._session)
        quiz_creation_filter = QuizCreationFilter(self._session, self._admins)

        self._app.add_handlers([
            CommandHandler('start', self._start_user_session, start_filter),
            MessageHandler(filters.TEXT & real_name_filter, self._set_user_real_name),
            MessageHandler(filters.TEXT & quiz_creation_filter, self._create_quiz),
            CallbackQueryHandler(self._create_quiz, pattern='cancel'),
            CallbackQueryHandler(self._show_quizzes_to_pass, pattern='choose_quiz'),
            CallbackQueryHandler(self._toggle_quiz_status, pattern='toggle:*'),
            CallbackQueryHandler(self._delete_confirmation, pattern='request_deletion:*'),
            CallbackQueryHandler(self._delete_quiz, pattern='delete:*'),
            CallbackQueryHandler(self._init_user_quiz, pattern='choose:*'),
            CallbackQueryHandler(self._manage_quiz, pattern='manage:*'),
            CallbackQueryHandler(self._download_quiz_results, pattern='download:*'),
            CallbackQueryHandler(self._get_quiz_results, pattern='results:*'),
            CallbackQueryHandler(self._submit_quiz_answer, pattern='quize:*'),
            CallbackQueryHandler(self._edit_user_real_name, pattern='edit_real_name'),
            CallbackQueryHandler(self._quizzes_menu, pattern='quizzes_menu'),
            CallbackQueryHandler(self._init_quiz_creation, pattern='create_quiz'),
            CallbackQueryHandler(self._return, pattern='return:*'),
            CallbackQueryHandler(self._show_quizzes_to_manage, pattern='show_quizzes_to_manage')
        ])

    async def _init_quiz_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        self._session.init_quiz_creation(chat_id)

        message = ("Ожидается сообщение следующего формата:\n\n"
                    "Название квиза\n"
                    "Количество вопросов\n"
                    "Номера правильных ответов (пробел в качестве разделителя)\n"
                    "[$Формулировка вопросов$] (Начало и конец секции - знак \"$\", точка с запятой в качестве разделителя формулировок)\n"
                    "[~Формулировка вариантов ответов~] (Начало и конец секции - знак \"~\", разделитель между вариантами - двоеточие, между вопросами - точка с запятой)]\n"        
                    "Каждый из параметров вводится с новой строки.\n\n"
                    "Параметры помещенные в квадратные скобки являются опциональными. Если их не задавать, будут использованы значения по умолчанию:\n"
                    "*для вопросов - \"Вопрос №1\", \"Вопрос №2\"... и так далее по указанному количеству вопросов;\n"
                    "* для формулировок вариантов ответов - для всех вопрос будут заданые значения от 1 до 4.")
        
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

    async def _return(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        return_type = update.callback_query.data.split(":")[1]
        message_id = update.effective_message.id

        if return_type == 'menu':
            await self._start_menu(update, context, message_id)
        elif return_type == 'quizzes_menu':
            await self._quizzes_menu(update, context)
        elif return_type == 'quizzes_to_manage':
            await self._show_quizzes_to_manage(update, context)

    async def _toggle_quiz_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        self._session.toggle_quiz_status(chat_id, uuid.UUID(quiz_id))

        await self._manage_quiz(update, context)
    
    async def _delete_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        self._session.delete_quiz(chat_id, uuid.UUID(quiz_id))

        await self._show_quizzes_to_manage(update, context)

    async def _download_quiz_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]

        quiz_name = str(self._session.get_quiz(uuid.UUID(quiz_id)))
        await context.bot.send_document(
                    chat_id,
                    document=quiz_name+'.xlsx'
        )

    async def _get_quiz_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        results = self._session.get_quiz_results(uuid.UUID(quiz_id))

        if not results:
            await context.bot.answer_callback_query(
                update.callback_query.id,
                text='Нет результатов для данного квиза',
                show_alert=True
            )
        else:
            results.sort(key=lambda x: int(x[1][0]), reverse=True)
            message = '\n'.join(f'[{u.real_name}](https://t.me/{u.username}) - {r}' for u,r in results)
            keyboard = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton('⬇️ Скачать xlsx документ', callback_data=f'download:{quiz_id}')],
                    [InlineKeyboardButton('↩️ Назад', callback_data=f'manage:{quiz_id}'),
                    InlineKeyboardButton('🏠 Домой', callback_data='return:menu')]
                ]
            )

            wb = Workbook()
            sheet = wb.active
            sheet['A1'] = 'ФИО'
            sheet['B1'] = 'Телеграм'
            sheet['C1'] = 'Результат'

            for i, (u, r) in enumerate(results):
                sheet[f'A{i+2}'] = u.real_name
                sheet[f'B{i+2}'] = f'https://t.me/{u.username}'
                sheet[f'C{i+2}'] = r
            
            quiz_name = str(self._session.get_quiz(uuid.UUID(quiz_id)))
            wb.save(quiz_name+'.xlsx')

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )

    async def _delete_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton('✅', callback_data=f'delete:{quiz_id}')],
                [InlineKeyboardButton('❌', callback_data=f'manage:{quiz_id}')]
            ]
        )

        await context.bot.edit_message_text(
            chat_id=chat_id,
            text='Уверен?',
            message_id=message_id,
            reply_markup=keyboard
        )

    async def _manage_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quiz_id = quiz_id = update.callback_query.data.split(':')[1]
        quiz_info = self._session.get_quiz(uuid.UUID(quiz_id)).as_dict()

        message = f'*Название*: {quiz_info["name"]}\n\n*Вопросы*:\n'
        for i, (x, y) in enumerate(zip(quiz_info['qa_pairs'], quiz_info['right_answers'])):
            message += f'{i+1}. {x[0]}\nВарианты ответов:\n•'
            message += '\n•'.join(x[1])
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

    async def _show_quizzes_to_manage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quizes = self._session.get_quizzes()

        if not quizes:
            await context.bot.answer_callback_query(
                update.callback_query.id,
                text='Нет созданных квизов',
                show_alert=True
            )
        else:
            keyboard = InlineKeyboardMarkup(
                    [[InlineKeyboardButton(
                        str(v), callback_data='manage:'+str(k)
                    )] for k,v  in quizes.items()
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

    async def _quizzes_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quizes = self._session.get_quizzes().values()

        if quizes:
            message = 'Доступные квизы:\n-' +\
                      '\n-'.join(f'{x} ({"🟩" if x.is_active else "🟥"})' for x in quizes)
        else:
            message = 'Нет созданных квизов'
        
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=message,
            reply_markup=QUIZZES_MENU_KEYBOARD
        )

    async def _edit_user_real_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        self._session.set_user_real_name(chat_id, None)

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text='Укажите, пожалуйста, Ваше ФИО'
        )

    async def _create_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id

        if update.callback_query is not None:
            self._session.cancel_quiz_creation(chat_id)
            await self._quizzes_menu(update, context)
            return

        try:
            quiz = QuizBuilder.create_quiz_from_message(update.effective_message.text)
            self._session.add_quiz(chat_id, quiz)
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
            print(exc)
            await context.bot.send_message(
                chat_id=chat_id,
                text='Ошибка при создании квиза. Попробуй еще раз.'
            )

    async def _start_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message_id: int = None):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        if message_id is None:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f'Добро пожаловать,\n{self._session.get_user_real_name(chat_id)}!',
                reply_markup=USER_KEYBOARD if user_id not in self._admins else ADMIN_KEYBOARD
            )
        else:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id = message_id,
                text=f'Добро пожаловать,\n{self._session.get_user_real_name(chat_id)}!',
                reply_markup=USER_KEYBOARD if user_id not in self._admins else ADMIN_KEYBOARD
            )

    async def _set_user_real_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_text = update.effective_message.text.strip().lower()

        if not re.match('^([а-я]+ +[а-я]+ +[а-я]+)$', message_text):
            await context.bot.send_message(
                chat_id=chat_id,
                text='Неправильный формат ФИО. Необходимо указать данные на кириллице. Попробуй еще раз.'
            )
        else:
            real_name = ' '.join(x.capitalize() for x in message_text.split() if x)
            self._session.set_user_real_name(chat_id, real_name)
            await self._start_menu(update, context)

    async def _start_user_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id

        self._session.add_user(
            chat_id,
            update.effective_user.username,
            update.effective_user.first_name,
            user_id,
            user_id in self._admins)

        await context.bot.send_message(
            chat_id=chat_id,
            text='Жду ФИО'
        )
    
    async def _show_quizzes_to_pass(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        active_quizzes = {k: v for k,v in self._session.get_quizzes().items() if v.is_active}
        if not active_quizzes:
            await context.bot.answer_callback_query(
                update.callback_query.id,
                text='Нет активных квизов',
                show_alert=True
            )
        else:
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(
                    str(active_quizzes[x]), callback_data='choose:'+str(x)
                )] for x in active_quizzes] +
                [[InlineKeyboardButton('↩️ Назад', callback_data='return:menu')]]
            )

            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text='Активные квизы:',
                reply_markup=keyboard
            )

    async def _init_user_quiz(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        quiz_id = update.callback_query.data.split(':')[1]

        if self._session.is_user_passed_quiz(chat_id, uuid.UUID(quiz_id)):
            await context.bot.answer_callback_query(
                update.callback_query.id,
                text='Ты уже проходил этот квиз',
                show_alert=True
            )
        else:
            self._session.init_user_quiz(chat_id, uuid.UUID(quiz_id))
            quiz_info = self._session.get_user_quiz_info(chat_id, uuid.UUID(quiz_id))
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

    async def _submit_quiz_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        message_id = update.effective_message.id
        callback_data = update.callback_query.data.split(':')
        quiz_id = callback_data[1]
        answer = int(callback_data[3])

        self._session.update_user_quiz_data(chat_id, uuid.UUID(quiz_id),answer)
        quiz_info = self._session.get_user_quiz_info(chat_id, uuid.UUID(quiz_id))
        if quiz_info is None:
            await context.bot.delete_message(chat_id, message_id)
            await context.bot.send_message(
            chat_id=chat_id,
            text='Спасибо за прохождения опроса! Жди результат :)'
            )
            self._session.apply_user_results(chat_id, uuid.UUID(quiz_id))
            if update.effective_user.id in self._admins:
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
        self._app.run_polling()
