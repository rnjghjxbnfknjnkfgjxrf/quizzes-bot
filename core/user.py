class User:
    def __init__(self, username: str, name: str,id: int) -> None:
        self.username = username
        self._name = name
        self._real_name = None
        self._id  = id
    
    @property
    def real_name(self) -> str | None:
        return self._real_name

    @real_name.setter
    def real_name(self, real_name: str | None) -> None:
        self._real_name = real_name

    @property
    def username(self) -> str:
        return self._username
    
    @username.setter
    def username(self, username: str) -> None:
        self._username = username

    def __repr__(self) -> str:
        return f'{self._id} - {self._username} - {self._name} - ' + \
               f'ФИО: {self._real_name} '