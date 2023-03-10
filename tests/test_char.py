import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)

import action_utils
from inspect import currentframe
from engine import Char

def test_char_notehead(asset):
    rest = Char("rests.1")
    action_utils.genass_or_cmp([rest], currentframe().f_code.co_name, __file__, asset)
