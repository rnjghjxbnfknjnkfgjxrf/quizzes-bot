import json
from uuid import uuid4
from psycopg2 import connect
from core.utils import singleton, INIT_DB_QUERY
from core.quiz_builder import QuizCreationError
from core.logger import Logger


@singleton
class DBTool:
    __slots__ = ('_connection', '_cursor')

    def __init__(self,
                 db_username: str,
                 db_password: str,
                 db_host: str,
                 db_port: str,
                 db_name: str) -> None:
        self._connection = connect(
            f'host={db_host} port={db_port} dbname={db_name} '+\
            f'user={db_username} password={db_password}'
        )
        self._cursor = self._connection.cursor()
        self._execute(INIT_DB_QUERY)
        Logger.log('DB connection created', 'info')
    
    def _execute(self, query: str, *args) -> bool:
        try:
            self._cursor.execute(query, args)
            self._connection.commit()
            return True
        except Exception as err:
            Logger.log(err, 'error')
            self._connection.rollback()
            return False

    def close_connection(self) -> None:
        self._cursor.close()
        self._connection.close()
        Logger.log('DB connection closed', 'info')

    def add_user(self,
                 user_id: int,
                 username: str,
                 name: str) -> None:
        self._execute(
            """
            INSERT INTO users (user_id, username, name)
            VALUES (%s, %s, %s);
            """, user_id, username, name
        )
    
    def is_user_authorized(self, user_id: int) -> bool:
        self._execute(
            """
            SELECT %s IN (SELECT user_id FROM users);
            """, user_id
        )
        return self._cursor.fetchone()[0]
    
    def is_user_passed_quiz(self, user_id: int, quiz_id: str) -> bool:
        self._execute(
            """
            SELECT %s IN (
                SELECT user_id
                FROM results
                WHERE user_id = %s AND quiz_id = %s
            );
            """, user_id, user_id, quiz_id
        )
        return self._cursor.fetchone()[0]

    def change_user_real_name(self, user_id: int, real_name: str | None) -> None:
        self._execute(
            """
            UPDATE users
            SET real_name = %s
            WHERE user_id = %s
            """, real_name, user_id
        )

    def get_user_real_name(self, user_id: int) -> str:
        self._execute(
            """
            SELECT real_name
            FROM users
            WHERE user_id = %s;
            """, user_id
        )
        return self._cursor.fetchone()[0]

    def add_quiz(self,
                 name: str,
                 right_answers: list[int],
                 qa_pairs: list[dict[str:list]]) -> None:
        if not self._execute(
            """
            INSERT INTO quizzes (quiz_id, name, right_answers, qa_pairs)
            VALUES (%s, %s, %s, %s);
            """, str(uuid4()), name, right_answers, json.dumps(qa_pairs)
        ):
            raise QuizCreationError('Квиз с таким именем уже существует')

    def fetch_quiz(self, quiz_id: str) -> dict:
        self._execute(
            """
            SELECT
                name, right_answers, qa_pairs, is_active
            FROM
                quizzes
            WHERE
                quiz_id = %s;
            """, quiz_id
        )
        quiz_data = self._cursor.fetchone()

        return {
            'quiz_id': quiz_id,
            'name': quiz_data[0],
            'right_answers': quiz_data[1],
            'qa_pairs': quiz_data[2],
            'is_active': quiz_data[3]
        }

    def toggle_quiz_activity(self, quiz_id: str) -> None:
        self._execute(
            """
            UPDATE quizzes
            SET is_active = NOT is_active
            WHERE quiz_id = %s;
            """, quiz_id
        )

    def delete_quiz(self, quiz_id: str) -> None:
        self._execute(
            """
            DELETE FROM quizzes
            WHERE quiz_id = %s;
            """, quiz_id
        )

    def _check_user_answers(self,
                            quiz_id: str,
                            user_answers: list[int]) -> str:
        self._execute(
            """
            SELECT right_answers
            FROM quizzes
            WHERE quiz_id = %s;
            """, quiz_id
        )
        right_answers = self._cursor.fetchone()[0]
        user_right_answers_counter = 0
        for u, r in zip(user_answers, right_answers):
            user_right_answers_counter += int(u==r)
        
        return f'{user_right_answers_counter}/{len(right_answers)}'


    def submit_user_result(self,
                          user_id: int,
                          quiz_id: str,
                          user_answers: list[int]) -> None:
        user_result = self._check_user_answers(quiz_id, user_answers)
        self._execute(
            """
            INSERT INTO results (user_id, quiz_id, result)
            VALUES (%s, %s, %s);
            """, user_id, quiz_id, user_result
        )

    def make_user_admin(self, user_id: int) -> None:
        self._execute(
            """
            INSERT INTO admins (user_id)
            VALUES (%s);
            """, user_id
        )
    
    def set_admin_busyness(self, user_id: int, is_busy: bool) -> None:
        self._execute(
            """
            UPDATE admins
            SET is_busy = %s
            WHERE user_id = %s;
            """, is_busy, user_id
        )

    def get_admins_busyness(self, user_id: int) -> bool:
        self._execute(
            """
            SELECT is_busy
            FROM admins
            WHERE user_id = %s;
            """, user_id
        )
        return self._cursor.fetchone()[0]

    def is_user_admin(self, user_id: int) -> bool:
        self._execute(
            """
            SELECT %s IN (SELECT user_id FROM admins);
            """, user_id
        )
        flag = self._cursor.fetchone()[0]
        return flag

    def get_all_users(self) -> list[tuple]:
        self._execute(
            """
            SELECT
                u.real_name, CONCAT('https://t.me/', u.username), u.user_id,
                CASE
                    WHEN a.user_id IS NOT NULL then TRUE
                    ELSE FALSE END
            FROM
                users u
            LEFT JOIN admins a
            USING(user_id);
            """
        )
        return self._cursor.fetchall()

    def get_all_quizzes(self) -> list[tuple]:
        self._execute(
            """
            SELECT quiz_id, name, is_active
            FROM quizzes; 
            """
        )
        return self._cursor.fetchall()
    
    def get_quiz_results(self, quiz_id: str) -> list[tuple]:
        self._execute(
            """
            SELECT 
                u.real_name,
                CONCAT('https://t.me/', u.username),
                r.result
            FROM
                results r
            JOIN
                users u
            USING(user_id)
            WHERE
                quiz_id = %s
            ORDER BY CAST(split_part(r.result, '/', 1) AS INTEGER) DESC;
            """, quiz_id
        )
        return self._cursor.fetchall()
