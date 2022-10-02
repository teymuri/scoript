import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)

import random
import cfg
from core import (RuleTable, render, HForm, mm_to_px, HLine,
                    Char, CMN, VLine, _SimplePointedCurve,
                    find_glyphs, SForm)
from score import (SimpleTimeSig, Clef, Note, Barline, StaffLines, KeySig, Accidental, Staff, Stem, FinalBarline, _Clock, is_last_barline_on_staff,
                   SlurOpen, SlurClose, Rest, MultiStaff)
from random import randint, choice
import score as S
import copy 


# cfg.CANVAS_VISIBLE = cfg.ORIGIN_VISIBLE = False

def pass_on_width(multistaff):
    """passing on multistaff's width to staves..."""
    for child in multistaff.content:
        child.width = multistaff.width
        child._width_locked=1

def _treble_pitch_offset_from_staff_bottom(obj):
    return obj.current_ref_glyph_bottom() + {
        "c": 1, "d": 0.5, "e": 0, "f": -0.5,
        "g": -1, "a": -1.5, "b": -2
    }[obj.pitch.name] * cfg.DESIRED_STAFF_SPACE_IN_PX

def _bass_pitch_offset_from_staff_bottom(obj):
    return obj.current_ref_glyph_bottom() + {
        "b": -1,
        "a": -.5, "g": 0, "f": 0.5, "e": 1, "d": 1.5, "c": 2
    }[obj.pitch.name] * cfg.DESIRED_STAFF_SPACE_IN_PX
    
def _pitch_vertical_pos(obj):
    """The pitch object is a note or an accidental. NOTE: all must
    be forms, probabely sform is more suitable for single chars, since
    we need the object's abstract staff info.

    note_obj is a stacked form; it's _abstract_staff_height_bottom
    is the bottom of a clefs.C (i.e. bottom edge of the chosen stave
    height). To find the vertical position of the notehead I set it's
    y (which is originally placed in the middle of the clefs.C
    i.e. the middle stave line) to be the bottom edge of the SForm
    (_abstract_staff_height_bottom) + 1 stave space to get C4, half
    stave space to get D4, 0 stave spaces to get the E4, half stave
    space towards top of page to get F4 (-0.5 * cfg.DESIRED_STAFF_SPACE_IN_PX, topwards
    our y coordinate is moving negative, downwards positive) etc. The
    rest is to replace the result of aforementioned calculations by a
    certian amount (offset_by_oct below) to transpose to other
    octaves.

    """
    pitch_name = obj.pitch.name
    octave = obj.pitch.octave
    if obj.domain == "treble":
        pos_on_staff = _treble_pitch_offset_from_staff_bottom(obj)
        ref_oct = 4
    elif obj.domain == "bass":
        pos_on_staff = _bass_pitch_offset_from_staff_bottom(obj)
        ref_oct = 2
    # breakpoint()
    offset_by_oct = (ref_oct - octave) * (7/8 * obj._abstract_staff_height)
    y = pos_on_staff + offset_by_oct
    return y

def is_simple_timesig(x): return isinstance(x, SimpleTimeSig)
def set_simple_timesig_chars(ts):
    """this is the ultimate, the one and the only guy putting
    together and punching time sigs"""
    ts.num_char=Char({3: "three", 4:"four", 5:"five"}.get(ts.num, ".notdef"),
                           canvas_visible=False,
                           origin_visible=False)
    ts.denom_char=Char({4: "four", 2:"two", 1: "one"}.get(ts.denom, ".notdef"),
                             canvas_visible=False,
                             origin_visible=False)
    # I'm shifting the 1 here because I know the font's properties?
    if ts.denom == 1:
        d=ts.denom_char.parent().width - ts.denom_char.width
        ts.denom_char.right = ts.denom_char.parent().right
        
def is_keysig(obj): return isinstance(obj, KeySig)

def set_keysig_char_list(keysig):
    dom = keysig.domain
    char_list = []
    if keysig.scale in ("amaj", "f#min"): # f# c# g# problem war dass
        f_sharp = Accidental(pitch=("f", 5, "#"), )
        c_sharp = Accidental(pitch=("c", 5, "#"), )
        g_sharp = Accidental(pitch=("g", 5, "#"), )
        char_list.extend([f_sharp, c_sharp, g_sharp])
    elif keysig.scale in ["dmaj"]:
        if dom == "treble":
            # octave
            o = 5
        elif dom == "bass":
            o = 3
        char_list.append(Accidental(pitch=("f", o, "#")))
        char_list.append(Accidental(pitch=("c", o, "#")))
    keysig.char_list = char_list


    
def is_accidental(obj):
    return isinstance(obj, Accidental)

def set_accidental_char(obj):
    name = {"#": "accidentals.sharp"}.get(obj.pitch.suffix,
                                          cfg.UNDEFINED_GLYPH)
    char = Char(name=name)
    obj.char = char
    obj.char.y = _pitch_vertical_pos(obj)

def is_note(x):
    return isinstance(x, Note)

# Setting noteheads
def set_notehead_char(obj):
    """setting notehead chars & vertical positioning..."""
    obj.head_char = Char(name={
        "w": "noteheads.s0",
        "h": "noteheads.s1",
        "q": "noteheads.s2",
        "e": "noteheads.s2"
    }[obj.dur],
                         canvas_visible=False,
                         origin_visible=False)
    obj.head_char.y = _pitch_vertical_pos(obj)

def is_rest(obj):
    return isinstance(obj, Rest)

def set_rest_char(obj):
    """setting rest chars..."""
    obj.char = Char(name={
        "h": "rests.1"
    }[obj.dur])
    obj.char.y = obj.current_ref_glyph_top() + cfg.DESIRED_STAFF_HEIGHT_IN_PX / 2

def isstem(o): return isinstance(o, S.Stem)
def set_stem_line(note):
    if note.dur in ("q", "h"): # needs stem
        stem = Stem(x=note.x+.7,
                    y=note.head_char.y,
                    )
        note.stem_graver = stem

def has_slur_close(obj):
    return isinstance(obj, Note) and isinstance(obj.slur, SlurClose)

# slures are applied at last wenn alle Noten in richtiger Pos sind,
# as last rule
def set_slur(obj):              # obj = Note with closing slur point
    """setting slures..."""
    close_slur = obj.slur
    open_slur = SlurOpen.get_by_id(close_slur.id)
    open_note = open_slur.owner
    mitte = (obj.head_char.right - open_note.head_char.left) / 2
    cx = open_note.x + mitte
    cy = open_note.head_char.top - 50
    curve = _SimplePointedCurve(
        start_x=open_note.head_char.x + open_note.head_char.width / 2,
        start_y=open_note.head_char.top - cfg.DESIRED_STAFF_SPACE_IN_PX / 2,
        control_x=cx, # ctrl_x
        control_y=cy,
        end_x=obj.head_char.x + obj.head_char.width / 2,
        end_y=obj.head_char.top - cfg.DESIRED_STAFF_SPACE_IN_PX / 2,
        end_square_diagonal=1.7,
        thickness=4,
        rotation=0
    )
    open_note.root().extend_content(curve)
    # open_note.slur = curve

def make_accidental_char(accobj):
    if not accobj.punch:
        accobj.punch = S.E.Char(name="accidentals.sharp", canvas_visible=False,
                                origin_visible=False)

def set_clef_char(clefobj):
    clefobj.char = Char(
        name={"g":"clefs.G","f":"clefs.F"}[clefobj.pitch.name])
    if clefobj.pitch.name == "g":
        clefobj.char.y = clefobj.current_ref_glyph_bottom() - cfg.DESIRED_STAFF_SPACE_IN_PX
    elif clefobj.pitch.name == "f":
        clefobj.char.y = clefobj.current_ref_glyph_top() + cfg.DESIRED_STAFF_SPACE_IN_PX



############################# punctuation

def find_ref_dur(dur_counts):
    """Returns the dur name with the largest number of occurrences.
    """
    return list(sorted(dur_counts, key=lambda lst: lst[0]))[0][1]

def _dur_ref_ratio(dur, ref_dur):
    """Returns the ratio of the dur's space proportion to
    the reference dur's space proportion.
    """
    return cfg.DUR_SPACE_PROPS[dur] / cfg.DUR_SPACE_PROPS[ref_dur]
    
def compute_perf_punct(clocks, w):
    # notes=list(filter(lambda x:isinstance(x, Note), clocks))
    durs=list(map(lambda x:x.dur, clocks))
    dur_counts = []
    for d in set(durs):
        # dur_counts[durs.count(d)] =d
        # dur_counts[d] =durs.count(d)
        dur_counts.append((durs.count(d), d))
    udur = find_ref_dur(dur_counts)
    uw=w / sum([x[0] * _dur_ref_ratio(x[1],udur) for x in dur_counts])
    perfwidths = []
    for x in clocks:
        # a space is excluding the own width of the clock (it's own char width)
        space = ((uw * _dur_ref_ratio(x.dur, udur)) - x.width)
        perfwidths.append(space)
        # x.width += ((uw * _dur_ref_ratio(udur, x.dur)) - x.width)
    return perfwidths

def right_guard(obj):
    return {S.Note: 2, S.Clef:0,
            S.Accidental: 2,
            S.SimpleTimeSig: 0}[type(obj)]

NON_CLOCK_RIGHT_PADDING = {
    KeySig: cfg.DESIRED_STAFF_SPACE_IN_PX,
    Accidental: cfg.DESIRED_STAFF_SPACE_IN_PX,
    Clef: cfg.DESIRED_STAFF_SPACE_IN_PX,
    # one space for the barline (Ross, p. 74)
    Barline: cfg.DESIRED_STAFF_SPACE_IN_PX,
    SimpleTimeSig: cfg.DESIRED_STAFF_SPACE_IN_PX
}

def first_clock_idx(l):
    for i,x in enumerate(l):
        if isinstance(x, S.Clock):
            return i

def _map_durs_to_count(clocks_list):
    durs_list = [obj.dur for obj in clocks_list]
    return {dur: durs_list.count(dur) for dur in set(durs_list)}

# Note that durations MUST BE strings!
def _find_ref_dur(durs_to_count):
    """Returns the dur with the heighest number of occurrences."""
    return max(durs_to_count, key=durs_to_count.get)

def get_non_clocked_space(staff, right_padding_dict):
    """Returns the sum of space """
    objs = _Clock.get_non_time_objs(staff)
    space = 0
    for x in objs:
        space += x.width
        if not is_last_barline_on_staff(x):
            space += right_padding_dict.get(type(x), 0)
    return space

def get_clocked_space_and_padding(staff, right_padding_dict):
    """Returns a list"""
    while True:
        # get sum of all non-time objects width of the staff
        non_clocked_space = get_non_clocked_space(staff, right_padding_dict)
        # get the remaining space for valued objs
        time_objs_space = staff.width - non_clocked_space
        # compute ideal widths for objs with durations (notes and rests and chords)
        clocks = _Clock.get_clock_objs(staff)
        if not clocks:
            return ([], right_padding_dict)
        durs_to_count = _map_durs_to_count(clocks)
        ref_dur = _find_ref_dur(durs_to_count)
        # Wieviele ref_durs konnten wir insgesamt haben?
        ref_dur_count = sum([v * _dur_ref_ratio(k, ref_dur) for k, v in durs_to_count.items()])
        # ideal width for the reference dur
        # See Ross page 73
        unit_of_space = time_objs_space / ref_dur_count
        shortest_time_obj = _Clock.shortest(clocks)
        shortest_time_obj_width = None
        clock_space_list = []
        for obj in clocks:
            space = unit_of_space * _dur_ref_ratio(obj.dur, ref_dur) - obj.width
            clock_space_list.append(space)
            if obj is shortest_time_obj:
                shortest_time_obj_width = space
        # momentan nehme ich an right paddding ist immer 1 staff space...
        if shortest_time_obj_width >= right_padding_dict[sorted(right_padding_dict, key=right_padding_dict.get)[0]]:
            return (clock_space_list, right_padding_dict)
        else:
            # zieh 1 pixel ab
            right_padding_dict = {objtype: padding - 1 for objtype, padding in right_padding_dict.items()}

def is_only_clock_in_bar(x):
    return isinstance(x, _Clock) and \
           isinstance(x.older_sibling(), Barline) and \
           isinstance(x.younger_sibling(), (Barline, FinalBarline))
def center_only_clock_in_bar(obj):
    """centering only clocks in bar..."""
    bar_half_width = (obj.width + obj.older_sibling().width - obj.older_sibling().char.width) / 2
    center = obj.older_sibling().char.right + bar_half_width - obj.head_char.width / 2
    obj.head_char.left = center

# Nothing should be added to the notes after this stage which would
# change it's dimensions
def horizontal_spacing(staff):
    """horizontal spacing..."""
    clock_space_list, right_padding_dict = get_clocked_space_and_padding(staff, NON_CLOCK_RIGHT_PADDING)
    # braucht nicht das if, else reicht
    if staff.is_clocks_only():
        for obj, width in zip(staff.content, clock_space_list):
            obj.width += width
            # obj._width_locked = True
    else:
        time_obj_idx = 0
        for obj in staff.content:
            if isinstance(obj, _Clock):
                obj.width += clock_space_list[time_obj_idx]
                obj._width_locked = 1
                time_obj_idx += 1
            else:
                # A barline at the end of the staff doesn't need it's
                # right margin.
                if not (isinstance(obj, (FinalBarline, Barline)) and obj.is_last_child()) and not isinstance(obj, _SimplePointedCurve):
                    obj.width += right_padding_dict.get(type(obj), 0)



def greenhead(x): x.head_char.color = e.svgwrite.utils.rgb(0,0,100,"%")
def reden(x): 
    print(x.id, x.content)
    x.content[0].color = e.svgwrite.utils.rgb(100,0,0,"%")
def Sid(x): return x.id == "S"
def isline(x): return isinstance(x, (System, S.E.HForm))
def ish(x): return isinstance(x, e.HForm)
def isclef(x): return isinstance(x, S.Clef)
def opachead(n): n.head_char.opacity = .3


def setbm(l):
    o=[x for x in l.content if isnote(x) and x.dur in ("q","h")] #note mit openbeam
    # c=[x for x in l.content if isnote(x) and x.close_beam][0]
    # d=c.stem_graver.right -o.stem_graver.left
    for a in o:
        a.obeam_graver = S.E.HLine(length=a.width,thickness=5,
        x=a.left,
        y=a.stem_graver.bottom,
        # rotate=45,
        )
    # o.append(S.E.HLine(length=o.width,thickness=5,x=o.left, y=o.stem_graver.bottom))
    # c.append(S.E.HLine(length=o.width,thickness=5,x=o.left, y=o.stem_graver.bottom))





def skew(stave):
    print(stave.skewx)
    stave.skewx = 50
    print(stave.skewx)
def ishline(x): return isinstance(x,S.E.HLine)
def is_barline(x): return isinstance(x, Barline)

def set_barline_char(obj):
    """setting barline char..."""
    # obj is a barline object
    obj.char = VLine(length=obj._abstract_staff_height + StaffLines.THICKNESS,
                        thickness=Barline.THICKNESS + 1,
                        y=obj.current_ref_glyph_top() - StaffLines.THICKNESS * .5,
                        # a barline is normally used right after a note or a rest
                        x=obj.older_sibling().right if obj.older_sibling() else obj.parent().x,
                        canvas_opacity=0.1,
                    )

def is_final_barline(obj):
    return isinstance(obj, FinalBarline)

def place_final_barline(obj):
    obj.thin.y = obj.current_ref_glyph_top() - StaffLines.THICKNESS * .5
    obj.thick.y = obj.current_ref_glyph_top() - StaffLines.THICKNESS * .5

    
# S.E.CMN.add(skew, isline, "SKEW stave")
# S.E.CMN.unsafeadd(skew, isline, "SKEW stave")

def flag(note):
    if note.dur != 1:
        # print(note.stem_graver.y)
        note.extend_content(S.E.Char(name="flags.d4",y=note.stem_graver.bottom,x=note.x+.5,
        origin_visible=1))

# def bm(n):
    # if n.stem_graver:
        # n.stem_graver.length -= 10
        # n.extend_content(S.E.HLine(length=10, thickness=5, y=n.stem_graver.bottom, skewy=-0, endxr=1,endyr=.5))


# S.E.CMN.add(bm, isnote, "beams")



# Rules adding
"""
hook mehrmals überall, 
test
"""
CMN.unsafeadd(pass_on_width, lambda x: isinstance(x, MultiStaff))
# The single argument to rule hooks are every objects defined in your
# score.
CMN.unsafeadd(set_simple_timesig_chars,
              is_simple_timesig)

CMN.unsafeadd(set_notehead_char, is_note)
CMN.unsafeadd(set_rest_char, is_rest)

CMN.unsafeadd(set_keysig_char_list, is_keysig)

CMN.unsafeadd(set_accidental_char,
              is_accidental)


CMN.unsafeadd(set_stem_line, is_note)

CMN.unsafeadd(set_clef_char, isclef)

CMN.unsafeadd(set_barline_char,
              lambda obj: is_barline(obj))

CMN.unsafeadd(place_final_barline,
              is_final_barline)

CMN.unsafeadd(horizontal_spacing,
              lambda x: isinstance(x, Staff))

CMN.unsafeadd(center_only_clock_in_bar, is_only_clock_in_bar)

CMN.unsafeadd(StaffLines.make,
              lambda obj: is_note(obj) or \
              isinstance(obj, SForm) and obj.get_idx() == 0 or \
              is_rest(obj) or \
              isclef(obj) or \
              is_simple_timesig(obj) or \
              is_accidental(obj) or \
              is_keysig(obj) or \
              is_barline(obj) and not obj.is_last_child() or \
              is_final_barline(obj))

CMN.unsafeadd(set_slur, has_slur_close)

if __name__ == "__main__":
    # a = Accidental(pitch=("f", 5, "#"))
    # accs = [
    #     Accidental(pitch=("f", 5, "#")),
    #     Accidental(pitch=("e", 5, "#")),
    #     Accidental(pitch=("d", 5, "#")),
    #     Accidental(pitch=("c", 5, "#")),
    #     Accidental(pitch=("b", 4, "#")),
    #     Accidental(pitch=("a", 4, "#")),
    #     Accidental(pitch=("g", 4, "#")),
    #     Accidental(pitch=("f", 4, "#")),
    #     Accidental(pitch=("g", 4, "#")),
    #     Accidental(pitch=("a", 4, "#")),
    #     Accidental(pitch=("b", 4, "#")),
    #     Accidental(pitch=("c", 5, "#")),
    #     Accidental(pitch=("d", 5, "#")),
    #     Accidental(pitch=("e", 5, "#")),
    # ]
    # # accs += list(reversed(accs))
    # # breakpoint()
    
    # h = Staff(content=[
    #     Clef(pitch="treble", canvas_visible=False, origin_visible=False),
    #     KeySig("amaj"),
    #     # KeySig("", content=accs),
    #     SimpleTimeSig(denom=4, canvas_visible=False, origin_visible=False),
    #     # a,
    #     Note(domain="treble",
    #          dur="q",
    #          pitch=["f", 5]),
    #     # Accidental(pitch=("f", 5, "#")),
    #     Note(domain="treble",
    #          dur="q",
    #          pitch=["f", 5]),
    #     # Accidental(pitch=("f", 5, "#")),
    #     Note(domain="treble",
    #          dur="q",
    #          pitch=["f", 5]),
    #     # Accidental(pitch=("g", 5, "#")),
    #     Note(domain="treble",
    #          dur="q",
    #          pitch=["g", 5]),
    #     Barline(),
    #     # Accidental(pitch=("a", 5, "#")),
    #     Note(domain="treble",
    #          dur="h",
    #          pitch=["a", 5]),
    #     # Accidental(pitch=("g", 5, "#")),
    #     Note(domain="treble",
    #          dur="h",
    #          pitch=["g", 5]),
    #     Barline(),
    #     # Accidental(pitch=("f", 5, "#")),
    #     Note(domain="treble",
    #          dur="q",
    #          pitch=["f", 5]),
    #     # Accidental(pitch=("a", 5, "#")),
    #     Note(domain="treble",
    #          dur="q",
    #          pitch=["a", 5]),
    #     # Accidental(pitch=("g", 5, "#")),
    #     Note(domain="treble",
    #          dur="q",
    #          pitch=["g", 5]),
    #     # Accidental(pitch=("g", 5, "#")),
    #     Note(domain="treble",
    #          dur="q",
    #          pitch=["g", 5]),
    #     Barline(),
    #     # Accidental(pitch=("c", 5, "#")),
    #     Note(domain="treble",
    #          dur="w",
    #          pitch=["f", 5]),
    #     Barline()
    # ],
    #           width=mm_to_px(270),
    #           x=20,
    #           y=60,
    #           canvas_visible=True,
    #           origin_visible=True)
    def _keysig(): return KeySig(scale="dmaj", domain="bass")
    def _clef(): return Clef(pitch=("f", 3, ""))
    def _timesig(): return SimpleTimeSig()
    def t1(): return [Note(dur="q",
                           pitch=("d", 3, ""),
                           domain="bass",
                           slur=SlurOpen(id="a")
                           ),
                      Note(dur="q",
                           pitch=("d", 3, ""),
                           domain="bass",
                           
                           ),
                      Note(dur="q",
                           pitch=("d", 3, ""),
                           domain="bass",
                           ),
                      Note(dur="q",
                           pitch=("e", 3, ""),
                           domain="bass",
                           ),
                      Barline()]
    
    def t2(): return [Note(dur="q",
                           pitch=("f", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("f", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("f", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("f", 3, ""),
                           domain="bass"),
                      Barline()]
    def t3(): return [Note(dur="q",
                           pitch=("e", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("d", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("e", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("f", 3, ""),
                           domain="bass"),
                      Barline()
                      ]
    def t4(): return [Note(dur="h",
                           pitch=("d", 3, ""),
                           domain="bass"),
                      Note(dur="h",
                           pitch=("d", 3, ""),
                           domain="bass",
                           slur=SlurClose(id="a")),
                      Barline()]
    def t5(): return [Note(dur="q",
                           pitch=("f", 3, ""),
                           domain="bass",
                           slur=SlurOpen(id="b")),
                      Note(dur="q",
                           pitch=("f", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("f", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("g", 3, ""),
                           domain="bass"),
                      Barline()]
    def t6(): return [Note(dur="q",
                           pitch=("a", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("a", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("a", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("a", 3, ""),
                           domain="bass"),
                      Barline()]
    def t7(): return [        Note(dur="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Barline()]
    def t8(): return [    Note(dur="h",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(dur="h",
             pitch=("f", 3, ""),
             domain="bass",
             slur=SlurClose(id="b")),
        Barline()]
    def t9(): return [Note(dur="q",
                           pitch=("a", 3, ""),
                           domain="bass",
                           slur=SlurOpen(id="c")),
                      Note(dur="q",
                           pitch=("a", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("a", 3, ""),
                           domain="bass"),
                      Note(dur="q",
                           pitch=("a", 3, ""),
                           domain="bass"),
                      Barline()]
    def t10(): return [
        Note(dur="q",
             pitch=("b", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("b", 3, ""),
             domain="bass"),
        Note(dur="h",
             pitch=("b", 3, ""),
             domain="bass",
             slur=SlurClose(id="c")),
        Barline()]
    def t11(): return [        Note(dur="q",
             pitch=("g", 3, ""),
                                    domain="bass",
                                    slur=SlurOpen(id="d")),
        Note(dur="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("b", 3, ""),
             domain="bass"),
        Barline()
]
    def t12(): return [        Note(dur="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(dur="h",
             pitch=("a", 3, ""),
             domain="bass",
             slur=SlurClose(id="d")),
        Barline()
]
    def t13(): return [        Note(dur="q",
             pitch=("d", 3, ""),
                                    domain="bass",
                                    slur=SlurOpen(id="e")),
        Note(dur="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("e", 3, ""),
             domain="bass"),
        Barline()
]
    def t14(): return [        Note(dur="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Barline()
]
    def t15(): return [        Note(dur="q",
             pitch=("e", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("e", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Barline()
]
    def t16(): return [        Note(dur="h",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(dur="h",
             pitch=("d", 3, ""),
             domain="bass",
             slur=SlurClose(id="e")),
        FinalBarline()
]
    
    # # oneliner
    # one = Staff(content=[_clef(),_keysig(),_timesig()]+t1()+t2()+t3()+t4()+t5()+t6()+t7()+t8()+t9()+t10()+t11()+t12()+t13()+t14()+t15()+t16(),
    #             
    #            width=mm_to_px(270),
    #            x=20,
    #            y=60
    #             )
    
    # two1 = Staff(content=[_clef(),_keysig(),_timesig()]+t1()+t2()+t3()+t4()+t5()+t6()+t7()+t8(),
    #                width=mm_to_px(270),
    #                x=20,
    #                y=one.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 3)
    # two2 = Staff(content=[_clef(),_keysig()]+t9()+t10()+t11()+t12()+t13()+t14()+t15()+t16(),
    #                width=mm_to_px(270),
    #                x=20,
    #                y=two1.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
    #                )
    # three1=Staff(content=[_clef(),_keysig(),_timesig()]+t1()+t2()+t3()+t4()+t5(),
    #              width=mm_to_px(270),
    #              x=20,
    #              y=two2.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 3
    #              )
    # three2=Staff(content=[_clef(),_keysig()]+t6()+t7()+t8()+t9()+t10(),
    #              width=mm_to_px(270),
    #              x=20,
    #              y=three1.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
    #              )
    # three3=Staff(content=[_clef(),_keysig()]+t11()+t12()+t13()+t14()+t15()+t16(),
    #              width=mm_to_px(270),
    #              x=20,
    #              y=three2.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
    #              )
    # # 4
    # four1=Staff(content=[_clef(),_keysig(), _timesig()]+t1()+t2()+t3()+t4(),
    #              width=mm_to_px(270),
    #              x=20,
    #              y=three3.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 3
    #              )
    # four2=Staff(content=[_clef(),_keysig()]+t5()+t6()+t7()+t8(),
    #              width=mm_to_px(270),
    #              x=20,
    #              y=four1.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
    #              )
    # four3=Staff(content=[_clef(),_keysig()]+t9()+t10()+t11()+t12(),
    #              width=mm_to_px(270),
    #              x=20,
    #              y=four2.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
    #              )
    # four4=Staff(content=[_clef(),_keysig()]+t13()+t14()+t15()+t16(),
    #              width=mm_to_px(270),
    #              x=20,
    #              y=four3.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
    #              )
    
    # render(one,
    #        # two1, two2,
    #        # three1, three2, three3,
    #        # four1,four2,four3,four4,
    #        path="/tmp/test.svg")

    # bartok
    piano = MultiStaff(width=mm_to_px(270), x=20, y=200,content=[
        Staff(domain="treble",
             content=[
                    SForm(width=cfg.DESIRED_STAFF_SPACE_IN_PX*.5),
                    Clef(("g", 4,"")),
                    SimpleTimeSig(num=4, denom=4),
                    Note(pitch=("c",5,""),dur="h",slur=SlurOpen(id="bar1")),
                    Note(pitch=("d",5,""),dur="h"),
                    Barline(id="xxx",canvas_visible=False),
                    Note(pitch=("e",5,""),dur="w", 
                         canvas_visible=False, 
                         origin_visible=False,
                         id="foo"
                        ),
                    Barline(),
                    Note(pitch=("f",5,""),dur="h"),
                    Note(pitch=("e",5,""),dur="h"),
                    Barline(),
                    Note(pitch=("d",5,""),dur="h",slur=SlurClose(id="bar1")),
                    Rest(dur="h"),
                    Barline(),
                    Note(pitch=("e",5,""),dur="h",slur=SlurOpen(id="bar5")),
                    Note(pitch=("f",5,""),dur="h"),
                    Barline(),
                    Note(pitch=("g",5,""),dur="h"),
                    Note(pitch=("f",5,""),dur="h"),
                    Barline(),
                    Note(pitch=("e",5,""),dur="h"),
                    Note(pitch=("d",5,""),dur="h"),
                    Barline(),
                    Note(pitch=("c",5,""),dur="w",slur=SlurClose(id="bar5"),
                         canvas_visible=False,
                         origin_visible=False),
                    FinalBarline(canvas_visible=False)
             ]),
        Staff(domain="bass",content=[
                    SForm(width=cfg.DESIRED_STAFF_SPACE_IN_PX*.5),
                    Clef(("f", 4,"")),
                    SimpleTimeSig(num=4, denom=4),
                    Note(pitch=("c",3,""),dur="h",slur=SlurOpen(id="bar12")),
                    Note(pitch=("d",3,""),dur="h"),
                    Barline(canvas_visible=False),
                    Note(pitch=("e",3,""),dur="w", 
                         canvas_visible=False, 
                         origin_visible=False,
                         id="foo"
                        ),
                    Barline(),
                    Note(pitch=("f",3,""),dur="h"),
                    Note(pitch=("e",3,""),dur="h"),
                    Barline(),
                    Note(pitch=("d",3,""),dur="h",slur=SlurClose(id="bar12")),
                    Rest(dur="h"),
                    Barline(),
                    Note(pitch=("e",3,""),dur="h",slur=SlurOpen(id="bar52")),
                    Note(pitch=("f",3,""),dur="h"),
                    Barline(),
                    Note(pitch=("g",3,""),dur="h"),
                    Note(pitch=("f",3,""),dur="h"),
                    Barline(),
                    Note(pitch=("e",3,""),dur="h"),
                    Note(pitch=("d",3,""),dur="h"),
                    Barline(),
                    Note(pitch=("c",3,""),dur="w",slur=SlurClose(id="bar52"),
                         canvas_visible=False,
                         origin_visible=False),
                    FinalBarline(canvas_visible=False)
            ])
        ])
    
    render(piano, path="/tmp/test.svg")

    
    # staff = Staff(content=[
    #     Note(pitch=("g", 4, ""), dur="w",
    #          canvas_visible=True,
    #          # slur=SlurOpen(id="x")
    #         ),
    #     Barline(canvas_visible=True,),
    #     Note(pitch=("f", 5, ""), dur="w",canvas_visible=True,),
    #     Barline(canvas_visible=True,),
    #     Accidental(pitch=("f", 5, "#")),
    #     # Rest(dur="h"),
    #     Note(pitch=("f", 5, ""), dur="w",canvas_visible=True,),
    #     Barline(canvas_visible=True,),
    #     Note(pitch=("f", 5, ""), dur="w",canvas_visible=True,),
    #     Barline(canvas_visible=True,),
    #     Note(pitch=("f", 5, ""), dur="w",canvas_visible=True,),
    #     Barline(canvas_visible=True,),
    #     Note(pitch=("f", 4, ""), dur="w",
    #          canvas_visible=True,
    #          # slur=SlurClose(id="x")
    #         ),
    #     Barline(canvas_visible=True,)
    # ], x=40, y=100, width=mm_to_px(100))
    # render(staff,
    #        path="/tmp/test.svg")
