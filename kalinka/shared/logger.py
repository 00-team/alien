import logging
import logging.config
from datetime import datetime
from logging import FileHandler

from .settings import BASE_DIR


class DailyRotating(FileHandler):
    def __init__(self, dirname: str):
        now = datetime.now()
        self.day = now.day
        self.path = BASE_DIR / f'logs/{dirname}'

        self.path.mkdir(parents=True, exist_ok=True)
        filename = str(self.path / (now.strftime('%m-%d') + '.log'))

        super().__init__(filename, 'a', 'utf-8')

    def emit(self, record):
        try:
            now = datetime.now()

            if now.day != self.day:
                if self.stream:
                    self.stream.close()
                    self.stream = None

                self.path.mkdir(parents=True, exist_ok=True)
                fn = (now.strftime('%m-%d') + '.log')
                self.baseFilename = str(self.path / fn)

                self.day = now.day
                if not self.delay:
                    self.stream = self._open()

            super().emit(record)

        except Exception:
            self.handleError(record)


logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'term': {
            'format': (
                '\033[32m%(asctime)s.%(msecs)03d \033[34m<%(levelname)s> '
                '\033[0m[\033[33m%(module)s\033[0m]: %(message)s'
            ),
            'datefmt': '%H:%M:%S'
        },
        'file': {
            'format': (
                '%(asctime)s.%(msecs)03d <%(levelname)s> '
                '[%(module)s]: %(message)s'
            ),
            'datefmt': '%H:%M:%S'
        },
    },
    'handlers': {
        'term': {
            'class': 'logging.StreamHandler',
            'formatter': 'term'
        },
        'root_file': {
            '()': DailyRotating,
            'formatter': 'file',
            'dirname': 'root'
        },
    },
    'root': {
        'handlers': ['term', 'root_file'],
        'level': 'INFO'
    },
})
