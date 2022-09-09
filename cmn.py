import sys
import os

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
SMT_DIR = os.path.dirname(TEST_DIR)
if SMT_DIR not in sys.path:
    sys.path.append(SMT_DIR)

import random
import cfg
from engine import (RuleTable, render, HForm, mm_to_px, HLineSeg,
                    DESIRED_STAFF_SPACE_IN_PX, Char, CMN, VLineSeg,
                    DESIRED_STAFF_HEIGHT_IN_PX)
from score import (SimpleTimeSig, Clef, Note, Barline, StaffLines, KeySig, Accidental, Staff, Stem, FinalBarline)


"""
This file contains rules for engraving Common Music Notation.
"""

from random import randint, choice
# from engine import DESIRED_STAFF_SPACE_IN_PX, Char, HForm, CMN, VLineSeg
import score as S
# from score import Note, Clef, SimpleTimeSig, StaffLines, Barline
import copy 



cfg.CANVAS_VISIBLE = cfg.ORIGIN_VISIBLE = False

def _treble_pitch_offset_from_staff_bottom(obj):
    return obj.current_ref_glyph_bottom() + {
        "c": 1, "d": 0.5, "e": 0, "f": -0.5,
        "g": -1, "a": -1.5, "b": -2
    }[obj.pitch.name] * DESIRED_STAFF_SPACE_IN_PX

def _bass_pitch_offset_from_staff_bottom(obj):
    return obj.current_ref_glyph_bottom() + {
        "b": -1,
        "a": -.5, "g": 0, "f": 0.5, "e": 1, "d": 1.5, "c": 2
    }[obj.pitch.name] * DESIRED_STAFF_SPACE_IN_PX
    
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
    space towards top of page to get F4 (-0.5 * DESIRED_STAFF_SPACE_IN_PX, topwards
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

def is_simple_timesig(x): return isinstance(x, S.SimpleTimeSig)
def set_simple_timesig_chars(ts):
    """this is the ultimate, the one and the only guy putting
    together and punching time sigs"""
    ts.num_char=S.E.Char({3: "three", 4:"four", 5:"five"}.get(ts.num, ".notdef"),
                           canvas_visible=False,
                           origin_visible=False)
    ts.denom_char=S.E.Char({4: "four", 2:"two", 1: "one"}.get(ts.denom, ".notdef"),
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
    }[obj.duration])
    obj.head_punch.y = _pitch_vertical_pos(obj)

def isnote(x): return isinstance(x,S.Note)



def isstem(o): return isinstance(o, S.Stem)
def set_stem_line(note):
    if note.duration in ("q", "h"):
        stem = Stem(x=note.x+.4,
                    y=note.head_punch.y)
        note.stem_graver = stem



def make_accidental_char(accobj):
    if not accobj.punch:
        accobj.punch = S.E.Char(name="accidentals.sharp", canvas_visible=False,
                     origin_visible=False)

def set_clef_char(clefobj):
    clefobj.char = Char(
        name={"g":"clefs.G","f":"clefs.F"}[clefobj.pitch.name])
    if clefobj.pitch.name == "g":
        clefobj.char.y = clefobj.current_ref_glyph_bottom() - DESIRED_STAFF_SPACE_IN_PX
    elif clefobj.pitch.name == "f":
        clefobj.char.y = clefobj.current_ref_glyph_top() + DESIRED_STAFF_SPACE_IN_PX



############################# punctuation

def find_ref_dur(dur_counts):
    """Returns the duration name with the largest number of occurrences.
    """
    return list(sorted(dur_counts, key=lambda lst: lst[0]))[0][1]

# from Gould page 39
DURS_SPACE_PROPORTION = {
    "w":7, "h": 5, "q": 3.5,"8":3.5, "e": 2.5, "s": 2
}

def _dur_ref_ratio(dur, ref_dur):
    """Returns the ratio of the duration's space proportion to
    the reference duration's space proportion.
    """
    return DURS_SPACE_PROPORTION[dur] / DURS_SPACE_PROPORTION[ref_dur]
    
def compute_perf_punct(clocks, w):
    # notes=list(filter(lambda x:isinstance(x, Note), clocks))
    durs=list(map(lambda x:x.duration, clocks))
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
        space = ((uw * _dur_ref_ratio(x.duration, udur)) - x.width)
        perfwidths.append(space)
        # x.width += ((uw * _dur_ref_ratio(udur, x.duration)) - x.width)
    return perfwidths

def right_guard(obj):
    return {S.Note: 2, S.Clef:0,
            S.Accidental: 2,
            S.SimpleTimeSig: 0}[type(obj)]

RIGHT_MARGIN = {
    KeySig: DESIRED_STAFF_SPACE_IN_PX,
    Accidental: DESIRED_STAFF_SPACE_IN_PX,
    Clef: DESIRED_STAFF_SPACE_IN_PX,
    Barline: DESIRED_STAFF_SPACE_IN_PX,
    SimpleTimeSig: DESIRED_STAFF_SPACE_IN_PX
}

def first_clock_idx(l):
    for i,x in enumerate(l):
        if isinstance(x, S.Clock):
            return i

def durs_to_count_dict(valued_objs_list) -> dict[str, int]:
    durs_list = [obj.duration for obj in valued_objs_list]
    return {dur: durs_list.count(dur) for dur in set(durs_list)}
    # return [(durs_list.count(dur), dur) for dur in set(durs_list)]

# Note that durations MUST BE strings!
def _find_ref_dur(durs_to_count: dict[str, int]) -> str:
    return max(durs_to_count, key=durs_to_count.get)

    
def horizontal_spacing(staff):
    # breakpoint()
    # get sum of all non-valued character's width of the staff
    non_valued_objs = [x for x in staff.content if not isinstance(x, Note)]
    # non_valued_objs_space = sum([x.width + RIGHT_MARGIN[type(x)] for x in non_valued_objs])
    non_valued_objs_space = 0
    for x in non_valued_objs:
        non_valued_objs_space += x.width
        if not (isinstance(x, (FinalBarline, Barline)) and x.is_last_child()):
            non_valued_objs_space += RIGHT_MARGIN[type(x)]
    # get the remaining space for valued objs
    remain_space = staff.width - non_valued_objs_space
    # compute ideal widths for notes ()
    valued_objs = [x for x in staff.content if isinstance(x, Note)]
    durs_to_count = durs_to_count_dict(valued_objs)
    ref_dur: str = _find_ref_dur(durs_to_count)
    ref_dur_count = sum([v * _dur_ref_ratio(k, ref_dur) for k, v in durs_to_count.items()])
    # ideal width for the reference duration
    ref_dur_width = remain_space / ref_dur_count
    valued_objs_space: list = [(ref_dur_width * _dur_ref_ratio(obj.duration, ref_dur) - obj.width) for obj in valued_objs]
    if all([isinstance(x, Note) for x in staff.content]):
        for obj, width in zip(staff.content, valued_objs_space):
            obj.width += width
            obj._width_locked = True
    else:
        valued_obj_idx = 0
        for obj in staff.content:
            if isinstance(obj, Note):
                obj.width += valued_objs_space[valued_obj_idx]
                valued_obj_idx += 1
                obj._width_locked = True
            else:
                # A barline at the end of the staff doesn't need it's
                # right margin.
                if not (isinstance(obj, (FinalBarline, Barline)) and obj.is_last_child()):
                    obj.width += RIGHT_MARGIN[type(obj)]
    
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
    o=[x for x in l.content if isnote(x) and x.duration in ("q","h")] #note mit openbeam
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
                        thickness=Barline.THICKNESS,
                        y=obj.current_ref_glyph_top() - StaffLines.THICKNESS * .5,
                        # a barline is normally used after a note or a rest
                        x=obj.direct_older_sibling().right,
                        canvas_visible=True,
                        canvas_opacity=0.1,
                        visible=True)

def is_final_barline(obj):
    return isinstance(obj, FinalBarline)

def place_final_barline(obj):
    obj.x = obj.direct_older_sibling().right
    # obj.thin.x = obj.direct_older_sibling().right
    obj.y = obj.current_ref_glyph_top() - StaffLines.THICKNESS * .5
    # The thin barline is placed 1/2 staff spaces before the thick one
    # (Gould, p.39)
    obj.thick.x = obj.x + DESIRED_STAFF_SPACE_IN_PX * .5
    obj.thick.x_locked =True
    # obj.extend_content(obj.thin, obj.thick)
    
    
# S.E.CMN.add(skew, isline, "SKEW stave")
# S.E.CMN.unsafeadd(skew, isline, "SKEW stave")

def flag(note):
    if note.duration != 1:
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
              is_simple_timesig,"Set Time...",)

CMN.unsafeadd(set_notehead_char, noteandtreble, "make noteheads",)
# CMN.unsafeadd(notehead_vertical_pos, noteandtreble, "note vertical position")

CMN.unsafeadd(set_keysig_char_list, is_keysig, "engraving keysig ...")

CMN.unsafeadd(set_accidental_char,
              is_accidental,
              "making accidental chars ...",)


S.E.CMN.unsafeadd(set_stem_line, isnote, "setting stems...",)

S.E.CMN.unsafeadd(set_clef_char, isclef, "Make clefs")

CMN.unsafeadd(set_barline_char, lambda obj: is_barline(obj), "placing barlines")
CMN.unsafeadd(place_final_barline,is_final_barline,
              "placing final barline...")
# S.E.CMN.unsafeadd(punctsys,
#                   # isline,
#                   lambda x: isinstance(x, HForm),
#                   "Punctuate",)

CMN.unsafeadd(horizontal_spacing,
              lambda x: isinstance(x, Staff),
              "horizontal_spacing,")

CMN.unsafeadd(StaffLines.make,
              lambda obj: isnote(obj) or \
              isclef(obj) or \
              is_simple_timesig(obj) or \
              is_accidental(obj) or \
              is_keysig(obj) or \
              is_barline(obj) and not obj.is_last_child(),
              "Draws stave ontop/behind(?)")


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
    #          duration="q",
    #          pitch=["f", 5]),
    #     # Accidental(pitch=("f", 5, "#")),
    #     Note(domain="treble",
    #          duration="q",
    #          pitch=["f", 5]),
    #     # Accidental(pitch=("f", 5, "#")),
    #     Note(domain="treble",
    #          duration="q",
    #          pitch=["f", 5]),
    #     # Accidental(pitch=("g", 5, "#")),
    #     Note(domain="treble",
    #          duration="q",
    #          pitch=["g", 5]),
    #     Barline(),
    #     # Accidental(pitch=("a", 5, "#")),
    #     Note(domain="treble",
    #          duration="h",
    #          pitch=["a", 5]),
    #     # Accidental(pitch=("g", 5, "#")),
    #     Note(domain="treble",
    #          duration="h",
    #          pitch=["g", 5]),
    #     Barline(),
    #     # Accidental(pitch=("f", 5, "#")),
    #     Note(domain="treble",
    #          duration="q",
    #          pitch=["f", 5]),
    #     # Accidental(pitch=("a", 5, "#")),
    #     Note(domain="treble",
    #          duration="q",
    #          pitch=["a", 5]),
    #     # Accidental(pitch=("g", 5, "#")),
    #     Note(domain="treble",
    #          duration="q",
    #          pitch=["g", 5]),
    #     # Accidental(pitch=("g", 5, "#")),
    #     Note(domain="treble",
    #          duration="q",
    #          pitch=["g", 5]),
    #     Barline(),
    #     # Accidental(pitch=("c", 5, "#")),
    #     Note(domain="treble",
    #          duration="w",
    #          pitch=["f", 5]),
    #     Barline()
    # ],
    #           width=mm_to_px(270),
    #           x=20,
    #           y=60,
    #           canvas_visible=True,
    #           origin_visible=True)


    # Auf der Mauer, auf der Lauer
    bass = Clef(pitch=("f", 3, ""))
    keysig = KeySig(scale="dmaj", domain="bass")
    timesig = SimpleTimeSig()
    first_8_bars = [
        bass, keysig, timesig,
        # t 1
        Note(duration="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("e", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("e", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("e", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="h",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="h",
             pitch=("d", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="h",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="h",
             pitch=("f", 3, ""),
             domain="bass"),
        Barline()
    ]
    last_8_bars = [
        Clef(pitch=("f", 3, "")),
        KeySig(scale="dmaj", domain="bass"),
        # last 8 bars
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("b", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("b", 3, ""),
             domain="bass"),
        Note(duration="h",
             pitch=("b", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("g", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("b", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("a", 3, ""),
             domain="bass"),
        Note(duration="h",
             pitch=("a", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("e", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="q",
             pitch=("e", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("e", 3, ""),
             domain="bass"),
        Note(duration="q",
             pitch=("f", 3, ""),
             domain="bass"),
        Barline(),
        Note(duration="h",
             pitch=("d", 3, ""),
             domain="bass"),
        Note(duration="h",
             pitch=("d", 3, ""),
             domain="bass")
    ]
    staff1 = Staff(content=first_8_bars,
                   width=mm_to_px(270),
                   x=20,
                   y=60)
    staff2 = Staff(content=last_8_bars,
                   width=mm_to_px(270),
                   x=20,
                   y=staff1.y + DESIRED_STAFF_HEIGHT_IN_PX * 2)
    render(staff1, staff2, path="/tmp/test.svg")
