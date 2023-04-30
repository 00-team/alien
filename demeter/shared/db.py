import json
from pathlib import Path


class DbDict(dict):
    def __init__(self, path: Path | str, defaults={}, load=False):
        path = Path(path).with_suffix('.json')
        self.__path__ = path

        if path.exists():
            self.__load__(defaults)
        else:
            if load:
                raise ValueError(f'{path} not found.')
            self.__save__()

    def __save__(self):
        with open(self.__path__, 'w') as f:
            json.dump(self, f)

    def __load__(self, defaults={}):
        with open(self.__path__, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError(f'invalid database file {self.__path__}')

            super().__init__({**defaults, **data})

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.__save__()

    def update(self, *a, **k):
        super().update(*a, **k)
        self.__save__()

    def pop(self, *a, **k):
        v = super().pop(*a, **k)
        self.__save__()
        return v

    def popitem(self):
        kv = super().popitem()
        self.__save__()
        return kv

    def __delitem__(self, v):
        super().__delitem__(v)
        self.__save__()

    def clear(self):
        super().clear()
        self.__save__()

    def save(self):
        self.__save__()


__all__ = [
    'DbDict'
]
