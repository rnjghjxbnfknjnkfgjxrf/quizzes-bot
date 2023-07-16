from typing import Literal, Union
from datetime import datetime
from os import path, mkdir


class Logger:
    @staticmethod
    def log(
        message: str,
        log_type: Union[Literal['error'], Literal['info']]
    ):
        file_name = f'logs/{log_type}_logs.txt'
        print(message if log_type=='info' else 'New message in error logs')
        with open(file_name, 'a+') as file:
            file.write(f'|{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}| ~ {message}\n')
    
    @staticmethod
    def clear_logs(log_type: Union[Literal['error'], Literal['info']] = None):
        if log_type is None:
            open('logs/info_logs.txt', 'w').close()
            Logger.log('Logs cleared', 'info')
            open('logs/error_logs.txt', 'w').close()
            Logger.log('Logs cleared', 'error')
        else:
            open(f'logs/{log_type}_logs.txt', 'w').close()
            Logger.log('Logs cleared', log_type)
    
    @staticmethod
    def check_logs_dir_existence():
        if not path.exists('logs/'):
            mkdir('logs')