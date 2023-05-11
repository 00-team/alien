import json
from pathlib import Path


class DbDict(dict):
    def __init__(self, path: Path | str, defaults={}, load=False, indent=None):
        path = Path(path).with_suffix('.json')
        self.__path__ = path
        self._indent_ = indent

        if path.exists():
            self.__load__(defaults)
        else:
            if load:
                raise ValueError(f'{path} not found.')
            self.__save__()

    def __save__(self):
        with open(self.__path__, 'w') as f:
            json.dump(self, f, indent=self._indent_)

    def __load__(self, defaults={}):
        with open(self.__path__, 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError(f'invalid database file {self.__path__}')

            super().__init__({**defaults, **data})

    def __setitem__(self, *args, **kwargs):
        result = super().__setitem__(*args, **kwargs)
        self.__save__()
        return result

    def update(self, *args, **kwargs):
        result = super().update(*args, **kwargs)
        self.__save__()
        return result

    def pop(self, *args, **kwargs):
        result = super().pop(*args, **kwargs)
        self.__save__()
        return result

    def popitem(self, *args, **kwargs):
        result = super().popitem(*args, **kwargs)
        self.__save__()
        return result

    def __delitem__(self, *args, **kwargs):
        result = super().__delitem__(*args, **kwargs)
        self.__save__()
        return result

    def clear(self, *args, **kwargs):
        result = super().clear(*args, **kwargs)
        self.__save__()
        return result

    def save(self):
        self.__save__()


__all__ = [
    'DbDict'
]
