import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)

import action_utils
import random
from inspect import currentframe
from engine import HLineSeg

def test_line(asset):
    line = HLineSeg(length=10, thickness=4, x=0, y=0)
    action_utils.genass_or_cmp([line], currentframe().f_code.co_name, __file__, asset)
