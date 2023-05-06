
# from gshare import DbDict
import logging
from pathlib import Path

logging.LOGS_PATH = Path(__file__).parent


# from gshare import DbDict
print(locals())
print(globals())

print('G')

logging.info('GG')

if __name__ == '__main__':
    import gshare
