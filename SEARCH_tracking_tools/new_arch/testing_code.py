import logging
import sys
import os

import SEARCH_functions as S

logging.basicConfig(format='%(message)s', level=logging.INFO)

if sys.argv>0:
	if "-v" in sys.argv:
		logging.getLogger().setLevel(logging.DEBUG)


test_filename = "S00_P0043_M0.zip"
input_directory = "C:\\Users\\kevin\\Desktop\\test_dir"
os.chdir(input_directory)


S.do_import(input_directory)