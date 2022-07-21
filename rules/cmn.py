"""
"""

from random import randint, choice
import score as S
import copy 

################ time signature

def is_simple_timesig(x): return isinstance(x, S.SimpleTimeSig)
def make_simple_timesig(ts):
    """this is the ultimate, the one and the only guy putting
    together and punching time sigs"""
    ts.num_punch=S.E.MChar({3: "three", 4:"four", 5:"five"}.get(ts.num, ".notdef"),
                           canvas_visible=False,
                           origin_visible=False)
    ts.denom_punch=S.E.MChar({4: "four", 2:"two", 1: "one"}.get(ts.denom, ".notdef"),
                             canvas_visible=False,
                             origin_visible=False)
    # I'm shifting the 1 here because I know the font's properties?
    if ts.denom == 1:
        d=ts.denom_punch.parent().width - ts.denom_punch.width
        ts.denom_punch.right = ts.denom_punch.parent().right
        







# Setting noteheads
def make_notehead(note):
    # setter for head? to append automatically
    if isinstance(note.duration, str):
        note.head_punch = S.E.MChar(name={
            "w": "noteheads.s0",
            "h": "noteheads.s1",
            "q": "noteheads.s2",
        }[note.duration],
                                    canvas_visible=False,
                                    origin_visible=False)
    # elif isinstance(note.duration, (float, int)):
        # note.head_punch = S.E.MChar(name={
            # 1: "noteheads.s0",
            # .5: "noteheads.s1",
            # .25: "noteheads.s2"
        # }[note.duration],
        # rotate=0)
def isnote(x): return isinstance(x,S.Note)



def isstem(o): return isinstance(o, S.Stem)
def setstem(self):
    if self.duration in (.25, .5, "q", "h", "8"):
        # self.stem_graver = S.E._LineSeg(x2=0, y2=10,thickness=2)
        s=S.Stem(length=20,thickness=1, 
                 x=self.x+.5, # Eigentlich wenn wir dieses X eingeben, es wird als absolut-X gesehen.
                 y=self.head_punch.y,
                 endyr=1,endxr=1,rotate=0,
                 origin_visible=False, canvas_visible=False)
        self.stem_graver = s #taze , appliedto =false

def notehead_vertical_pos(note_obj):
    if isinstance(note_obj.pitch, list):
        p = note_obj.pitch[0]
        okt = note_obj.pitch[1]
        note_obj.head_punch.y = ((note_obj.fixbottom - {
            "a": -(2 * S.E.STAFF_SPACE),
            "b": -(1.5 * S.E.STAFF_SPACE),
            "c": -(1 * S.E.STAFF_SPACE), 
            "d": -(0.5 * S.E.STAFF_SPACE),
            "x": -(0 * S.E.STAFF_SPACE),
        }[p]) + ((4 - okt) * 7/8 * note_obj.FIXHEIGHT))


def make_accidental_char(accobj):
    if not accobj.punch:
        accobj.punch = S.E.MChar(name="accidentals.sharp", canvas_visible=False,
                     origin_visible=False)

def setclef(clefobj):
    clefobj.punch = S.E.MChar(name={"g": "clefs.G", 1:"clefs.C",
                                    "F":"clefs.F", "f":"clefs.F_change","c":"clefs.C"}[clefobj.pitch],
                              rotate=0, canvas_visible=False,
                              origin_visible=False)

############################# punctuation

def decide_unit_dur(dur_counts):
    # return list(sorted(dur_counts.items()))[1][1]
    return list(sorted(dur_counts, key=lambda l:l[0]))[0][1]

punct_units = {"w":7, "h": 5, "q": 3.5,"8":3.5, "e": 2.5, "s": 2}

def ufactor(udur, dur2):
    return punct_units[dur2] / punct_units[udur]
    
def compute_perf_punct(clocks, w):
    # notes=list(filter(lambda x:isinstance(x, Note), clocks))
    durs=list(map(lambda x:x.duration, clocks))
    dur_counts = []
    for d in set(durs):
        # dur_counts[durs.count(d)] =d
        # dur_counts[d] =durs.count(d)
        dur_counts.append((durs.count(d), d))
    udur=decide_unit_dur(dur_counts)
    uw=w / sum([x[0] * ufactor(udur, x[1]) for x in dur_counts])
    perfwidths = []
    for x in clocks:
        # a space is excluding the own width of the clock (it's own char width)
        space = ((uw * ufactor(udur, x.duration)) - x.width)
        perfwidths.append(space)
        # x.width += ((uw * ufactor(udur, x.duration)) - x.width)
    return perfwidths

def right_guard(obj):
    return {S.Note: 2, S.Clef:3, S.Accidental: 2, S.SimpleTimeSig: 5}[type(obj)]
def first_clock_idx(l):
    for i,x in enumerate(l):
        if isinstance(x, S.Clock):
            return i
            
            
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
                    # by setstem: setstem only impacts it's papa: the NOTE object
                    # a._width_locked = 1
    # h._lineup()


def noteandtreble(x): return isinstance(x, S.Note) and x.domain == "treble"
def isacc(x): return isinstance(x, S.Accidental)


def greenhead(x): x.head_punch.color = e.SW.utils.rgb(0,0,100,"%")
def reden(x): 
    print(x.id, x.content)
    x.content[0].color = e.SW.utils.rgb(100,0,0,"%")
def Sid(x): return x.id == "S"
def isline(x): return isinstance(x, (System, S.E.HForm))
def ish(x): return isinstance(x, e.HForm)
def isclef(x): return isinstance(x, S.Clef)
def opachead(n): n.head_punch.opacity = .3

# Rules adding
"""
hook mehrmals überall, 
test
"""
# The single argument to rule hooks are every objects defined in your
# score.
S.E.CMN.unsafeadd(make_simple_timesig,is_simple_timesig,"Set Time...",)
S.E.CMN.unsafeadd(make_notehead, noteandtreble, "make noteheads",)
S.E.CMN.unsafeadd(notehead_vertical_pos, noteandtreble, "note vertical position")
S.E.CMN.unsafeadd(make_accidental_char, isacc, "Making Accidental Characters",)
# e.CMN.unsafeadd(greenhead, noteandtreble)
S.E.CMN.unsafeadd(setstem, isnote, "Set stems",)
S.E.CMN.unsafeadd(setclef, isclef, "Make clefs",)
# S.E.CMN.unsafeadd(opachead, isnote)
S.E.CMN.unsafeadd(punctsys, isline, "Punctuate",)


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


# S.E.CMN.unsafeadd(setbm, isline,
#                   "Setting the beams, after noteheads are fixed (punctuated)"
#                   )

# "Set beams after Noten stehen fest (punctuation)",


def addstaff(n):
    # s=S.Staff()
    # n.append(s)
    # print(s.y)
    # n.append(S.E.MultiHLineSeg(6, S.E.STAFF_SPACE, n.fixtop))
    # m=S.E.MChar(name="m")
    # n.append(m)
    # n.append(S.E.HLineSeg(length=30, thickness=1, y=n.fixtop))
    # print(m.x, m.y, n.x, n.y)
    # print(n.FIXHEIGHT)
    x=5
    h=n.FIXHEIGHT / (x-1)
    for i in range(x):
        l=S.E.HLineSeg(length=n.width, thickness=1, y=i*h + n.top,
                       canvas_visible=False,
                       origin_visible=False)
        n.append(l)
        # S.E.CMN.add(rescale, pred(obj, isinstance(obj, int)), "Reset acc xscale.")
        # print(S.E.CMN.rules.keys())

# class pred:
    # def __init__(self, obj, *exprs):
        # self.obj = obj
        # self.exprs = exprs
    # def _replace(self):
        # for e in self.exprs:
            # print(e)
# # pred(isinstance(int), )
    
S.E.CMN.unsafeadd(addstaff,
                  lambda obj: isnote(obj),
                  "Draws stave.")


def skew(staff):
    print(staff.skewx)
    staff.skewx = 50
    print(staff.skewx)
def ishline(x): return isinstance(x,S.E.HLineSeg)
# S.E.CMN.add(skew, isline, "SKEW stave")
# S.E.CMN.unsafeadd(skew, isline, "SKEW stave")

def flag(note):
    if note.duration != 1:
        # print(note.stem_graver.y)
        note.append(S.E.MChar(name="flags.d4",y=note.stem_graver.bottom,x=note.x+.5,
        origin_visible=1))
# S.E.CMN.add(flag, isnote, "Flags...")
# print(S.E._glyph_names("haydn-11"))

# def bm(n):
    # if n.stem_graver:
        # n.stem_graver.length -= 10
        # n.append(S.E.HLineSeg(length=10, thickness=5, y=n.stem_graver.bottom, skewy=-0, endxr=1,endyr=.5))


# S.E.CMN.add(bm, isnote, "beams")



# 680.3149 pxl
# gemischt=[
# Note(domain="treble", duration=1, pitch=["c",4]),
# Accidental(pitch=["c", 4],domain="treble",),
# Accidental(domain="treble"), 
# # Clef(pitch="g",domain="treble"),
# Accidental(domain="treble"),
# Note(pitch=["d",4],domain="treble", duration=.5),
# Note(pitch=["d",4],domain="treble", duration=.25),
# # Clef(domain="treble",pitch="bass"),
# Accidental(domain="treble",pitch=["d",4])
# ]

class System(S.E.HForm):
    def __init__(self, cnt, **kw):
        S.E.HForm.__init__(self, content=cnt, **kw, canvas_visible=False,)
# s=SForm(width=5,width_locked=0,x=50)
# s.append(Stem(length=10,thickness=30))
# h=HForm(content=[s],width=mm_to_pix(20),x=40,y=200, canvas_opacity=.2, width_locked=0)
# F=S.E.RuleTable()
# def note(pitch, dur, **kwargs):
    # return {"type": "note", "pitch":pitch, "dur":dur,**kwargs}
# def sethead(n):
    # print(n["dur"])
    # return S.E.SForm(content=S.E.MChar(n["name"]))
# print(sethead(note(0,1,name="noteheads.s0")))
if __name__=="__main__":
    ns = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50)
    W = 270
    hs = []
    for x in range(22):
        h = S.E.HForm(content=[
            S.Clef(pitch=choice(("g", "f")), canvas_visible=False, origin_visible=False),
            S.SimpleTimeSig(denom=1, canvas_visible=False,origin_visible=False),
            *[S.Note(domain="treble",
                     duration=choice(["q", "h", "w"]),
                     pitch=[choice(["c", "d"]), 5],
                     canvas_visible=False,
                     origin_visible=False)
              for _ in range(choice(ns))]
        ],
                      width=S.E.mm_to_pix(W),
                      x=20,
                      y=60 + x * 70,
                      canvas_visible=False,
                      origin_visible=False)
        hs.append(h)
    
    S.E.render(*hs)
