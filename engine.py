
"""
Semantic Music Typesetting
"""

import tempfile
import json
import os
import cfg                      # 
import xml.etree.ElementTree as ET
import subprocess as sp
import copy as cp
import svgwrite as SW
import svgelements as SE
import svgpathtools as SPT

from tqdm import tqdm
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


def mm_to_px(mm):
    """Converts millimeter to pixels.
    1 mm = 3.7795275591 pixels
    """
    return mm * 3.7795275591


def n_staff_spaces(n):
    """Returns the specified amount of staff spaces (in pixels)."""
    return n * cfg.DESIRED_STAFF_SPACE_IN_PX

def scale_by_staff_height_factor(r):
    """Scales the number r by the chosen staff's height. The staff
    height factor is the ratio between the desired height of our staff
    (the global cfg.DESIRED_STAFF_HEIGHT_IN_PX) and the height of the chosen reference
    glyph (which is by default the alto clef, as described by Chlapik
    on page 33). The global scale factor is present to let us control
    scaling globally for all objects.
    """
    raw_staff_height = get_glyph(cfg.STAFF_HEIGHT_REF_GLYPH, "haydn-11")["height"]
    staff_height_factor = cfg.DESIRED_STAFF_HEIGHT_IN_PX / raw_staff_height
    return r * cfg.GLOBAL_SCALE_FACTOR * staff_height_factor






def _index_generation_mapping(obj, gen_idx: int, gen_dict: dict) -> dict[int, list]:
    """Returns a mapping of generation indices to generation family_tree
    of object. Index is added to the output of this helper function to
    make the descendants function capable of sorting based on
    generation indices."""
    if isinstance(obj, _Form) and obj.content:
        if gen_idx not in gen_dict:
            # ~ Shallow copy only the outer content List,
            gen_dict[gen_idx] = cp.copy(obj.content)
        else:
            gen_dict[gen_idx].extend(obj.content)
        for child in obj.content:
            _index_generation_mapping(child, gen_idx+1, gen_dict)
    return gen_dict
    
def descendants(obj, young_gen_first=True) -> list:
    """Returns a full list of all children and grand children and
    grand grand children and so on of the object (hence the naming
    descendants and not e.g. children). By default the youngest of
    generations appear first in the list, then their parents, then
    their grand parents and so forth.

    """
    desc_list = []
    for _, gen_list in sorted(_index_generation_mapping(obj, 0, {}).items(),
                              reverse=young_gen_first):
        desc_list.extend(gen_list)
    return desc_list

def family_tree(obj) -> list:
    """Returns a list containing the object and it's descendants
    ordered from old to young.

    """
    return [obj] + descendants(obj, young_gen_first=False)


############# deprecated, remove
_ruletables = set()             # put this as class var in RuleTable?

def _pending_rule_tables():
    """True if there some ruletables with pending rules."""
    return [rt for rt in _ruletables if rt.pending_rules()]
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

    def make_rule(self, hook, pred, desc) -> dict:
        return {"desc": desc,
                "hook": hook,
                "pred": pred,
                "applied": False}
    
    def pending_rules(self) -> list:       # this name is bullshit (not a bool)!!!
        """Returns a sorted list of only rules of this ruletable
        instance of the form (order: int, rule: dict obtained from
        self.make_rule) which are pending (waiting) for application.

        """
        return [(order, rule) for (order, rule) in sorted(self.rules.items()) if not rule["applied"]]
    
    @classmethod
    def pending_rule_tables(cls) -> list[dict[int, dict]]:
        """Returns any rule tables if there is any unapplied rules in it."""
        return [rule_table for rule_table in RuleTable.RULE_TABLES if rule_table.pending_rules()]
    
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
        
    def unsafeadd(self, hook, pred, desc=None): # rename register
        self.rules[self._order] = self.make_rule(hook, pred, desc or hook.__name__)
        # next rule will be added at the next position, this order
        # decides when the rule should be applied.
        self._order +=1

    @classmethod
    def reset(cls):
        """Marks all rules as unapplied, so they will be applicable."""
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
    
    def apply_rules(self):
        """
        Applies rules to this smt object and all it's descendants.
        A rule will look for application target objects exactly once per each 
        rule-application iteration. This means however that a rule might be applied
        to an object more than once, if the object satisfies it's pred.
        """
        depth = -1
        # mark all rules as unapplied, this is necessary because
        # apply_rules could be called multiple times by render for
        # each of it's items.
        RuleTable.reset()
        while True:
            # pending_rule_tables = _pending_rule_tables()
            pending_rule_tables = RuleTable.pending_rule_tables()
            if pending_rule_tables:
                # Gehe eine Stufe tiefer rein, nach jedes Mal alle pendings 
                # bearbeitet zu haben.
                depth += 1
                # NOTE: rule tables are not sorted! maybe can add also
                # an order to them (like with rules) to let them be
                # sortable?!!!
                
                # pend_rule_tabs_prog_bar = tqdm(pending_rule_tables)
                for rt in pending_rule_tables:
                    for order, rule in rt.pending_rules():                       
                        print(f"RT: {rt.name}, DEPTH: {depth}, ORDER: {order}, DESC: '{rule['desc']}'")
                            
                        # get in each round the up-to-date list of family_tree (possibly new objects have been added etc....)
                        members_prog_bar = tqdm(family_tree(self), leave=0)
                        for member in members_prog_bar:
                            # Call the predicate function to decide
                            # whether to apply the rule or not.
                            if rule["pred"](member):
                                members_prog_bar.set_description(f"applying to {member}")
                                rule["hook"](member)
                                if isinstance(member, (HForm, VForm)):
                                    member.lineup()
                            else:
                                members_prog_bar.set_description(f"skipped {member}")
                        # A rule should not be applied more than once,
                        # so tag it as being applied.
                        rule["applied"] = True
                # this is a bit of an overkill, but was added to allow
                # modifications to the ruletables on the fly
                # (e.g. rules adding new rules) to take effect.
                pending_rule_tables = RuleTable.pending_rule_tables()
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
        item.apply_rules()
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
        self.canvas_visible = cfg.CANVAS_VISIBLE and canvas_visible
        self.canvas_color = canvas_color or SW.utils.rgb(20, 20, 20, "%")
        self.origin_visible = cfg.ORIGIN_VISIBLE and origin_visible
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
    @property
    def x(self): return self._x
    @property
    def y(self): return self._y

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
    be observed on its own. This is in contrast to a form which is a
    container for other objects and can not be observed on it's own
    (you can see it's canvas, but not the form itself!).
    Note that a view's ...
    Examples for views are characters and lines.
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
            for anc in reversed(self.ancestors):
                anc.refresh_horizontals()
    
    @_Canvas.y.setter
    def y(self, new):
        if not self.y_locked:
            self._y = new
            for anc in reversed(self.ancestors):
                anc.refresh_verticals()
    
    def _bbox(self): self._notimplemented("_bbox")
    
    @property
    def left(self):
        return self._bbox()[0]
    
    # X Setters; as these set the x, they have any effect only when x is unlocked.
    @left.setter
    def left(self, new):
        self.x += (new - self.left)
    
    @property
    def right(self):
        return self._bbox()[1]

    @right.setter
    def right(self, new):
        self.x += (new - self.right)
    
    @property
    def top(self):
        return self._bbox()[2]

    @property
    def bottom(self):
        return self._bbox()[3]
    
    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    # Y setters
    @top.setter
    def top(self, new): self.y += (new - self.top)
    



class Char(_View, _Font):
    def __init__(self, name, font=None, **kwargs):
        _View.__init__(self, **kwargs)
        _Font.__init__(self, font)
        self.name = name
        self._glyph = get_glyph(self.name, self.font)
        self.canvas_color = SW.utils.rgb(100, 0, 0, "%")
    
    @_Canvas.xscale.setter
    def xscale(self, new):
        self._xscale = new
        for a in reversed(self.ancestors):
            a.refresh_horizontals()
    
    @_Canvas.yscale.setter
    def yscale(self, new):
        self._yscale = new
        for a in reversed(self.ancestors):
            a.refresh_verticals()
    
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
    
    # svgelements bbox seems to have a bug getting bboxes of transformed (rotated) paths,
    # use svgpathtools bbox instead (xmin, xmax, ymin, ymax).
    def _bbox(self): return SPT.Path(self._path().d()).bbox()
    
    

class _Form(_Canvas, _Font):

    def __init__(self, font=None, content=None, **kwargs):
        _Canvas.__init__(self, **kwargs)
        _Font.__init__(self, font)
        self.content = content or []
        self._establish_parent_relation(self.content)
        # The following 3 attributes carry information about the
        # height of a Form object. Each Form is created with a default
        # (imaginary) height, which is equal to the height of the
        # chosen staff (cfg.DESIRED_STAFF_HEIGHT_IN_PX). This imaginary height
        # information can be useful in various contexts, e.g. where
        # reference to the height of the underlying staff is
        # needed. These values are relative to the position of the
        # Form on the page (they contain it's y coordinate). They
        # should be considered read-only and are updated automatically
        # by the parent Form upon his replacement. Unlike this default
        # height setup, a Form has no pre-existing width (i.e. width = 0 pixels).
        self._abstract_staff_height_top = self.y + scale_by_staff_height_factor(get_glyph(cfg.STAFF_HEIGHT_REF_GLYPH, self.font)["top"])
        self._abstract_staff_height_bottom = self.y + scale_by_staff_height_factor(get_glyph(cfg.STAFF_HEIGHT_REF_GLYPH, self.font)["bottom"])
        self._abstract_staff_height = scale_by_staff_height_factor(get_glyph(cfg.STAFF_HEIGHT_REF_GLYPH, self.font)["height"])
        for c in self.content:
            c.x = self.x
            c.y = self.y            
        #
        self.REF_GLYPH_HEIGHT = scale_by_staff_height_factor(
            get_glyph(cfg.STAFF_HEIGHT_REF_GLYPH, self.font)["height"]
        )
    def current_ref_glyph_top(self):
        return self.y + scale_by_staff_height_factor(get_glyph(cfg.STAFF_HEIGHT_REF_GLYPH, self.font)["top"])

    def current_ref_glyph_bottom(self):
        return self.y + scale_by_staff_height_factor(get_glyph(cfg.STAFF_HEIGHT_REF_GLYPH, self.font)["bottom"])
    
    def delcont(self, test):    # name: del_content_if
        for i, c in enumerate(self.content):
            if test(c): del self.content[i]
    
    def refresh_horizontals(self):
        self._left = self.query_left()
        self._right = self.query_right()
        self._width = self.query_width()

    def refresh_verticals(self):
        self._top = self.query_top()
        self._bottom = self.query_bottom()
        # querying the height must happen after refreshing top and bottom
        self._height = self.query_height()
    
    def _establish_parent_relation(self, obj_list):
        """Establishes parental relationships to each obj in obj_list:
        adds this object and all it's parents to the ancestors list of
        new objects and their descendants.

        """
        for obj in obj_list:
            for member in family_tree(obj):
                for parent in ([self] + list(reversed(self.ancestors))):
                    member.ancestors.insert(0, parent)
    
    # Children is a sequence. This method modifies only ancestor lists.
    def _establish_parental_relationship(self, children):
        for child in children:
            assert isinstance(child, _SMTObject), "Form can only contain MeObjs!"
            child.ancestors.insert(0, self)
            if isinstance(child, _Form):
                for desc in descendants(child, False):
                    desc.ancestors.insert(0, self)
            for anc in reversed(self.ancestors):
                child.ancestors.insert(0, anc)
                if isinstance(child, _Form):
                    for desc in descendants(child, False):
                        desc.ancestors.insert(0, anc)

    @_Canvas.x.setter
    def x(self, new_x):        
        if not self.x_locked:
            dx = new_x - self.x
            for member in family_tree(self):
                member._x += dx
                if isinstance(member, _Form): # Char doesn't have _left/_right
                    member._left += dx
                    member._right += dx
            # moving x might have had an impact on ancestor's height
            for anc in reversed(self.ancestors):
                anc.refresh_horizontals()

    @_Canvas.y.setter
    def y(self, new_y):
        if not self.y_locked:
            dy = new_y - self.y
            for member in family_tree(self): # member will be self too
                member._y += dy
                if isinstance(member, _Form): # Char doesn't have _top/_bottom
                    member._top += dy
                    member._bottom += dy
            # moving y might have had an impact on ancestor's width
            for anc in reversed(self.ancestors):
                anc.refresh_verticals()

    def query_left(self):
        """Determines the left-most of either: form's own x coordinate 
        or the left-most site of it's direct children."""
        return min([self.x] + [child.left for child in self.content])

    def query_right(self):
        if self._width_locked: # ,then right never changes!
            return self.left + self.width
        else:
            return max([self.x] + [child.right for child in self.content])

    def query_width(self):
        if self._width_locked:
            return self.width
        else:
            return self.right - self.left

    def query_top(self):
        """Returns the top-most of it's own staff height top or ..."""
        return min([self.current_ref_glyph_top()] + [child.top for child in self.content])
    
    def query_bottom(self):
        return max([self.current_ref_glyph_bottom()] + [child.bottom for child in self.content])
    
    def query_height(self):
        if self.height_locked:
            return self.height
        else:
            return self.bottom - self.top
    
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
        
    @property
    def left(self):
        return self._left

    @left.setter
    def left(self, new):
        self.x += (new - self.left)

    @property
    def right(self): return self._right

    @property
    def top(self):
        return self._top
    @top.setter
    def top(self, new):
        self.y += (new - self.top)

    @property
    def bottom(self): return self._bottom

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, new):
        if not self._width_locked:
            self._right = self.left + new
            self._width = new
            # self.right = self.left + new
            for A in reversed(self.ancestors):
                A.refresh_horizontals()

    @property
    def height(self): return self._height
    
    
    @right.setter
    def right(self, new): 
        self.x += (new - self.right)
    


class SForm(_Form):
        
    def __init__(self, **kwargs):
        _Form.__init__(self, **kwargs)
        self.canvas_color = SW.utils.rgb(0, 100, 0, "%")
        self.domain = kwargs.get("domain", "stacked")
        # Content may contain children with absolute x, so compute horizontals with respect to them.
        # See whats happening in _Form init with children without absx!
        self.refresh_horizontals()
        self.refresh_verticals()

    def lineup(self): pass
        
    # Sinnvoll nur in rule-application-time?!!!!!!!!!!!!!!!
    def extend_content(self, *children):
        """Extend_Contents new children to Form's content list."""
        self._establish_parental_relationship(children)
        for c in children:
            c.x = self.x
            c.y = self.y
        self.content.extend(children)
        # # Having set the content before would have caused assign_x to trigger computing horizontals for the Form,
        # # which would have been to early!????
        self.refresh_horizontals()
        self.refresh_verticals()
        for A in reversed(self.ancestors):
            if isinstance(A, _Form) and not isinstance(A, SForm):
                A.lineup()
            A.refresh_horizontals()
            A.refresh_verticals()


class HForm(_Form):

    def __init__(self, **kwargs):
        _Form.__init__(self, **kwargs)
        self.canvas_color = SW.utils.rgb(0, 0, 100, "%")
        self.domain = kwargs.get("domain", "horizontal")
        self.lineup()
        self.refresh_horizontals()
        self.refresh_verticals()
    
    def extend_content(self, *children):
        """Extend_Contents new children to Form's content list."""
        # self._establish_parental_relationship(children)
        self._establish_parent_relation(children)
        for new_obj in children:
            new_obj.x = self.x
            new_obj.y = self.y
        self.content.extend(children)
        # # Having set the content before would have caused assign_x to trigger computing horizontals for the Form,
        # # which would have been to early!????
        self.lineup()
        self.refresh_horizontals()
        self.refresh_verticals()
        for anc in reversed(self.ancestors):
            anc.lineup()
            anc.refresh_horizontals()
            anc.refresh_verticals()
            
    def lineup(self):
        for a, b in zip(self.content[:-1], self.content[1:]):            
            b.left = a.right

class VForm(_Form):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lineup()
        self.refresh_horizontals()
        self.refresh_verticals()
    
    def lineup(self):
        for a, b in zip(self.content[:-1], self.content[1:]):
            b.top = a.bottom
    
    def extend_content(self, *children):
        """Extend_Contents new children to Form's content list."""
        self._establish_parental_relationship(children)
        # self._establish_parent_relation(children)
        for c in children:
            c.x = self.x
            c.y = self.y
        self.content.extend(children)
        # # Having set the content before would have caused assign_x to trigger computing horizontals for the Form,
        # # which would have been to early!????
        self.lineup()
        self.refresh_horizontals()
        self.refresh_verticals()
        for anc in reversed(self.ancestors):
            anc.lineup()
            anc.refresh_horizontals()
            anc.refresh_verticals()
        

class _LineSeg(_View):
    """Angle in degrees
    https://github.com/meerk40t/svgelements/issues/102
    """
    def __init__(self, length=None, direction=None,
                 thickness=None, angle=None, endxr=None, endyr=None,
    # start=None, end=None,
    **kwargs):
        super().__init__(**kwargs)
        self.length = length or 0
        self._angle = angle or 0
        self._thickness = thickness or 0
        self.direction = direction or 1
        self.endxr = endxr or 0
        self.endyr = endyr or 0

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
    
    @property
    def thickness(self):
        return self._thickness
    @thickness.setter
    def thickness(self, new):
        self._thickness = new
    
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
    # def query_height(self): return self.length
    # def query_bottom(self): return self.y + self.length
    # def query_top(self): return self.y
    # @_LineSeg.length.setter
    # def length(self, new):
        # self._length = new
        # self.refresh_verticals()
        # for a in reversed(self.ancestors):
            # a.refresh_verticals()

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
