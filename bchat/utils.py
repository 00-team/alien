
import sys

from gshare import DbDict

config = DbDict(sys.argv[1], load=True, indent=2)
