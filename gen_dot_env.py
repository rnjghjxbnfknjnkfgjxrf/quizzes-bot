#Скрипт для генерации .env файла.
from re import search
from os import path


def main():
    token = input('Введите токен бота: ')

    username = input('Введите имя пользователя БД (enter для "postgres"): ')
    if not username:
        username = 'postgres'

    password = input('Введите пароль пользователя БД (enter для "postgres"): ')
    if not password:
        password = 'postgres'

    host = input('Введите адрес хоста (enter для "localhost"): ')
    if not host:
        host = 'localhost'

    while True:
        port = input('Введите порт (enter для 5432): ')
        if not port:
            port = 5432
            break
        try:
            port = int(port)
            break
        except ValueError:
            print('Неправильный формат порта. Попробуйте еще раз. ')

    db_name = input('Введите название БД: ')
    while True:
        admin_key = input(
            'Введите кодовую фразу (без пробельных символов)'+\
            ', для получения прав администратора у бота: '
        )
        if search('\s', admin_key):
            print('Кодовая фраза не должна содержать пробельные символы.')
        else:
            break
    
    with open('.env', 'w') as f:
        f.write(
            f'TOKEN="{token}"\n'+\
            f'DB_USERNAME="{username}"\n'+\
            f'DB_PASSWORD="{password}"\n'+\
            f'DB_HOST="{host}"\n'+\
            f'DB_PORT="{port}"\n'+\
            f'DB_NAME="{db_name}"\n'+\
            f'ADMIN_KEY="{admin_key}"\n'
        )
    print('Конфигурационный файл успешно сгенерирован.')

if __name__ == '__main__':
    if path.exists('.env'):
        while True:
            try:
                answer = input(
                    'Конфигурационный файл уже существует.'+\
                    '\nПосле запуска скрипта файла будет перезаписан.'+\
                    '\nПродолжить? (y/n) '
                    ).strip().lower()
                if answer not in 'yn':
                    raise ValueError
                elif answer == 'y':
                    main()
                    break
                else:
                    break
            except ValueError:
                print('Неправильный формат ответа. Ожидается "y" или "n".')
    else:
        main()