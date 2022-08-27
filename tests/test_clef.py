import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)

import action_utils
from random import choice
from inspect import currentframe
from engine import (RuleTable, render, HForm, mm_to_px)
from rules.cmn import (is_simple_timesig, make_simple_timesig)
from score import (SimpleTimeSig, Clef, Note)

def test_clef_width(asset):
    render(Clef(pitch="g"), path="/tmp/clef.svg")
