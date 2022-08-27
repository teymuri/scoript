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


def test_hform_list_with_diff_durs(asset):
    W = 270
    hs = []
    dur_list = (("q", "w", "q", "h", "h", "w", "q", "q", "q", "w", "h"),
                ("h", "h", "h", "w", "q", "h", "q", "q", "q", "w", "w", "h", "q"),
                ("q", "q", "q", "q", "q", "h", "q", "w", "h", "h"),
                ("q", "w", "w", "w", "h", "h", "h", "h", "q", "q", "q", "q", "q", "q"),
                ("h", "h", "w"),
                ("w", "w"),
                ("q", "q", "h", "h", "h", "h", "w", "q", "q"),
                ("h", "h", "h", "h", "w", "h", "h", "h", "h", "w", "w", "w", "h", "q", "h", "h", "h"),
                ("h", "h", "h", "h"))
    pitches = ("c", "d")
    for i, durs in enumerate(dur_list):
        h = HForm(content=[
            Clef(pitch="g", canvas_visible=True, origin_visible=True),
            SimpleTimeSig(denom=1, canvas_visible=True,origin_visible=True),
            *[Note(domain="treble",
                   duration=dur,
                   pitch=[pitches[j % len(pitches)], 5],
                   canvas_visible=True,
                   origin_visible=True)
              for j, dur in enumerate(durs)]
        ],
                      width=mm_to_px(W),
                      x=20,
                      y=60 + i * 70,
                      canvas_visible=True,
                      origin_visible=True)
        hs.append(h)
    action_utils.genass_or_cmp(hs, currentframe().f_code.co_name, __file__, asset)

def test_twelve_hform_list(asset):
    W = 270
    hs = []
    durs = ("q", "h", "w")
    for i, dur in enumerate(durs):
        h = HForm(content=[
            Clef(pitch="g", canvas_visible=True, origin_visible=True),
            SimpleTimeSig(denom=1, canvas_visible=True,origin_visible=True),
            *[Note(domain="treble",
                     duration=dur,
                     pitch=[p, 4],
                     canvas_visible=True,
                     origin_visible=True)
              for p in ("c", "d", "e", "f", "g", "a", "b")]
        ],
                      width=mm_to_px(W),
                      x=20,
                      y=60 + i * 120,
                      canvas_visible=True,
                      origin_visible=True)
        hs.append(h)
    action_utils.genass_or_cmp(hs, currentframe().f_code.co_name, __file__, asset)

def test_only_valued_objs(asset):
    W = 270
    hs = []
    dur_list = (("q", "w", "q", "h", "h", "w", "q", "q", "q", "w", "h"),
                ("h", "h", "h", "w", "q", "h", "q", "q", "q", "w", "w", "h", "q"),
                ("q", "q", "q", "q", "q", "h", "q", "w", "h", "h"),
                ("q", "w", "w", "w", "h", "h", "h", "h", "q", "q", "q", "q", "q", "q"),
                ("h", "h", "w"),
                ("w", "w"),
                ("q", "q", "h", "h", "h", "h", "w", "q", "q"),
                ("h", "h", "h", "h", "w", "h", "h", "h", "h", "w", "w", "w", "h", "q", "h", "h", "h"),
                ("h", "h", "h", "h"))
    pitches = ("c", "d")
    for i, durs in enumerate(dur_list):
        h = HForm(content=[
            Clef(pitch="g", canvas_visible=True, origin_visible=True),
            SimpleTimeSig(denom=1, canvas_visible=True,origin_visible=True),
            *[Note(domain="treble",
                   duration=dur,
                   pitch=[pitches[j % len(pitches)], 5],
                   canvas_visible=True,
                   origin_visible=True)
              for j, dur in enumerate(durs)]
        ],
                      width=mm_to_px(W),
                      x=20,
                      y=60 + i * 70,
                      canvas_visible=True,
                      origin_visible=True)
        hs.append(h)
    action_utils.genass_or_cmp(hs, currentframe().f_code.co_name, __file__, asset)

