import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)

import action_utils
from inspect import currentframe
from engine import (MChar, SForm, HForm, render)

def test_char_dim():
    char = MChar(name="noteheads.s0")
    sform = SForm(canvas_opacity=1)
    
    print(sform._abstract_staff_height_bottom, sform.top, sform._abstract_staff_height,
          char.bottom, char.top,
          char._bbox(),
          sform.canvas_color, sform.canvas_visible, sform.canvas_opacity)
    char.y = sform._abstract_staff_height_bottom
    h=HForm(content=[])
    h.width = 10
    sform.width = 20
    print(h.canvas_color, h.canvas_opacity, h.canvas_visible,
          h._abstract_staff_height_bottom, h._abstract_staff_height_top, h._abstract_staff_height, h.width)
    render(sform, path="/tmp/amir.svg")
