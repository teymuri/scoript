CANVAS_VISIBLE = True
ORIGIN_VISIBLE = True

# We use the height of the alto clef as the reference for the height
# of the staff. Note that this name should exist in the font we are
# using. See also Chlapik page 33.
STAFF_HEIGHT_REFERENCE_GLYPH = "clefs.C"
UNDEFINED_GLYPH = ".notdef"

# Gould, page 483
GOULD_STAFF_HEIGHTS_IN_MM = {
    0: 9.2, 1: 7.9, 2: 7.4, 3: 7.0,
    4: 6.5, 5: 6.0, 6: 5.5, 7: 4.8,
    8: 3.7
}

# Chlapik, page 32
CHLAPIK_STAFF_SPACES_IN_MM = {
    2: 1.88, 3: 1.755, 4: 1.6,
    5: 1.532, 6: 1.4, 7: 1.19, 8: 1.02
}

# This factor should be used to scale all objects globally
GLOBAL_SCALE_FACTOR = 1.0
