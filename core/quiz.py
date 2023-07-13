class Quiz:
    def __init__(self,
                 name: str,
                 qa_pairs: tuple[str,list[str]],
                 right_answers: list[int]) -> None:
        self._name = name
        self._qa_pairs = qa_pairs
        self._right_answers = right_answers
        self._is_active = False
    
    def check_answers(self, user_answers: list[int]) -> bool:
        right_answers = 0
        for user, right in zip(user_answers, self._right_answers):
            right_answers += int(user==right)
        return f'{right_answers}/{len(self._right_answers)}'

    def get_questions_number(self) -> int:
        return len(self._qa_pairs)

    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def toggle_status(self) -> None:
        self._is_active = not self._is_active
    
    def __str__(self) -> str:
        return self._name
    
    def get_chosen_question(self, question_number: int) -> list:
        return self._qa_pairs[question_number]

    def as_dict(self) -> dict:
        return {
            "name": self._name,
            "qa_pairs": self._qa_pairs,
            "right_answers": self._right_answers,
            "is_active": self.is_active
        }


class QuizBuilder:
    @staticmethod
    def create_quiz_from_message(message: str) -> Quiz:
        message_lines = message.strip().split('\n')
        if len(message_lines) < 3:
            raise QuizCreationError('Неправильные число параметров')
        
        name = message_lines[0].strip()
        questions_number = None
        try:
            questions_number = int(message_lines[1].strip())
        except ValueError:
            raise QuizCreationError('Количество вопросов должно быть представлено в виде целого числа')
        right_answers = ()
        try:
            right_answers = tuple(map(int, message_lines[2].strip().split(' ')))
        except ValueError:
            raise QuizCreationError('Правильные ответы должны быть представлены как целые числа')
        if len(right_answers) != questions_number:
            raise QuizCreationError('Неправильное число правильных ответов')

        wordings_section_begin_index = message.find('$')
        if wordings_section_begin_index != -1:
            wordings_section_end_index = message.find('$', wordings_section_begin_index + 1)
            if wordings_section_end_index == -1:
                raise QuizCreationError('Ошибка в секции формулировок вопросов(нет закрывающего "$")')
            wordings_section = message[wordings_section_begin_index+1:wordings_section_end_index]
            wordings = wordings_section.split(';')
            if len(wordings) != questions_number:
                raise QuizCreationError('Ошибка в секции формулировок вопросов(неправильное число формулировок)')
            questions = [x.strip() for x in wordings]
        else:
            questions = [f'Вопрос №{i+1}' for i in range(questions_number)]
        
        answer_options_section_begin_index = message.find('~')
        if answer_options_section_begin_index != -1:
            answers = []
            answer_options_section_end_index = message.find('~', answer_options_section_begin_index+1)
            if answer_options_section_end_index == -1:
                raise QuizCreationError('Ошибка в секции формулировок вариантов ответов(нет закрывающего "~")')
            answer_options_section = message[answer_options_section_begin_index+1:answer_options_section_end_index]
            answer_options = answer_options_section.split(';')
            if len(answer_options) != questions_number:
                raise QuizCreationError('Ошибка в секции формулировок вариантов ответов(неправильное количество вопросов)')
            for i, answer in enumerate(answer_options):
                options = [x.strip() for x in answer.split(':')]
                if len(options) != 4:
                    raise QuizCreationError(f'Ошибка в секции формулировок вариантов ответов(неправильное число формулировок для вопроса {i+1};ожидается - 4)')
                answers.append(options)
        else:
            answers = [['1', '2', '3', '4'] for _ in range(questions_number)]
        
        qa_pairs = tuple((q, a) for q,a in zip(questions, answers))

        return Quiz(name, qa_pairs, right_answers)
        

class QuizCreationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
