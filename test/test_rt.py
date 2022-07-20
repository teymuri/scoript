
import sys

sys.path.insert(0,"/home/amir/Work/smt/smt/")

from engine import (RuleTable, render, HForm)
from cmn import (is_simple_timesig, make_simple_timesig)
from score import (SimpleTimeSig)

if __name__=="__main__":
    ns = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50)
    W = 270
    hs = []
    for x in range(1):
        h = HForm(content=[
            Clef(pitch=choice(("g", "f")), canvas_visible=False, origin_visible=False),
            SimpleTimeSig(denom=1, canvas_visible=False,origin_visible=False),
            *[Note(domain="treble",
                     duration=choice(["q", "h", "w"]),
                     pitch=[choice(["c", "d"]), 5],
                     canvas_visible=False,
                     origin_visible=False)
              for _ in range(choice(ns))]
        ],
                      width=mm_to_pix(W),
                      x=20,
                      y=60 + x * 70,
                      canvas_visible=False,
                      origin_visible=False)
        hs.append(h)
    
    render(*hs)
