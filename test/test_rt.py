# from /home/amir/Work/Symbolic-Music-Typesetting/smt/engine.py import RuleTable
import sys

sys.path.insert(0,"/home/amir/Work/Symbolic-Music-Typesetting/smt")

from engine import (RuleTable, render, HForm)
from cmn import (is_simple_timesig, make_simple_timesig)
from score import (SimpleTimeSig)

test_rt = RuleTable(name="test rt")
test_rt.unsafeadd(make_simple_timesig,is_simple_timesig,"Making simple time sig")

if __name__ == "__main__":
    # render(HForm(content=[],
    #              ruletable=test_rt))
    timesig = SimpleTimeSig(denom=2, num=5,
                         ruletable=test_rt)
    breakpoint()
    render(timesig)
