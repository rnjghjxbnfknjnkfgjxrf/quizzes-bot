from core.utils import singleton
from core.db import DBTool
from core.logger import Logger


@singleton
class API:
    __slots__ = ('_db', '_user_to_quiz')

    def __init__(self, db: DBTool) -> None:
        self._db = db
        self._user_to_quiz = {}

    def init_quiz_creation(self, user_id: int) -> None:
        self._db.set_admin_busyness(user_id, True)
        Logger.log(f'Init quiz creation: {user_id}', 'info')
    
    def cancel_quiz_creation(self, user_id: int) -> None:
        self._db.set_admin_busyness(user_id, False)
        Logger.log(f'Canceled quiz creation: {user_id}', 'info')
    
    def get_admins_busyness(self, user_id: int) -> bool:
        return self._db.get_admins_busyness(user_id)

    def make_user_admin(self, user_id: int) -> None:
        self._db.make_user_admin(user_id)

    def add_user(self, user_id: int, username: int, name: str) -> None:
        self._db.add_user(user_id, username, name)

    def add_quiz(self,  quiz_data: dict) -> None:
        self._db.add_quiz(**quiz_data)

    def delete_quiz(self, quiz_id: str) -> None:
        self._db.delete_quiz(quiz_id)
        Logger.log(f'Deleted quiz: {quiz_id}', 'info')

    def toggle_quiz_activity(self, quiz_id: str) -> None:
        self._db.toggle_quiz_activity(quiz_id)
        Logger.log(f'Changed status: {quiz_id}', 'info')

    def get_all_quizzes(self) -> list[tuple]:
        return self._db.get_all_quizzes()

    def fetch_quiz(self, quiz_id: str) -> dict:
        return self._db.fetch_quiz(quiz_id)

    def get_quiz_results(self, quiz_id: str) -> list[tuple]:
        return self._db.get_quiz_results(quiz_id)

    def init_user_quiz(self, user_id: int, quiz_id: str) -> None:
        self._user_to_quiz[user_id]=  [0, [], None, self._db.fetch_quiz(quiz_id)]
        Logger.log(f'Started quiz: {user_id} ~ {quiz_id}', 'info')

    def cancel_user_quiz(self, user_id: int) -> None:
        self._user_to_quiz.pop(user_id)
        Logger.log(f'Cancelled quiz: {user_id}', 'info')

    def submit_user_results(self, user_id: int) -> None:
        user_quiz_data = self._user_to_quiz[user_id]
        self._db.submit_user_result(user_id, user_quiz_data[3]['quiz_id'], user_quiz_data[1])
        Logger.log(f'Submitted result: {user_id}', 'info')

    def restore_user_quiz_data(self, user_id: int) -> None:
        self._user_to_quiz[user_id][0] -= 1
        self._user_to_quiz[user_id][1].pop()

    def update_user_quiz_data(self, user_id: int, answer: int) -> None:
        self._user_to_quiz[user_id][0] += 1
        self._user_to_quiz[user_id][1].append(answer)
    
    def get_user_quiz_info(self, user_id: int) -> tuple | None:
        user_quiz_data = self._user_to_quiz[user_id]
        quiz_data = user_quiz_data[3]

        if user_quiz_data[0] == len(quiz_data['right_answers']):
            return None
        else:
            return next(iter(quiz_data['qa_pairs'][user_quiz_data[0]].items())), user_quiz_data[0] + 1

    def change_user_real_name(self, user_id: int, real_name: str | None) -> None:
        self._db.change_user_real_name(user_id, real_name)

    def is_user_authorized(self, user_id: int) -> bool:
        return self._db.is_user_authorized(user_id)
    
    def is_user_passed_quiz(self, user_id: int, quiz_id: str) -> bool:
        return self._db.is_user_passed_quiz(user_id, quiz_id)

    def is_user_have_real_name(self, user_id: int) -> bool:
        return self._db.get_user_real_name(user_id) is None
    
    def is_user_admin(self, user_id: int) -> bool:
        return self._db.is_user_admin(user_id)

    def get_user_real_name(self, user_id: int) -> str:
        return self._db.get_user_real_name(user_id)
    
    def get_all_users(self) -> list[tuple]:
        return self._db.get_all_users()