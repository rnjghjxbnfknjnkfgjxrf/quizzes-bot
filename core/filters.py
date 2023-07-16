from telegram.ext.filters import UpdateFilter, MessageFilter


class StartFilter(UpdateFilter):
    def __init__(self, bot_session):
        super().__init__()
        self._session = bot_session

    def filter(self, update):
        return not self._session.is_user_authorized(update.effective_chat.id)


class RealNameFilter(MessageFilter):
    def __init__(self, bot_session):
        super().__init__()
        self._session = bot_session

    def filter(self, message):
        return self._session.is_user_have_real_name(message.from_user.id)


class AdminFilter(MessageFilter):
    def __init__(self, bot_session):
        super().__init__()
        self._session = bot_session
    
    def filter(self, message):
        return self._session.is_user_admin(message.from_user.id)


class QuizCreationFilter(MessageFilter):
    def __init__(self, bot_session):
        super().__init__()
        self._session = bot_session

    def filter(self, message):
        return self._session.get_admins_busyness(message.from_user.id)
