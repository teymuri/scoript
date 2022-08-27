
"""
Semantic Music Typesetting
"""

import tempfile
import json
import os
import xml.etree.ElementTree as ET
import subprocess as sp
import copy as cp
import svgwrite as SW
import svgelements as SE
import svgpathtools as SPT
from math import atan2, hypot

##### Font

SVG_NAMESPACE = {"ns": "http://www.w3.org/2000/svg"}
# _fontsdict = {}
# installed_fonts = []
def install_font1(path, overwrite=False):
    name, ext = os.path.splitext(os.path.basename(path))
    if os.path.exists(f"./fonts/json/{name}.json") and not overwrite:
        raise FileExistsError(f"{name} is already installed.")
    else:
        D = {}
        D[name] = {}
        if ext == ".svg":
            with open(f"./fonts/json/{name}.json", "w") as file_:
                font = ET.parse(path).getroot().find("ns:defs", SVG_NAMESPACE).find("ns:font", SVG_NAMESPACE)
                for glyph in font.findall("ns:glyph", SVG_NAMESPACE):
                    try:
                        path = SE.Path(glyph.attrib["d"], transform="scale(1 -1)")
                        # .scaled(sx=1, sy=-1)

                        # svgpathtools' scaled() method has a bug which deforms shapes. It offers however good bbox support.
                        # svgelements has unreliable bbox functionality, but transformations seem to be more safe than in pathtools.
                        # Bypass: apply transformations in svgelements and pass the d() to pathtools to get bboxes when needed.
                        min_x, min_y, max_x, max_y = path.bbox()
                        D[name][glyph.get("glyph-name")] = {
                            "d": path.d(), "left": min_x, "right": max_x, 
                            "top": min_y, "bottom": max_y, "width": max_x - min_x,
                            "height": max_y - min_y
                        }
                        # D[name][glyph.get("glyph-name")] = glyph.attrib["d"]
                    except KeyError:
                        pass
                json.dump(D[name], file_, indent=2)
                del path
                del glyph
        else:
            raise NotImplementedError("Non-svg fonts are not supported!")

loaded_fonts_dict = {}

def _load_fonts():
    smt_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir = smt_dir + "/fonts/json"
    for json_file in os.listdir(json_dir):
        with open(f"{json_dir}/{json_file}") as font:
            loaded_fonts_dict[os.path.splitext(json_file)[0]] = json.load(font)


# install_font1("./fonts/svg/haydn-11.svg",1)
_load_fonts()

def glyph_names(font):
    return loaded_fonts_dict[font].keys()

def get_glyph(name, font):
    """Returns ...
    """
    return loaded_fonts_dict[font][name]
# print(loaded_fonts_dict)


# ################################
# _fonts = {}
# current_font = "Haydn"

# We use the height of the alto clef as the reference for the height
# of the staff. Note that this name should exist in the font we are
# using. See also Chlapik page 33.
STAFF_HEIGHT_REFERENCE_GLYPH = "clefs.C"


##### Rastral, Dimensions, Margins

# 1 mm = 3.7795275591 pixels
MM_PIX_FACTOR = 3.7795275591

def mm_to_px(mm):
    """Converts millimeter to pixels. 
    """
    return mm * MM_PIX_FACTOR

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

DESIRED_STAFF_HEIGHT_IN_PXL = mm_to_px(GOULD_STAFF_HEIGHTS_IN_MM[0])
DESIRED_STAFF_SPACE_IN_PXL = mm_to_px(GOULD_STAFF_HEIGHTS_IN_MM[0] / 4)

# This factor should be used to scale all objects globally
GLOBAL_SCALE_FACTOR = 1.0


def scale_by_staff_height_factor(r):
    """Scales the number r by the chosen staff's height. The staff
    height factor is the ratio between the desired height of our staff
    (the global DESIRED_STAFF_HEIGHT_IN_PXL) and the height of the chosen reference
    glyph (which is by default the alto clef, as described by Chlapik
    on page 33). The global scale factor is present to let us control
    scaling globally for all objects.
    """
    raw_staff_height = get_glyph(STAFF_HEIGHT_REFERENCE_GLYPH, "haydn-11")["height"]
    staff_height_factor = DESIRED_STAFF_HEIGHT_IN_PXL / raw_staff_height
    return r * GLOBAL_SCALE_FACTOR * staff_height_factor


_LEFT_MARGIN = mm_to_px(36)
_TOP_MARGIN = mm_to_px(56)



# ~ Why am I not writing this as a method to FORM?
def _descendants(obj, N, D):
    if isinstance(obj, _Form) and obj.content:
        if N not in D:
            # ~ Shallow copy only the outer content List,
            D[N] = cp.copy(obj.content)
        else:
            D[N].extend(obj.content)
        for C in obj.content:
            _descendants(C, N+1, D)
    return D
    
def descendants(obj, lastgen_first=True):
    D = []
    for _, gen in sorted(_descendants(obj, 0, {}).items(), reverse=lastgen_first):
        D.extend(gen)
    return D


def members(obj):
    """Returns a list containing the object itself and all it's children.
    """
    return [obj] + descendants(obj, lastgen_first=False)

def getallin(typeof, obj):
    """Returns an iterable of all types in obj."""
    return filter(lambda O: isinstance(O, typeof), members(obj))


############# deprecated, remove
_ruletables = set()             # put this as class var in RuleTable?

def _pending_rule_tables():
    """True if there some ruletables with pending rules."""
    return [rt for rt in _ruletables if rt.is_pending()]
###############
class RuleTable:
    RULE_TABLES = set()
    def __init__(self, name=None):
        self.name = name
        self.rules = dict()
        # this order is the position where a rule was added to the
        # table in a rule definition file (e.g. cmn.py)
        self._order = 0
        self.log = True # Print rule's info as they are being applied.
        self._hook_registry = []
        self._pred_registry = []
        # _ruletables.add(self)
        RuleTable.RULE_TABLES.add(self)
    # def __repr__(self): return f"RuleTable {self.id}"
    def is_pending(self):       # this name is bullshit (not a bool)!!!
        """Returns a list of rules of this ruletable of the form:
        (order, rule dictionary)
        which are pending (waiting) for application. If nothing is pending 
        [] is returned."""
        # o=order, rd=rule dict
        return [(o, rd) for (o, rd) in self.rules.items() if not rd["applied"]]
    @classmethod
    def pending_rule_tables(cls):
        return [rt for rt in RuleTable.RULE_TABLES if rt.is_pending()]
    
    def add(self, hook, pred, desc=None, aux=False):
        """
        Rule will be added only if at least one of hook or predicate are fresh.
        """
        hhash = hook.__hash__()
        phash = pred.__hash__()
        if hhash not in self._hook_registry or phash not in self._pred_registry or aux:
            self.rules[self._order] = {"desc": desc, "hook": hook, "pred": pred, "applied": False}
            self._order += 1
            self._hook_registry.append(hhash)
            self._pred_registry.append(phash)
        
    def unsafeadd(self, hook, pred, desc=""):
        self.rules[self._order] = {"desc": desc,
                                   "hook": hook,
                                   "pred": pred,
                                   "applied": False}
        # next rule will be added at the next position, this order
        # decides when the rule should be applied.
        self._order +=1

    @classmethod
    def reset(cls):
        for rule_table in cls.RULE_TABLES:
            for rule in rule_table.rules.values():
                rule["applied"] = False
    
    def __len__(self): return len(self.rules)


# Common Music Notation, default ruletable for all objects
_RT = CMN = COMMON_MUSIC_NOTATION = RuleTable(name="CMN")






_registry = {}
def getbyid(id): return _registry[id]

class _Identifiable:
    """?"""
    def __init__(self, id_class=None):
        self.id = self.assign_id(id_class)
    
    def assign_id(self, id_class):
        id = f"{id_class.__name__}{id_class.id_counter}"
        id_class.id_counter += 1
        return id

class _SMTPath(_Identifiable, SW.path.Path):
    id_counter = 0
    def __init__(self, is_bbox=False, main_obj_id=None, **kwargs):
        _Identifiable.__init__(self, kwargs.pop("id_class", self.__class__))
        # Pass the just created id to svgwrite.path.Path, otherwise
        # it will use it's own id (which is something like path1234).
        if is_bbox:
            kwargs["id"] = f"{self.id}-BBox-for-{main_obj_id}"
        else:
            kwargs["id"] = self.id
        SW.path.Path.__init__(self, **kwargs)

class _SMTObject(_Identifiable):
    id_counter = 0
    def __init__(self, domain=None, id=None, id_class=None,
                 # We use the Common Music Notation as default rule
                 # table.
                 ruletable=COMMON_MUSIC_NOTATION,
                 toplevel=False):
        _Identifiable.__init__(self, id_class or _SMTObject)
        self.toplevel = toplevel
        self.ancestors = []
        # self.id = id or self.assign_id()
        self._svg_list = []
        self.domain = domain
        # self.ruletable = ruletable or COMMON_MUSIC_NOTATION
        self.ruletable = ruletable
        # self.index = self._get_index()
        _registry[self.id] = self

    def pack_svg_list(self): self._notimplemented("pack_svg_list")
    
    def _notimplemented(self, method_name):
        """Crashs if the derived class hasn't implemented this important method."""
        raise NotImplementedError(f"{self.__class__.__name__} must override {method_name}!")
    
    def addsvg(self, *elements):
        self._svg_list.extend(elements)

    # NOTE: following methods couldn't have been written as a at
    # init-time initialized attribute, since the parental relationship
    # which is crucial for these functions is possibly not set at
    # init-time yet.
    def parent(self):
        return self.ancestors[-1]
    
    def root(self):
        return self.ancestors[0]
    
    def siblings(self):
        return self.parent().content
    
    def direct_older_sibling(self):
        siblings = self.siblings()
        for i, obj in enumerate(siblings):
            if obj is self and i != 0:
                return siblings[i - 1]

    def index(self):
        for i, x in enumerate(self.siblings()):
            if x is self:
                return i

    def is_last_child(self):
        """Returns true if this object is the last of it's parent's
        children."""
        return self.index() == len(self.siblings()) - 1
    
    def _apply_rules(self):
        """
        Applies rules to this smt object and all it's descendants.
        A rule will look for application target objects exactly once per each 
        rule-application iteration. This means however that a rule might be applied
        to an object more than once, if the object satisfies it's pred.
        """
        depth = -1
        print("APPLYING RULES:")
        RuleTable.reset()
        while True:
            # pending_rule_tables = _pending_rule_tables()
            pending_rule_tables = RuleTable.pending_rule_tables()
            if pending_rule_tables:
                # Gehe eine Stufe tiefer rein, nach jedes Mal alle pendings 
                # bearbeitet zu haben.
                depth += 1
                for rt in pending_rule_tables:
                    # o_rd=(order, ruledictionary), sort pending rules based on their order.
                    for order, rule in sorted(rt.is_pending(), key=lambda o_rd: o_rd[0]):
                        if rt.log:
                            print(f"RT: {rt.name}, DEPTH: {depth}, ORDER: {order}, DESC: '{rule['desc']}'", end=" ")
                        # get in each round the up-to-date list of members (possibly new objects have been added etc....)
                        applied_to_something = False
                        # if rt.log: print(", APPLIED:", end=" ")
                        for m in members(self):
                            # Call the predicate function to decide
                            # whether to apply the rule or not.
                            if rule["pred"](m):
                                rule["hook"](m)
                                applied_to_something = True
                                if rt.log: print("✓", end="")
                                if isinstance(m, HForm): m._lineup() # Das untenstehende scheint sinvoller??!
                                # for a in reversed(m.ancestors):
                                    # if isinstance(a, HForm): a._lineup()
                        if not applied_to_something and rt.log:
                            print("✘")
                        elif applied_to_something and rt.log:
                            print("") # just the new line for the check mark(s) above
                        # A rule should not be applied more than once,
                        # so tag it as being applied.
                        rule["applied"] = True
                # pending_rule_tables = RuleTable.pending_rule_tables()
            else:
                break


############ page formats
def page_size(use):
    """Behind Bards, pg. 481, portrait formats (height, width)
    largest (A3) = Largest practical """
    return {
        "largest": (mm_to_px(420), mm_to_px(297)), 
        "largest_instrumental": (mm_to_px(353), mm_to_px(250)),
        "smallest_instrumental": (mm_to_px(297), mm_to_px(210)),
        "printed_sheet_music": (mm_to_px(305), mm_to_px(229)),
        "printed_choral_music": (mm_to_px(254), mm_to_px(178))
    }[use]

PAGEH, PAGEW = page_size("largest")

def render(*items, path="/tmp/smt"):
    """score items
    """
    drawing = SW.drawing.Drawing(filename=path, size=(PAGEW, PAGEH), debug=True)
    for item in items:
        item._apply_rules()
        # Form's packsvglst will call packsvglst on descendants recursively
        item.pack_svg_list()
        for elem in item._svg_list:
            drawing.add(elem)
    drawing.save(pretty=True)
    print("wrote to " + path)


class _Canvas(_SMTObject):
    def __init__(self,
                 canvas_color=None,
                 canvas_opacity=None,
                 xscale=1,
                 yscale=1,
                 x=None,
                 y=None,
                 rotate=0,
                 skewx=0,
                 skewy=0,
                 width=None,
                 height=None,
                 canvas_visible=True,
                 origin_visible=True,
                 **kwargs):
        super().__init__(**kwargs)
        self.skewx = skewx
        self.skewy = skewy
        # self.rotate=rotate
        # Only the first item in a hform will need _hlineup, for him 
        # this is set by HForm itself.
        self._is_hlineup_head = False
        self.rotate=rotate
        self.canvas_opacity = canvas_opacity or 0.3
        self.canvas_visible = canvas_visible
        self.canvas_color = canvas_color or SW.utils.rgb(20, 20, 20, "%")
        self.origin_visible = origin_visible
        self._xscale = xscale
        self._yscale = yscale
        # Permit zeros for x and y. xy will be locked if supplied as arguments.
        self._x = 0 if x is None else x
        self.x_locked = False if x is None else True
        self._y = 0 if y is None else y
        self.y_locked = False if y is None else True
        # self.y_locked = y_locked
        # self.x_locked = x_locked
        self._width = 0 if width is None else width
        self._width_locked = False if width is None else True
        self._height = 0 if height is None else height
        self.height_locked = False if height is None else True
        
    @property
    def xscale(self): return self._xscale
    @property
    def yscale(self): return self._yscale
    
    # def unlock(what):
        # if what == "y":
            # self.y_locked = False
    
    @property
    def x(self): return self._x
    @property
    def y(self): return self._y
    
    # # Placeholders
    # @property
    # def top(self): raise NotImplementedError
    # @property
    # def bottom(self): raise NotImplementedError
    # @property
    # def height(self): raise NotImplementedError
    # @property
    # def width(self): raise NotImplementedError
    # @property
    # def left(self): raise NotImplementedError
    # @property
    # def right(self): raise NotImplementedError

    # # X Setters; as these set the x, they have any effect only when x is unlocked.
    # @left.setter
    # def left(self, new): self.x += (new - self.left)
    # @right.setter
    # def right(self, new): self.x += (new - self.right)

    # # Make sure from canvas derived subclasses have implemented these computations.
    # def _compute_width(self):
        # raise NotImplementedError(f"_compute_width not overriden by {self.__class__.__name__}")
    # def _compute_height(self):
        # raise NotImplementedError(f"_compute_height not overriden by {self.__class__.__name__}")
    

    
# def _bboxelem(obj): 
    # return SW.shapes.Rect(insert=(obj.left, obj.top),
                                # size=(obj.width, obj.height), 
                                # fill=obj.canvas_color,
                                # fill_opacity=obj.canvas_opacity, 
                                # id=obj.id + "BBox")

_ORIGIN_CROSS_LEN = 20
_ORIGIN_CIRCLE_R = 4
_ORIGIN_LINE_THICKNESS = 0.06
def origin_elems(obj, main_obj_id):
    halfln = _ORIGIN_CROSS_LEN / 2
    return [SW.shapes.Circle(center=(obj.x, obj.y), r=_ORIGIN_CIRCLE_R,
                             # id=obj.id + "OriginCircle",
                             id=f"OriginCircle-for-{main_obj_id}",
                             stroke=SW.utils.rgb(87, 78, 55), fill="none",
                             stroke_width=_ORIGIN_LINE_THICKNESS),
            SW.shapes.Line(start=(obj.x-halfln, obj.y), end=(obj.x+halfln, obj.y),
                           # id=obj.id + "OriginHLine",
                           id=f"OriginHLine-for-{main_obj_id}",
                           stroke=SW.utils.rgb(87, 78, 55), 
                           stroke_width=_ORIGIN_LINE_THICKNESS),
            SW.shapes.Line(start=(obj.x, obj.y-halfln), end=(obj.x, obj.y+halfln),
                           # id=obj.id + "OriginVLine",
                           id=f"OriginVLine-for-{main_obj_id}",
                           stroke=SW.utils.rgb(87, 78, 55), 
                           stroke_width=_ORIGIN_LINE_THICKNESS)]


class _Font:
    """Adds font to Char & Form"""
    def __init__(self, font=None):
        self.font = font or tuple(loaded_fonts_dict.keys())[0]


class _View(_Canvas):
    """A view is a something which is drawn on a canvas and which can
    be observed on its own, e.g. a character, a line etc. This is in
    contrast to a form which is a container for other objects and can
    not be observed on it's own (you can see it's canvas, but not the
    form itself!).

    """
    def __init__(self, color=None, opacity=None, visible=True, **kwargs):
        super().__init__(**kwargs)
        self.color = color or SW.utils.rgb(0, 0, 0)
        self.opacity = opacity or 1
        self.visible = visible
    
    @_Canvas.x.setter
    def x(self, new):
        if not self.x_locked:
            self._x = new
            for a in reversed(self.ancestors):
                a._compute_horizontals()
    
    @_Canvas.y.setter
    def y(self, new):
        if not self.y_locked:
            self._y = new
            for a in reversed(self.ancestors):
                a._compute_verticals()
    
    def _bbox(self): self._notimplemented("_bbox")
        # raise NotImplementedError(f"_bbox method not overriden by {self.__class__.__name__}!")  
    
    @property
    def left(self): return self._bbox()[0]
    @property
    def right(self): return self._bbox()[1]
    @property
    def top(self): return self._bbox()[2]
    @property
    def bottom(self): return self._bbox()[3]
    @property
    def width(self): return self.right - self.left
    @property
    def height(self): return self.bottom - self.top
    # X Setters; as these set the x, they have any effect only when x is unlocked.
    @left.setter
    def left(self, new): self.x += (new - self.left)
    @right.setter
    def right(self, new): self.x += (new - self.right)
    # Y setters
    @top.setter
    def top(self, new): self.y += (new - self.top)
    



class Char(_View, _Font):
    def __init__(self, name, font=None, **kwargs):
        _View.__init__(self, **kwargs)
        _Font.__init__(self, font)
        self.name = name
        # self.glyph = _getglyph(self.name, self.font)
        self._glyph = get_glyph(self.name, self.font)
        # self._se_path = SE.Path(self.glyph, transform)
        # self.bbox = SPT.Path(self.glyph).bbox()
        # self._path = SPT.Path(_get_glyph_d(self.name, self.font))
        self.canvas_color = SW.utils.rgb(100, 0, 0, "%")
        # self._compute_horizontals()
        # self._compute_verticals()
    
    @_Canvas.xscale.setter
    def xscale(self, new):
        self._xscale = new
        for a in reversed(self.ancestors):
            a._compute_horizontals()
    
    @_Canvas.yscale.setter
    def yscale(self, new):
        self._yscale = new
        for a in reversed(self.ancestors):
            a._compute_verticals()
        
    
    # @_Canvas.x.setter
    # def x(self, new):
        # if not self.x_locked:
            # self._x = new
            # for a in reversed(self.ancestors):
                # a._compute_horizontals()
    # @_Canvas.y.setter
    # def y(self, new):
        # if not self.y_locked:
            # self._y = new
            # for a in reversed(self.ancestors):
                # a._compute_verticals()
    
    # @_Canvas.x.setter
    # def x(self, new):
        # if not self.x_locked:
            # dx = new - self.x # save x before re-assignment!
            # self._x = new
            # self._left += dx
            # self._right += dx
            # for A in reversed(self.ancestors): # An ancestor is always a Form!!
                # A._compute_horizontals()
    
    # @_Canvas.y.setter
    # def y(self, newy):
        # if not self.y_locked:
            # dy = newy - self.y
            # self._y = newy
            # self._top += dy
            # self._bottom += dy
            # for A in reversed(self.ancestors): # A are Forms
                # A._compute_verticals()
            
    # @_Canvas.width.setter
    # def width(self, neww):
        # raise Exception("Char's width is immutable!")

    # def _compute_left(self):
        # return self.x + scale_by_staff_height_factor(self.glyph["left"])

    # def _compute_right(self):
        # return self.x + scale_by_staff_height_factor(self.glyph["right"])

    # def _compute_width(self):
        # return scale_by_staff_height_factor(self.glyph["width"])
    
    # def _compute_top(self):
        # return self.y + scale_by_staff_height_factor(self.glyph["top"])
    
    # def _compute_bottom(self):
        # return self.y + scale_by_staff_height_factor(self.glyph["bottom"])
    
    # def _compute_height(self):
        # return scale_by_staff_height_factor(self.glyph["height"])
    
    # def pack_svg_list(self):
        # # Add bbox rect
        # if self.canvas_visible:
            # self._svg_list.append(_bboxelem(self))
        # # Add the music character
        # self._svg_list.append(SW.path.Path(d=_getglyph(self.name, self.font)["d"],
        # id=self.id, fill=self.color, fill_opacity=self.opacity,
        
        # transform="translate({0} {1}) scale(1 -1) scale({2} {3})".format(
        # self.x, self.y, self.xscale * _toplevel_scaler(), self.yscale * _toplevel_scaler())
        
        
        # ))
        # # Add the origin
        # if self.origin_visible:
            # for elem in origin_elems(self):
                # self._svg_list.append(elem)
    
    def pack_svg_list(self):
        char = _SMTPath(
            id_class=self.__class__,
            d=self._path().d(),
            fill=self.color,
            fill_opacity=self.opacity)
        bbox = _SMTPath(
            d=SPT.bbox2path(*self._bbox()).d(),
            fill=self.canvas_color,
            fill_opacity=self.canvas_opacity,
            is_bbox=True,
            main_obj_id=char.id)
        if self.canvas_visible:
            self._svg_list.append(bbox)
        # Music character itself
        if self.visible:
            self._svg_list.append(char)
        # Add the origin
        if self.origin_visible:
            for elem in origin_elems(self, char.id):
                self._svg_list.append(elem)
    
    # svgelements
    def _path(self):
        path = SE.Path(self._glyph)
        # path *= f"scale({self.xscale * _toplevel_scaler()}, {self.yscale * _toplevel_scaler()})"
        path *= f"scale({scale_by_staff_height_factor(self.xscale)}, {scale_by_staff_height_factor(self.yscale)})"
        # First rotate at 00,
        path *= f"rotate({self.rotate}deg)"
        # then move.
        path *= f"translate({self.x}, {self.y})"
        return path
        # return SE.Path(self._glyph, transform=f"rotate({self.rotate}) scale({self.xscale*_toplevel_scaler()} {self.yscale*_toplevel_scaler()})")
    
    # svgelements bbox seems to have a bug getting bboxes of transformed (rotated) paths,
    # use svgpathtools bbox instead (xmin, xmax, ymin, ymax).
    def _bbox(self): return SPT.Path(self._path().d()).bbox()
    
    # @property
    # def left(self): return self._bbox()[0]
    # @property
    # def right(self): return self._bbox()[1]
    # @property
    # def top(self): return self._bbox()[2]
    # @property
    # def bottom(self): return self._bbox()[3]
    # @property
    # def width(self): return self.right - self.left
    # @property
    # def height(self): return self.bottom - self.top
    
    # # X Setters; as these set the x, they have any effect only when x is unlocked.
    # @left.setter
    # def left(self, new): self.x += (new - self.left)
    # @right.setter
    # def right(self, new): self.x += (new - self.right)
    
    

class _Form(_Canvas, _Font):

    def __init__(self, font=None, content=None, **kwargs):
        self.content = content or []
        _Canvas.__init__(self, **kwargs)
        _Font.__init__(self, font)
        # The following 3 attributes carry information about the
        # height of a Form object. Each Form is created with a default
        # (hypothetical) height, which is equal to the height of the
        # chosen stave (DESIRED_STAFF_HEIGHT_IN_PXL). This hypothetical height
        # information can be useful in various contexts, e.g. where
        # reference to the height of the underlying stave is
        # needed. These values are relative to the position of the
        # Form on the page (they include it's y coordinate). They
        # should be considered read-only and are updated automatically
        # by the parent Form upon his replacement. Unlike this default
        # height setup, a Form has no pre-existing width (i.e. = 0).
        self._abstract_staff_height_top = self.y + scale_by_staff_height_factor(get_glyph(STAFF_HEIGHT_REFERENCE_GLYPH, self.font)["top"])
        self._abstract_staff_height_bottom = self.y + scale_by_staff_height_factor(get_glyph(STAFF_HEIGHT_REFERENCE_GLYPH, self.font)["bottom"])
        self._abstract_staff_height = scale_by_staff_height_factor(get_glyph(STAFF_HEIGHT_REFERENCE_GLYPH, self.font)["height"])
        
        for D in descendants(self, False):
            D.ancestors.insert(0, self) # Need smteq??
        for c in self.content:
            # These assignments take place only if xy are not locked!
            c.x = self.x
            c.y = self.y
            
            # if not c.x_locked:
                # c.x += self.x
            if not c.y_locked:
                # # c.y += self.y
                # c.y = self.y
                
                # If child is to be relocated vertically, their fix-top & bottom can not be
                # the original values, but must move along with the parent.
                if isinstance(c, _Form):
                    c._abstract_staff_height_top += self.y
                    # c._abstract_staff_height_top = self.y
                    c._abstract_staff_height_bottom += self.y
                    # Fixheight never changes!
    
    def delcont(self, test):
        for i, c in enumerate(self.content):
            if test(c): del self.content[i]
    
    def _compute_horizontals(self):
        self._left = self._compute_left()
        self._right = self._compute_right()
        self._width = self._compute_width()

    def _compute_verticals(self):
        self._top = self._compute_top()
        self._bottom = self._compute_bottom()
        self._height = self._compute_height()

    # Children is a sequence. This method modifies only ancestor lists.
    def _establish_parental_relationship(self, children):
        for child in children:
            assert isinstance(child, _SMTObject), "Form can only contain MeObjs!"
            child.ancestors.insert(0, self)
            if isinstance(child, _Form):
                for D in descendants(child, False):
                    D.ancestors.insert(0, self)
            for A in reversed(self.ancestors):
                child.ancestors.insert(0, A)
                if isinstance(child, _Form):
                    for D in descendants(child, False):
                        D.ancestors.insert(0, A)

    @_Canvas.x.setter
    def x(self, new):
        if not self.x_locked:
            dx = new - self.x
            self._x = new
            self._left += dx
            self._right += dx
            for D in descendants(self, False):
                # Descendants' x are shifted by delta-x. 
                D._x += dx
                if isinstance(D, _Form):
                    D._left += dx
                    D._right += dx
            for A in reversed(self.ancestors):
                A._compute_horizontals()

    @_Canvas.y.setter
    def y(self, new):
        if not self.y_locked:
            dy = new - self.y
            self._y = new
            self._top += dy
            self._bottom += dy
            for D in descendants(self, False):
                D._y += dy
                if isinstance(D, _Form):
                    # # D._y += dy
                    D._top += dy
                    D._bottom += dy
            # Shifting Y might have an impact on ancestor's width!
            for A in reversed(self.ancestors):
                A._compute_verticals()
    
    def _compute_left(self):
        """Determines the left-most of either: form's own x coordinate 
        or the left-most site of it's direct children."""
        return min([self.x] + list(map(lambda c: c.left, self.content)))
        # return min(self.x, *[c.left for c in self.content])
        # return self._bbox()[0]

    def _compute_right(self):
        if self._width_locked: # ,then right never changes!
            return self.left + self.width
        else:
            return max([self.x] + list(map(lambda c: c.right, self.content)))
    # def _compute_right(self): return self._bbox()[1]

    def _compute_width(self):
        # # print(self.id)
        # if self._width_locked:
            # return self.width
        # else:
            # return self.right - self.left
        return self.width if self._width_locked else (self.right - self.left)

    def _compute_top(self):
        return min([self._abstract_staff_height_top] + list(map(lambda c: c.top, self.content)))
        # return min(self._abstract_staff_height_top, self._bbox()[2])
    
    def _compute_bottom(self):
        return max([self._abstract_staff_height_bottom] + list(map(lambda c: c.bottom, self.content)))
        # return max(self._abstract_staff_height_bottom, self._bbox()[3])
    
    def _compute_height(self): 
        return self.height if self.height_locked else self.bottom - self.top
    
    def pack_svg_list(self):
        # Bbox
        if self.canvas_visible: 
            # self._svg_list.append(_bboxelem(self))
            self._svg_list.append(
                SW.shapes.Rect(insert=(self.left, self.top),
                                size=(self.width, self.height), 
                                fill=self.canvas_color,
                                fill_opacity=self.canvas_opacity, 
                                id=f"{self.id}-BBox")
            )
        # Add content
        for C in self.content:
            # C.xscale *= self.xscale
            # C.yscale *= self.yscale
            # Recursively pack svg elements of each child:
            C.pack_svg_list() 
            self._svg_list.extend(C._svg_list)
        # Origin
        if self.origin_visible:
            self._svg_list.extend(origin_elems(self, self.id))
        
    # def pack_svg_list(self):
        # # Bbox
        # if self.canvas_visible:
            # self._svg_list.append(SW.path.Path(
                # d=SPT.bbox2path(*self._bbox()).d(),
                # fill=self.canvas_color,
                # fill_opacity=self.canvas_opacity, 
                # id=f"{self.id}-BBox")
                # )
        # # Add content
        # for C in self.content:
            # C.xscale *= self.xscale
            # C.yscale *= self.yscale
            # C.pack_svg_list() # Recursively gather svg elements
            # self._svg_list.extend(C._svg_list)
        # # Origin
        # # if self.origin_visible: self._svg_list.extend(origin_elems(self))
        
    @property
    def left(self): return self._left
    @property
    def right(self): return self._right
    @property
    def top(self): return self._top
    @property
    def bottom(self): return self._bottom
    @property
    def width(self): return self._width
    @property
    def height(self): return self._height
    
    # Setters
    @left.setter
    def left(self, new):
        self.x += (new - self.left)
    
    @right.setter
    def right(self, new): 
        self.x += (new - self.right)
    @top.setter
    def top(self, new): self.y += (new - self.top)
    
    @width.setter
    def width(self, new):
        if not self._width_locked:
            self._right = self.left + new
            self._width = new
            # self.right = self.left + new
            for A in reversed(self.ancestors):
                A._compute_horizontals()
    
    # # SPT bbox output: xmin, xmax, ymin, ymax
    # def _bbox(self):
        # # print(">>",self.id, [[*c._bbox()] for c in self.content])
        # # return SPT.Path(*[SPT.bbox2path(*c._bbox()) for c in self.content]).bbox()
        # if self.content:
            # bboxs = [c._bbox() for c in self.content]
            # minx = min(self.x, *[bb[0] for bb in bboxs])
            # maxx = max(self.x, *[bb[1] for bb in bboxs])
            # miny = min(self.y, *[bb[2] for bb in bboxs])
            # maxy = max(self.y, *[bb[3] for bb in bboxs])
            # return SPT.Path(SPT.bbox2path(minx, maxx, miny, maxy)).bbox()
        # else:
            # return 0, 0, self._abstract_staff_height_top, self._abstract_staff_height_bottom


class SForm(_Form):
        
    def __init__(self, **kwargs):
        _Form.__init__(self, **kwargs)
        self.canvas_color = SW.utils.rgb(0, 100, 0, "%")
        self.domain = kwargs.get("domain", "stacked")
        # Content may contain children with absolute x, so compute horizontals with respect to them.
        # See whats happening in _Form init with children without absx!
        self._compute_horizontals()
        self._compute_verticals()
    
    # Sinnvoll nur in rule-application-time?!!!!!!!!!!!!!!!
    def append(self, *children):
        """Appends new children to Form's content list."""
        self._establish_parental_relationship(children)
        for c in children:
            c.x = self.x
            c.y = self.y
        self.content.extend(children)
        # # Having set the content before would have caused assign_x to trigger computing horizontals for the Form,
        # # which would have been to early!????
        self._compute_horizontals()
        self._compute_verticals()
        for A in reversed(self.ancestors):
            if isinstance(A, _Form) and not isinstance(A, SForm):
                A._lineup()
            A._compute_horizontals()
            A._compute_verticals()


class HForm(_Form):

    def __init__(self, **kwargs):
        _Form.__init__(self, **kwargs)
        # self.abswidth = abswidth
        self.canvas_color = SW.utils.rgb(0, 0, 100, "%")
        self.domain = kwargs.get("domain", "horizontal")
        # Lineup content created at init-time,
        self._lineup()
        # then compute surfaces.
        self._compute_horizontals()
        self._compute_verticals()
            
    def _lineup(self):
        for a, b in zip(self.content[:-1], self.content[1:]):            
            b.left = a.right

class VForm(_Form):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._lineup()
        self._compute_horizontals()
        self._compute_verticals()
    def _lineup(self):
        for a, b in zip(self.content[:-1], self.content[1:]):
            b.top = a.bottom
    def append(self, *children):
        """Appends new children to Form's content list."""
        self._establish_parental_relationship(children)
        for c in children:
            c.x = self.x
            c.y = self.y
        self.content.extend(children)
        # # Having set the content before would have caused assign_x to trigger computing horizontals for the Form,
        # # which would have been to early!????
        self._lineup()
        self._compute_horizontals()
        self._compute_verticals()
        for A in reversed(self.ancestors):
            if isinstance(A, _Form) and not isinstance(A, SForm): # V & H
                A._lineup()
            A._compute_horizontals()
            A._compute_verticals()
        
# https://github.com/meerk40t/svgelements/issues/102
class _LineSeg(_View):
    """Angle in degrees"""
    def __init__(self, length=None, direction=None, thickness=None, angle=None, endxr=None, endyr=None,
    # start=None, end=None,
    **kwargs):
        super().__init__(**kwargs)
        self.length = length or 0
        # self.color = color or SW.utils.rgb(0, 0, 0)
        # self.opacity = opacity
        self._angle = angle or 0
        self._thickness = thickness or 0
        self.direction = direction or 1
        self.endxr = endxr or 0
        self.endyr = endyr or 0
        # self.start = start
        # self.end = end
        # self._x2 = 
        # self._y2=y2
        # self._compute_horizontals()
        # self._compute_verticals()


    # Override canvas packsvglist
    def pack_svg_list(self):
        # the main thing
        line = _SMTPath(
            id_class=self.__class__,
            d=self._rect().d(),
            fill=self.color, fill_opacity=self.opacity
        )
        # bbox
        line_bbox = _SMTPath(
            d=SPT.bbox2path(*self._bbox()).d(),
            fill=SW.utils.rgb(100,100,0,"%"),
            fill_opacity=self.canvas_opacity,
            is_bbox=True,
            main_obj_id=line.id
        )
        if self.canvas_visible: # why not called bbox_visible then??!!
            self._svg_list.append(line_bbox)
        if self.visible:
            self._svg_list.append(line)
        # Add the origin
        if self.origin_visible:
            for elem in origin_elems(self, line.id):
                self._svg_list.append(elem)
        
        
    # @property
    # def length(self): return self._length
    
    # @_Canvas.x.setter
    # def x(self, new):
        # if not self.x_locked:
            # # dx = new - self.x
            # self._x = new
            # # self._left += dx
            # # self._right += dx
            # for A in reversed(self.ancestors): # An ancestor is always a Form!!
                # A._compute_horizontals()
    
    # @_Canvas.y.setter
    # def y(self, new): 
        # if not self.y_locked:
            # # dy = new - self.y
            # self._y = new
            # # self._top += dy
            # # self._bottom += dy
            # for A in reversed(self.ancestors): # An ancestor is always a Form!!
                # A._compute_verticals()
    
    @property
    def thickness(self): return self._thickness
    # xmin, xmax, ymin, ymax
    def _bbox(self):
        return SPT.Path(self._rect().d()).bbox()








class VLineSeg(_LineSeg):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    # def angle(self):
        # """Inverse tangent of the line in radians"""
        # return atan2(self.y2 - self.y, self.x2 - self.x)
    # def _recty(self): return self.y - self.thickness*.5
    # def _rect(self):
        # R = SE.Rect(self.x, self._recty(), hypot(self.x2-self.x, self.y2-self.y), self.thickness)
        # R *= f"rotate({self.angle()}rad {self.x} {self.y})"
        # return R
    
    def _rect(self):
        rect = SE.Rect(
            # Rect(x, y, width, height, rx, ry, matrix, stroke, fill)
            self.x - self.thickness*.5, self.y, 
            self.thickness, self.length,
            self.endxr, self.endyr
            )
        rect *= f"skew({self.skewx}, {self.skewy}, {self.x}, {self.y})"
        rect *= f"rotate({self.rotate}deg, {self.x}, {self.y})"
        return rect
    

    
    # @property
    # def left(self): return self._bbox()[0]
    # @property
    # def right(self): return self._bbox()[1]
    # @property
    # def top(self): return self._bbox()[2]
    # @property
    # def bottom(self): return self._bbox()[3]
    # @property
    # def width(self): 
        # # return self.thickness
        # return self.right-self.left
    # @property
    # def height(self):
        # # return self.length
        # return self.bottom -self.top
    
    # def _compute_width(self): return self.thickness
    # def _compute_left(self): return self.x - self.thickness*.5
    # def _compute_right(self): return self.x + self.thickness*.5
    # def _compute_height(self): return self.length
    # def _compute_bottom(self): return self.y + self.length
    # def _compute_top(self): return self.y
    # @_LineSeg.length.setter
    # def length(self, new):
        # self._length = new
        # self._compute_verticals()
        # for a in reversed(self.ancestors):
            # a._compute_verticals()

class HLineSeg(_LineSeg):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def _rect(self):
        rect = SE.Rect(
            self.x,
            self.y - self.thickness*.5,
            # self.y,
            self.length,
            self.thickness,
            self.endxr,
            self.endyr
            )
        rect *= f"scale({self.direction} 1)"
        rect *= f"skew({self.skewx}, {self.skewy}, {self.x}, {self.y})"
        rect *= f"rotate({self.rotate}deg, {self.x}, {self.y})"
        return rect
    # def _compute_width(self): return self.length
    # def _compute_height(self): return self.thickness
    # def _compute_left(self): return self.x
    # def _compute_right(self): return self.x + self.length
    # def _compute_top(self): return self.y - self.thickness*.5
    # def _compute_bottom(self): return self.y + self.thickness*.5




