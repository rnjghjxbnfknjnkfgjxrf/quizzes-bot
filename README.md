# quizzes-bot
Telegram бот для проведения квизов.
## Установка
### MS Windows
```
python -m venv <venv_name>
.\<venv_name>\Scripts\Activate.ps1
pip install -r requirements.txt
```
### Linux
```
python3 -m venv <venv_name>
source <venv_name>/bin/activate
pip install -r requirements.txt
```
## Использование
### Первоначальная настройка
Для хранения данных о пользователях и квизах используется  PostgreSQL.
![Pucture of db schema](https://github.com/rnjghjxbnfknjnkfgjxrf/quizzes-bot/blob/main/demo-images/db_schema.png?raw=True)
Первоначальная настройка происходит посредствам запуска скрипта `gen_dot_end.py`: у пользователя будут запрошены необходимые для дальнейшей работы данные - токен бота, имя пользователя в БД, пароль пользователя в БД, адрес хоста, порт, имя БД, а также кодовая фраза (`ADMIN_KEY`) для дальнейшего получения прав администратора у бота.
### Запуск бота
```
python3 run_bot.py [--clear-logs]
```
Запуск осуществляется только из директории с ботом. 
При запуске с ключом `--clear-logs` перед запуском бота будет проведена очистка файлов с логами (как логов с информацией, так и логов с ошибками).
### Работа бота
#### Команды
* По команде `/start` бот запрашивает у пользователя ФИО. После получения корректного ответа, происходит авторизация пользователя и занесение его данных в БД. После авторизации пользователю отправляется сообщение, содержащее меню выбора действий: редактирование ФИО и выбор квиза для прохождения. Для прохождения доступны только непройденные квизы, запущенные администратором.
![Picture of regular user start menu](https://github.com/rnjghjxbnfknjnkfgjxrf/quizzes-bot/blob/main/demo-images/regular_user_start_menu.png?raw=True)
* Для получения прав администратора нужно отправить команду `/ADMIN_KEY`, где ADMIN_KEY - введённая при первоначальной настройке кодовая фраза. После этого пользователю будет представлено расширенное меню: помимо редактирования ФИО и прохождения квиза также появятся пункты "Меню квизов" и "Панель администратора". 
![Picture of admin start menu](https://github.com/rnjghjxbnfknjnkfgjxrf/quizzes-bot/blob/main/demo-images/admin_start_menu.png?raw=True)
* Для непредвиденных ситуаций предусмотрена команда, по которой бот отправляет новое сообщение со стартовым меню - `/menu`.
#### Меню квизов
Через данное меню происходит доступ ко всем инструментам, связанных с квизами - их создание, удаление, изменения статуса (активен/неактивен) получение результатов (как в виде сообщения так и xlsx документа). При создании квиза пользователю будет представлено сообщение в котором описывается формат ожидаемого сообщения, из которого будет формироваться квиз. По умолчанию после создания квизы являются неактивными.
![Picture of quizzes menu](https://github.com/rnjghjxbnfknjnkfgjxrf/quizzes-bot/blob/main/demo-images/quizzes_menu.png?raw=True)
![Picture of quiz management](https://github.com/rnjghjxbnfknjnkfgjxrf/quizzes-bot/blob/main/demo-images/manage_quiz.png?raw=True)
#### Панель администратора
Через данное меню происходит доступ к различных системной информации - просмотр списка авторизованных пользователей, просмотр логов.
![Picture of admins panel](https://github.com/rnjghjxbnfknjnkfgjxrf/quizzes-bot/blob/main/demo-images/admin_panel.png?raw=True)
#### Прохождение квиза
На данный момент во время прохождения квиза пользователю нельзя вернуться к предыдущему вопросу с целью его редактирования, а также нельзя выйти из квиза, единственный выход - решить квиз. После прохождения квиза пользователю пользователю не будут доступны результаты.
## TODO
* Использовать ORM, чтобы PostgreSQL перестал быть единственной опцией.
* Добавить возможность редактировать квизы.
* Улучшить систему создания квизов (не через одно сообщение).
* Добавить возможность менять доступность результатов пользователю. В таком случае у каждого  пользователя появиться личный кабинет, в котором будут собраны его достижения.
* Добавить ErrorHandler'ы
* (?) Использовать в квизах ReplyKeyboardMarkup вместо InlineKeyboardMarkup, поскольку в текущей ситуации слишком длинные формулировки обрезаются, а переход на другую клавиатуру повлечет за собой достаточно объемные изменения в логике программы.
