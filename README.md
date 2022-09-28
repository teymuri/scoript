# Satie

## Dependencies
- Python 3.5 or higher

## Thinking in Rules
### How to thinkg when I'm about to add new rules to a table
Generally how defining new rules happens is as follows:
  1. Understand what is the rule about, what is it it's doing, to which object it applies?
  2. Understand at which moment in the engraving process should the rule be applied (i.e. be added/unsafeadded to the rule table)
  3. Make a rule predicate func which returns true when called with some object as arg (this is called then on each obj in the score), to find out to which objs our rule should be applied.
  4. Make the actual engraving func which is applied to that object

## SVG measurements
are by default (if not correct them) in pixels only.

## Coordinate Movement of Objects
When you move an object's **y coordinate**
- **incrementing** (+) is to the **bottom**
- **decrementing** (-) is to the **top**

When moving an object's **x coordinate**
- **incrementing** (+) is to the **right**
- **decrementing** (-) is to the **left**

## API's Pitfalls (just for the record, some common mistakes I did while working with the API)
- When creating forms (e.g. a horizontal form), it's _origin_ (xy coord) is placed in the _middle_ of it's height. Moving the y for instance, of course moves the top and bottom of the whole form as well, which can end with wrong results if you set y by somehow referencing it's top/bottom. I did this mistake while replacing the hform of final bar in a rule: `obj.y = obj.current_ref_glyph_top() - StaffLines.THICKNESS * 0.5` in order to place the obj's (`FinalBarline`) thin and thick at once. This resulted in a longer hform.
