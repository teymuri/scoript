import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)
from random import choice
from engine import (RuleTable, render, HForm, mm_to_pix)
from rules.cmn import (is_simple_timesig, make_simple_timesig)
from score import (SimpleTimeSig, Clef, Note)

if __name__=="__main__":
    ns = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50)
    durs = ("q", "q", "h", "w", "q", "h", "q", "w", "w", "q", "q", "q", "q")
    W = 270
    hs = []
    for x in range(2):
        h = HForm(content=[
            Clef(pitch=choice(("g", "f")), canvas_visible=False, origin_visible=False),
            SimpleTimeSig(denom=1, canvas_visible=False,origin_visible=False),
            *[Note(domain="treble",
                     duration=dur,
                     pitch=[choice(["c", "d", "b", "a","x"]), 5],
                     canvas_visible=False,
                     origin_visible=False)
              for dur in durs]
        ],
                      width=mm_to_pix(W),
                      x=20,
                      y=60 + x * 70,
                      canvas_visible=False,
                      origin_visible=False)
        hs.append(h)
    
    render(*hs)
