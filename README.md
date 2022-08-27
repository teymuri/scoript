# Symbolic Music Typesetting

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
When you move an object's y coordinate
- upwards is decrementing (-)
- downwards is incrementing (+)

When moving an object's x coordinate
- to the right is ?
- to the left is ?
