import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)

import action_utils
import random
from inspect import currentframe
from engine import (RuleTable, render, HForm, mm_to_px, HLineSeg)
from score import (SimpleTimeSig, Clef, Note, Barline)

def test_barline(asset):
    h = HForm(content=[
        Clef(pitch="g", canvas_visible=True, origin_visible=True),
        SimpleTimeSig(denom=1, canvas_visible=True,origin_visible=True),
        Note(domain="treble",
             duration="q",
             pitch=[random.choice(("c", "d")), 5]),
        Barline(),
        Note(domain="treble",
             duration="q",
             pitch=[random.choice(("c", "d")), 5]),
        Barline(),
        Note(domain="treble",
             duration="q",
             pitch=[random.choice(("c", "d")), 5]),
        Barline()
        # Clef(pitch="g", canvas_visible=True, origin_visible=True)
    ],
              width=mm_to_px(270),
              x=20,
              y=60,
              canvas_visible=True,
              origin_visible=True)
    action_utils.genass_or_cmp([h], currentframe().f_code.co_name, __file__, asset)
