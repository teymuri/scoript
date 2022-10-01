

"""
Conveniece objects for creating music
"""


import engine as E
import cfg
from engine import _SMTObject, VLine, HLine, SForm, HForm, VForm, Char, _SimplePointedCurve



class _Clock:
    ORDER = {
        "s": 0, "e": 1, "q": 2,
        "h": 3, "w": 4
    }
    def __init__(self, dur=None):
        # durations are: "w", "h", "q", "e", "s"
        self.dur = dur or "q"
    
    @staticmethod
    def shortest(time_objs_list):
        return sorted(time_objs_list,
                      key=lambda obj: _Clock.ORDER[obj.dur])[0]
    
    @classmethod
    def is_clock(cls, obj):
        return isinstance(obj, cls)

    # DEPRECATED! use Staff.get_clocks
    @staticmethod
    def get_clock_objs(staff):
        return [obj for obj in staff.content if _Clock.is_clock(obj)]

    @staticmethod
    def get_non_time_objs(staff):
        return [obj for obj in staff.content if not _Clock.is_clock(obj)]



def allclocks(form):
    """Returns True if form's content is made up of Clocks only."""
    return all(map(lambda C: isinstance(C, _Clock), form.content))

def clock_chunks(content_list):
    indices = []
    for i in range(len(content_list)):
        if isinstance(content_list[i], _Clock):
            indices.append(i)
    chunks = []
    for start, end in zip(indices[:-1], indices[1:]):
        chunks.append(content_list[start:end])
    chunks.append(content_list[indices[-1]:])
    return chunks

class _Pitch:
    def __init__(self, name: str, suffix: str, octave: int):
        self.name = name
        # calling accidentals suffix because of lacking a better name,
        # didn't want to colide with the name accidental, search a
        # better term!
        self.suffix = suffix
        self.octave = octave



class StaffLines(VForm):
    THICKNESS = cfg.DESIRED_STAFF_SPACE_IN_PX * 0.17
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @staticmethod               # static because it's going to be used in rules
    def make(obj):
        """drawing staff lines..."""
        for i in range(5):
            y = i * cfg.DESIRED_STAFF_SPACE_IN_PX + obj.current_ref_glyph_top()
            line = HLine(length=obj.width,
                            thickness=StaffLines.THICKNESS,
                            y=y,
                            x=obj.left,
                            # opacity=0.5,
                            canvas_visible=True,
                            canvas_opacity=0.1,
                            visible=True)
            obj.extend_content(line)


class Staff(HForm):
    def __init__(self, **kwargs):
        HForm.__init__(self, **kwargs)

    def is_clocks_only(self):
        """Returns true if the content of the staff is made up of
        clocks only."""
        return all([isinstance(x, _Clock) for x in self.content])

    def get_clocks(self):
        """Returns all clock objs in my content list."""
        return [obj for obj in self.content if isinstance(obj, _Clock)]


class Barline(SForm):
    # Gould, page 38: The barline is thicker than a stave-line ...
    THICKNESS = StaffLines.THICKNESS + .1
    
    def __init__(self, type="single", **kwargs):
        # Types by Gould: single, double, final, repeat
        self.type = type
        self._char = None
        super().__init__(**kwargs)
    
    @property
    def char(self):
        return self._char
    
    @char.setter
    def char(self, new):
        self._char = new
        self.extend_content(self._char)


class FinalBarline(HForm):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thin = VLine(
            length=self.REF_GLYPH_HEIGHT + StaffLines.THICKNESS,
            thickness=Barline.THICKNESS
        )
        # The thin barline is placed 1/2 staff spaces before the thick one
        # (Gould, p.39)
        self.space = SForm(width=cfg.DESIRED_STAFF_SPACE_IN_PX * 0.5)
        self.thick = VLine(
            length=self.REF_GLYPH_HEIGHT + StaffLines.THICKNESS,
            # The thick final line is of beam thickness (Gould, p. 39).
            thickness=3         # should be decided, don't have beams yet!
        )
        self.extend_content(self.thin, self.space, self.thick)


def is_last_barline_on_staff(obj):
    return isinstance(obj, (Barline, FinalBarline)) and obj.is_last_child()
        
class KeySig(HForm):
    
    def __init__(self, scale, **kwargs):
        self.scale = scale
        self._char_list = []
        HForm.__init__(self, **kwargs)
    
    @property
    def char_list(self):
        return self._char_list
    
    @char_list.setter
    def char_list(self, new_list):
        self._char_list = new_list
        self.extend_content(*self._char_list)


class Stem(VLine):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Die Länge der Notenhälse beträgt in der Regel 3
        # Rastralzwischenräume (Chlapik p. 39).
        # 3.5 spaces (Ross, p. 83)
        self.length = cfg.DESIRED_STAFF_SPACE_IN_PX * 3.5
        # Der Notenhals soll die gleiche
        # Stärke haben wie das Liniensystem (Chlapik p. 39).
        self.thickness = StaffLines.THICKNESS
        self.endxr = self.endyr = 1.35

class OpenBeam(E.HLine):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Rest(_Clock, SForm):
    
    def __init__(self, dur, **kwargs):
        _Clock.__init__(self, dur)
        SForm.__init__(self, **kwargs)
        self._char = None

    @property
    def char(self):
        return self._char

    @char.setter
    def char(self, new):
        self._char = new
        self.extend_content(self._char)
        
        
class Note(SForm, _Clock):
    
    def __init__(self,
                 head_char=None, # ???
                 stem_graver=None,
                 obeam_graver=None,
                 cbeam_graver=None,
                 dur=None,
                 pitch=None,
                 slur=None,
                 **kwargs):
        if "domain" not in kwargs:
            kwargs["domain"] = "treble"
        SForm.__init__(self, **kwargs)
        _Clock.__init__(self, dur)
        if pitch:
            self.pitch = _Pitch(name=pitch[0], suffix=pitch[2], octave=pitch[1])
        else:
            self.pitch = _Pitch(name="c", suffix="", octave=4)
        self._obeam_graver=obeam_graver
        self._cbeam_graver=cbeam_graver
        self._slur = slur
        if self._slur:
            self._slur.owner = self
        self._head_char = head_char
        self._stem_graver = stem_graver

    @property
    def slur(self):
        return self._slur

    @slur.setter
    def slur(self, new):
        self._slur = new
        self.extend_content(self._slur)
        
    @property
    def head_char(self):
        return self._head_char
    
    @head_char.setter
    def head_char(self, newhead):
        # wird auch flag sein!!!!!!!!!!!!!!!!!!!!!!!!!!
        self._head_char = newhead
        self.extend_content(self._head_char)

    @property
    def stem_graver(self): return self._stem_graver
    @stem_graver.setter
    def stem_graver(self, newstem):
        # Allow only a single stem_graver per note?
        self.delcont(lambda c: isinstance(c, Stem))
        self._stem_graver = newstem
        self.extend_content(self._stem_graver)
    @property
    def obeam_graver(self): return self._obeam_graver
    @obeam_graver.setter
    def obeam_graver(self, new):
        self._obeam_graver = new
        self.extend_content(self._obeam_graver)
    @property
    def cbeam_graver(self): return self._cbeam_graver
    @cbeam_graver.setter
    def cbeam_graver(self, new):
        self._cbeam_graver = new
        self.extend_content(self._cbeam_graver)


class Accidental(SForm):
    def __init__(self, pitch=None, **kwargs):
        if "domain" not in kwargs:
            kwargs["domain"] = "treble"
        SForm.__init__(self, **kwargs)
        # self.pitch = pitch      # e.g. ("f", 5, "#")
        self.pitch = _Pitch(name=pitch[0], suffix=pitch[2], octave=pitch[1])
        self._char = None
        
    @property
    def char(self): return self._char
    
    @char.setter
    def char(self, new):
        self.delcont(lambda c: isinstance(c, Char))
        self._char = new
        self.extend_content(self._char)


class Clef(SForm):
    def __init__(self, pitch=None, **kwargs):
        SForm.__init__(self, **kwargs)
        # _Pitch.__init__(self, pitch)
        self.pitch = _Pitch(name=pitch[0], suffix=pitch[2], octave=pitch[1])
        self._char = None

    @property
    def char(self): return self._char
    @char.setter
    def char(self, new):
        self.delcont(lambda c: isinstance(c, e.Char))
        self._char = new
        self.extend_content(self._char)

class SimpleTimeSig(E.VForm):
    def __init__(self, num=4, denom=4, **kwargs):
        self.num=num
        self.denom=denom
        self._num_char=None
        self._denom_char=None
        super().__init__(**kwargs)

    @property
    def num_char(self): return self._num_char
    @num_char.setter
    def num_char(self, new):
        self._num_char = new
        self.extend_content(self._num_char)
    
    @property
    def denom_char(self): return self._denom_char
    @denom_char.setter
    def denom_char(self, new):
        if self._denom_char: # First time setting in a rule
            self.delcont(lambda c: c.id == self._denom_char.id)
        self._denom_char = new
        self.extend_content(self._denom_char)


class _Slur:
    
    def __init__(self, id, owner=None):
        self.id = id
        self.owner = owner


class SlurOpen(_Slur):
    
    registry = dict()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        SlurOpen.registry[self.id] = self
    
    @staticmethod
    def get_by_id(id):
        return SlurOpen.registry[id]


class SlurClose(_Slur):
    pass
