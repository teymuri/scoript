

"""
Conveniece for creating score objects
"""


import engine as E
import cfg
from engine import VLineSeg, HLineSeg, SForm, HForm, VForm, Char



class Clock:
    def __init__(self, duration=None):
        self.duration = duration or 0.25

def allclocks(form):
    """Returns True if form's content is made up of Clocks only."""
    return all(map(lambda C: isinstance(C, Clock), form.content))

def clock_chunks(content_list):
    indices = []
    for i in range(len(content_list)):
        if isinstance(content_list[i], Clock):
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
    THICKNESS = 1.6
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    @staticmethod               # static because it's going to be used in rules
    def make(obj):
        for i in range(5):
            y = i * cfg.DESIRED_STAFF_SPACE_IN_PX + obj.current_ref_glyph_top()
            line = HLineSeg(length=obj.width,
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

class Barline(SForm):
    # Gould, page 38: The barline is thicker than a stave-line ...
    THICKNESS = StaffLines.THICKNESS + .5
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
        self.thin = VLineSeg(
            length=self.REF_GLYPH_HEIGHT + StaffLines.THICKNESS,
            thickness=Barline.THICKNESS
        )
        # The thin barline is placed 1/2 staff spaces before the thick one
        # (Gould, p.39)
        self.space = SForm(width=cfg.DESIRED_STAFF_SPACE_IN_PX * 0.5)
        self.thick = VLineSeg(
            length=self.REF_GLYPH_HEIGHT + StaffLines.THICKNESS,
            # The thick final line is of beam thickness (Gould, p. 39).
            thickness=3         # should be decided, don't have beams yet!
        )
        self.extend_content(self.thin, self.space, self.thick)
        
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


class Stem(VLineSeg):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # See Gould page 14 (Stem Length)
        self.length = cfg.DESIRED_STAFF_SPACE_IN_PX * 3.5
        # According to Gould (p. 13, Stems) stems are thinner than
        # staff lines, but I sorta don't like it!
        self.thickness = StaffLines.THICKNESS * .9
        self.endxr = self.endyr = 1.35

class OpenBeam(E.HLineSeg):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class Note(SForm, Clock):
    def __init__(self, head_punch=None, stem_graver=None, obeam_graver=None, cbeam_graver=None,
    duration=None, pitch=None, **kwargs):
        Clock.__init__(self, duration)
        # _Pitch.__init__(self, pitch)
        self.pitch = _Pitch(name=pitch[0], suffix=pitch[2], octave=pitch[1])
        E.SForm.__init__(self, **kwargs)
        
        self._obeam_graver=obeam_graver
        self._cbeam_graver=cbeam_graver
        
        self._head_punch = head_punch
        self._stem_graver = stem_graver

    @property
    def head_punch(self): return self._head_punch
    @head_punch.setter
    def head_punch(self, newhead):
        # wird auch flag sein!!!!!!!!!!!!!!!!!!!!!!!!!!
        self._head_punch = newhead
        self.extend_content(self._head_punch)

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
    
