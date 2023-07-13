import uuid
from core.user import User
from core.quiz import Quiz
from core.utils import singleton, log


@singleton
class BotSession:
    def __init__(self) -> None:
        log('Session started')
        self._users = {}
        self._quizzes = {}
        self._user_to_quiz = {}
        self._admins_busyness = {}

    def init_quiz_creation(self, chat_id: int) -> None:
        self._admins_busyness[chat_id] = True
        log(f'Init quiz creation: {self._users[chat_id]}')
    
    def cancel_quiz_creation(self, chat_id: int) -> None:
        self._admins_busyness[chat_id] = False
        log(f'Canceled quiz creation: {self._users[chat_id]}')
    
    def get_admins_busyness(self, chat_id: int) -> bool:
        return self._admins_busyness[chat_id]

    def add_user(self, chat_id: int, user_name: int, name: str, user_id: int, is_admin: bool = False) -> None:
        self._users[chat_id] = User(user_name, name, user_id)
        if is_admin:
            self._admins_busyness[chat_id] = False
        self._user_to_quiz[chat_id] = {}
        log(f'Added user: {self._users[chat_id]}')
    
    def get_user(self, chat_id: int) -> User:
        return self._users[chat_id]

    def add_quiz(self, chat_id:int, quiz: Quiz) -> None:
        self._quizzes[uuid.uuid4()] = quiz
        self._admins_busyness[chat_id] = False
        log(f'Ended quiz creation: {self._users[chat_id]}')
        log(f'Added quiz: {quiz}')

    def delete_quiz(self, chat_id: int, quiz_id: uuid.UUID) -> None:
        quiz = self._quizzes.pop(quiz_id)
        self._user_to_quiz = {k:v for k,v in self._user_to_quiz.items() if v!=quiz}
        log(f'Deleted quiz: {self._users[chat_id]} ~ {quiz}')

    def toggle_quiz_status(self, chat_id: int, quiz_id: uuid.UUID) -> None:
        quiz = self._quizzes[quiz_id]
        quiz.toggle_status()
        log(f'Changed status: {self._users[chat_id]} ~ {quiz}')

    def get_quizzes(self) -> dict:
        return self._quizzes

    def get_quiz(self, quiz_id: int) -> Quiz:
        return self._quizzes[quiz_id]

    def get_quiz_results(self, quiz_id: uuid.UUID) -> list[tuple]:
        results = []
        for chat_id, user_result in self._user_to_quiz.items():
            if quiz_id in user_result:
                results.append((self._users[chat_id], user_result[quiz_id][2]))
        return results

    def init_user_quiz(self, chat_id: int, quiz_id: uuid.UUID) -> None:
        self._user_to_quiz[chat_id][quiz_id] =  [0, [], None]
        log(f'Started quiz: {self._users[chat_id]} ~ {self._quizzes[quiz_id]}')

    def apply_user_results(self, chat_id: int, quiz_id: uuid.UUID) -> None:
        user_quiz_data = self._user_to_quiz[chat_id][quiz_id]
        user_quiz_data[2] = self._quizzes[quiz_id].check_answers(user_quiz_data[1])
        log(f'Submitted result: {self._users[chat_id]} - res: {user_quiz_data[2]}')

    def update_user_quiz_data(self, chat_id: int, quiz_id: uuid.UUID, answer: int) -> None:
        self._user_to_quiz[chat_id][quiz_id][0] += 1
        self._user_to_quiz[chat_id][quiz_id][1].append(answer)
    
    def get_user_quiz_info(self, chat_id: int, quiz_id: uuid.UUID):
        quiz = self._quizzes[quiz_id]
        user_quiz_data = self._user_to_quiz[chat_id][quiz_id]
        
        return quiz.get_chosen_question(user_quiz_data[0]) if not \
               len(user_quiz_data[1]) == quiz.get_questions_number() else None

    def set_user_real_name(self, chat_id: int, real_name: str | None) -> None:
        self._users[chat_id].real_name = real_name
        if real_name is not None:
            log(f'Modified user: {self._users[chat_id]}')

    def is_user_authorized(self, chat_id: int) -> bool:
        return chat_id in self._users
    
    def is_user_passed_quiz(self, chat_id: int, quiz_id: uuid.UUID) -> bool:
        return quiz_id in self._user_to_quiz[chat_id]

    def is_user_have_real_name(self, chat_id: int) -> bool:
        return self._users[chat_id].real_name is None
    
    def get_users(self) -> dict:
        return self._users

    def get_user_real_name(self, chat_id: int) -> str:
        return self._users[chat_id].real_name