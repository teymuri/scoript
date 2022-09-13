import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)

import random
import cfg
from engine import (RuleTable, render, HForm, mm_to_px, HLineSeg,
                    Char, CMN, VLineSeg)
from score import (SimpleTimeSig, Clef, Note, Barline, StaffLines, KeySig, Accidental, Staff, Stem, FinalBarline, _Time)
from random import randint, choice
import score as S
import copy 



cfg.CANVAS_VISIBLE = cfg.ORIGIN_VISIBLE = False

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
    pitch_name: str = obj.pitch.name
    octave: int = obj.pitch.octave
    if obj.domain == "treble":
        pos_on_staff = _treble_pitch_offset_from_staff_bottom(obj)
        ref_oct = 4
    elif obj.domain == "bass":
        pos_on_staff = _bass_pitch_offset_from_staff_bottom(obj)
        ref_oct = 2
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
        char_list.append(Accidental(pitch=("f", o, "#"), domain=dom))
        char_list.append(Accidental(pitch=("c", o, "#"), domain=dom))
    keysig.char_list = char_list


    
def is_accidental(obj):
    return isinstance(obj, Accidental)

def set_accidental_char(obj):
    name = {"#": "accidentals.sharp"}.get(obj.pitch.suffix,
                                          cfg.UNDEFINED_GLYPH)
    char = Char(name=name)
    obj.char = char
    obj.char.y = _pitch_vertical_pos(obj)



# Setting noteheads
def set_notehead_char(obj):
    obj.head_punch = Char(name={
        "w": "noteheads.s0",
        "h": "noteheads.s1",
        "q": "noteheads.s2",
        "e": "noteheads.s2"
    }[obj.dur])
    obj.head_punch.y = _pitch_vertical_pos(obj)

def isnote(x): return isinstance(x, Note)



def isstem(o): return isinstance(o, S.Stem)
def set_stem_line(note):
    if note.dur in ("q", "h"): # needs stem
        stem = Stem(x=note.x+.7,
                    y=note.head_punch.y,
                    )
        note.stem_graver = stem



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

NON_TIME_OBJS_RIGHT_PADDING = {
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

def _map_durs_to_count(valued_objs_list) -> dict[str, int]:
    durs_list = [obj.dur for obj in valued_objs_list]
    return {dur: durs_list.count(dur) for dur in set(durs_list)}

# Note that durations MUST BE strings!
def _find_ref_dur(durs_to_count: dict[str, int]) -> str:
    """Returns the dur with the heighest number of appearances."""
    return max(durs_to_count, key=durs_to_count.get)

def time_obj_space_list(staff):
    right_paddings = NON_TIME_OBJS_RIGHT_PADDING
    while True:
        # get sum of all non-timed character's width of the staff
        non_time_objs = [x for x in staff.content if not _Time.is_time(x)]
        non_time_objs_space = 0
        for x in non_time_objs:
            non_time_objs_space += x.width
            if not (isinstance(x, (FinalBarline, Barline)) and x.is_last_child()):
                non_time_objs_space += right_paddings[type(x)]
        # get the remaining space for valued objs
        time_objs_space = staff.width - non_time_objs_space
        # compute ideal widths for objs with durations (notes and rests and chords)
        time_objs = [x for x in staff.content if _Time.is_time(x)]
        durs_to_count: dict = _map_durs_to_count(time_objs)
        ref_dur: str = _find_ref_dur(durs_to_count)
        # Wieviele red_durs könnten wir insgesamt haben?
        ref_dur_count = sum([v * _dur_ref_ratio(k, ref_dur) for k, v in durs_to_count.items()])
        # ideal width for the reference dur
        # See Ross page 73
        unit_of_space = time_objs_space / ref_dur_count
        shortest_time_obj = _Time.shortest(time_objs)
        shortest_time_obj_width = None
        _time_obj_space_list = []
        for obj in time_objs:
            space = unit_of_space * _dur_ref_ratio(obj.dur, ref_dur) - obj.width
            _time_obj_space_list.append(space)
            if obj is shortest_time_obj:
                shortest_time_obj_width = space
        # momentan nehme ich an right paddding ist immer 1 staff space...
        if shortest_time_obj_width >= right_paddings[sorted(right_paddings, key=right_paddings.get)[0]]:
            return (_time_obj_space_list, right_paddings)
        else:
            # zieh 1 pixel ab
            right_paddings = {_type: padding - 1 for _type, padding in right_paddings.items()}

def imperfect_punctuation(staff):
    _time_obj_space_list, right_paddings = time_obj_space_list(staff)
    if all([isinstance(x, Note) for x in staff.content]):
        for obj, width in zip(staff.content, _time_obj_space_list):
            obj.width += width
            obj._width_locked = True
    else:
        time_obj_idx = 0
        for obj in staff.content:
            if isinstance(obj, Note):
                obj.width += _time_obj_space_list[time_obj_idx]
                time_obj_idx += 1
                obj._width_locked = True
            else:
                # A barline at the end of the staff doesn't need it's
                # right margin.
                if not (isinstance(obj, (FinalBarline, Barline)) and obj.is_last_child()):
                    obj.width += right_paddings[type(obj)]
    
def punctsys(h):
    # print("---punct----")
    first_clock_idx_ = first_clock_idx(h.content)
    startings=h.content[0:first_clock_idx_]
    for starting in startings:
        starting.width += right_guard(starting)
    clkchunks=S.clock_chunks(h.content[first_clock_idx_:])
    # print(clkchunks)
    clocks = list(map(lambda l:l[0], clkchunks))
    perfwidths = compute_perf_punct(clocks, h.width - sum([x.width for x in startings]))
    if S.allclocks(h):
        for C, w in zip(h.content, perfwidths):
            C.width += w
            C._width_locked = True
    else:
        for c,w in zip(clkchunks, perfwidths):
            clock = c[0]
            nonclocks = c[1:]
            s=sum([nc.width + right_guard(nc) for nc in nonclocks])
            # s=sum(map(lambda x:x.width + right_guard(x), nonclocks))
            if s <= w:
                # add rest of perfect width - sum of nonclocks
                clock.width += (w - s)
                clock._width_locked = True
                for a in nonclocks:
                    a.width += right_guard(a)
                    # dont need to lock this width, since it's not touched
                    # by set_stem_line: set_stem_line only impacts it's papa: the NOTE object
                    # a._width_locked = 1
    # h.lineup()


def noteandtreble(x):
    return isinstance(x, Note)



def greenhead(x): x.head_punch.color = e.SW.utils.rgb(0,0,100,"%")
def reden(x): 
    print(x.id, x.content)
    x.content[0].color = e.SW.utils.rgb(100,0,0,"%")
def Sid(x): return x.id == "S"
def isline(x): return isinstance(x, (System, S.E.HForm))
def ish(x): return isinstance(x, e.HForm)
def isclef(x): return isinstance(x, S.Clef)
def opachead(n): n.head_punch.opacity = .3


def setbm(l):
    o=[x for x in l.content if isnote(x) and x.dur in ("q","h")] #note mit openbeam
    # c=[x for x in l.content if isnote(x) and x.close_beam][0]
    # d=c.stem_graver.right -o.stem_graver.left
    for a in o:
        a.obeam_graver = S.E.HLineSeg(length=a.width,thickness=5,
        x=a.left,
        y=a.stem_graver.bottom,
        # rotate=45,
        )
    # o.append(S.E.HLineSeg(length=o.width,thickness=5,x=o.left, y=o.stem_graver.bottom))
    # c.append(S.E.HLineSeg(length=o.width,thickness=5,x=o.left, y=o.stem_graver.bottom))





def skew(stave):
    print(stave.skewx)
    stave.skewx = 50
    print(stave.skewx)
def ishline(x): return isinstance(x,S.E.HLineSeg)
def is_barline(x): return isinstance(x, Barline)

def set_barline_char(obj):
    # obj is a barline object
    obj.char = VLineSeg(length=obj._abstract_staff_height + StaffLines.THICKNESS,
                        thickness=Barline.THICKNESS + 1,
                        y=obj.current_ref_glyph_top() - StaffLines.THICKNESS * .5,
                        # a barline is normally used after a note or a rest
                        x=obj.direct_older_sibling().right if obj.direct_older_sibling() else obj.parent().x,
                        canvas_visible=True,
                        canvas_opacity=0.1,
                        visible=True)

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
# S.E.CMN.add(flag, isnote, "Flags...")
# print(S.E._glyph_names("haydn-11"))

# def bm(n):
    # if n.stem_graver:
        # n.stem_graver.length -= 10
        # n.extend_content(S.E.HLineSeg(length=10, thickness=5, y=n.stem_graver.bottom, skewy=-0, endxr=1,endyr=.5))


# S.E.CMN.add(bm, isnote, "beams")



# Rules adding
"""
hook mehrmals überall, 
test
"""
# The single argument to rule hooks are every objects defined in your
# score.
CMN.unsafeadd(set_simple_timesig_chars,
              is_simple_timesig)

CMN.unsafeadd(set_notehead_char, noteandtreble,)
# CMN.unsafeadd(notehead_vertical_pos, noteandtreble, "note vertical position")

CMN.unsafeadd(set_keysig_char_list, is_keysig)

CMN.unsafeadd(set_accidental_char,
              is_accidental)


S.E.CMN.unsafeadd(set_stem_line, isnote)

S.E.CMN.unsafeadd(set_clef_char, isclef)

CMN.unsafeadd(set_barline_char,
              lambda obj: is_barline(obj))

CMN.unsafeadd(place_final_barline,
              is_final_barline)

CMN.unsafeadd(imperfect_punctuation,
              lambda x: isinstance(x, Staff))

CMN.unsafeadd(StaffLines.make,
              lambda obj: isnote(obj) or \
              isclef(obj) or \
              is_simple_timesig(obj) or \
              is_accidental(obj) or \
              is_keysig(obj) or \
              is_barline(obj) and not obj.is_last_child() or \
              is_final_barline(obj))


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
                            domain="bass"),
                       Note(dur="q",
                            pitch=("d", 3, ""),
                            domain="bass"),
                       Note(dur="q",
                            pitch=("d", 3, ""),
                            domain="bass"),
                       Note(dur="q",
                            pitch=("e", 3, ""),
                            domain="bass"),
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
                           domain="bass"),
                      Barline()]
    def t5(): return [Note(dur="q",
                           pitch=("f", 3, ""),
                           domain="bass"),
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
             domain="bass"),
        Barline()]
    def t9(): return [        Note(dur="q",
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
    def t10(): return [
        Note(dur="q",
             pitch=("b", 3, ""),
             domain="bass"),
        Note(dur="q",
             pitch=("b", 3, ""),
             domain="bass"),
        Note(dur="h",
             pitch=("b", 3, ""),
             domain="bass"),
        Barline()]
    def t11(): return [        Note(dur="q",
             pitch=("g", 3, ""),
             domain="bass"),
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
             domain="bass"),
        Barline()
]
    def t13(): return [        Note(dur="q",
             pitch=("d", 3, ""),
             domain="bass"),
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
             domain="bass"),
        FinalBarline()
]
    
    # oneliner
    one = Staff(content=[_clef(),_keysig(),_timesig()]+t1()+t2()+t3()+t4()+t5()+t6()+t7()+t8()+t9()+t10()+t11()+t12()+t13()+t14()+t15()+t16(),
               width=mm_to_px(270),
               x=20,
               y=60
                )
    two1 = Staff(content=[_clef(),_keysig(),_timesig()]+t1()+t2()+t3()+t4()+t5()+t6()+t7()+t8(),
                   width=mm_to_px(270),
                   x=20,
                   y=one.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 3)
    two2 = Staff(content=[_clef(),_keysig()]+t9()+t10()+t11()+t12()+t13()+t14()+t15()+t16(),
                   width=mm_to_px(270),
                   x=20,
                   y=two1.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
                   )
    three1=Staff(content=[_clef(),_keysig(),_timesig()]+t1()+t2()+t3()+t4()+t5(),
                 width=mm_to_px(270),
                 x=20,
                 y=two2.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 3
                 )
    three2=Staff(content=[_clef(),_keysig()]+t6()+t7()+t8()+t9()+t10(),
                 width=mm_to_px(270),
                 x=20,
                 y=three1.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
                 )
    three3=Staff(content=[_clef(),_keysig()]+t11()+t12()+t13()+t14()+t15()+t16(),
                 width=mm_to_px(270),
                 x=20,
                 y=three2.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
                 )
    # 4
    four1=Staff(content=[_clef(),_keysig(), _timesig()]+t1()+t2()+t3()+t4(),
                 width=mm_to_px(270),
                 x=20,
                 y=three3.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 3
                 )
    four2=Staff(content=[_clef(),_keysig()]+t5()+t6()+t7()+t8(),
                 width=mm_to_px(270),
                 x=20,
                 y=four1.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
                 )
    four3=Staff(content=[_clef(),_keysig()]+t9()+t10()+t11()+t12(),
                 width=mm_to_px(270),
                 x=20,
                 y=four2.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
                 )
    four4=Staff(content=[_clef(),_keysig()]+t13()+t14()+t15()+t16(),
                 width=mm_to_px(270),
                 x=20,
                 y=four3.y + cfg.DESIRED_STAFF_HEIGHT_IN_PX * 2
                 )
    
    render(one,
           two1, two2,
           three1, three2, three3,
           four1,four2,four3,four4,
           path="/tmp/test.svg")

    # render(Staff(content=[
    #     Note(pitch=("f", 5, ""), dur="q"),
    #     Note(pitch=("f", 5, ""), dur="e"),
    #     Accidental(pitch=("f", 5, "#")),
    #     Note(pitch=("f", 5, ""), dur="e"),
    #     Note(pitch=("f", 5, ""), dur="q"),
    #     Note(pitch=("f", 5, ""), dur="q"),
    #     Barline()
    # ],
    #              width=mm_to_px(100)),
    #        path="/tmp/test.svg")
