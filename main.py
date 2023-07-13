from dotenv import dotenv_values
from core.bot import QuizBot

if __name__ == '__main__':
    env_values = dotenv_values('.env')
    token = env_values['TOKEN']
    admins = env_values['ADMINS']

    bot = QuizBot(token, tuple(map(int, admins.split(':'))))

    bot.run()
