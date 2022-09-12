"""This file contains global names which should be modifiable from
everywhere!

"""

import engine


DESIRED_STAFF_HEIGHT_IN_PX = engine.mm_to_px(engine.GOULD_STAFF_HEIGHTS_IN_MM[0])
DESIRED_STAFF_SPACE_IN_PX = engine.mm_to_px(engine.GOULD_STAFF_HEIGHTS_IN_MM[0] / 4)

CANVAS_VISIBLE = True
ORIGIN_VISIBLE = True

# We use the height of the alto clef as the reference for the height
# of the staff. Note that this name should exist in the font we are
# using. See also Chlapik page 33.
STAFF_HEIGHT_REF_GLYPH = "clefs.C"
UNDEFINED_GLYPH = ".notdef"


# This factor should be used to scale all objects globally
GLOBAL_SCALE_FACTOR = 1.0

# duration-space proportions (Gould, p. 39)
DUR_SPACE_PROP = {
    "w":7, "h": 5, "q": 3.5,
    "e": 2.5, "s": 2
}

# _LEFT_MARGIN = mm_to_px(36)
# _TOP_MARGIN = mm_to_px(56)
