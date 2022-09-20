<!---
Decision record template by Michael Nygard

This is the template in [Documenting architecture decisions - Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

You can use [adr-tools] https://github.com/npryce/adr-tools for managing the ADR files.

In each ADR file, write these sections:
-->

<!---
What is the issue that we're seeing that is motivating this decision or change?
-->
# Context
3 different svg libs are in use: svgwrite, svgelements and svgpathtools.

svgpathtools' scaled() method has a bug which deforms shapes. It offers however good bbox support.
svgelements has unreliable bbox functionality, but transformations seem to be more safe than in pathtools.
Bypass: apply transformations in svgelements and pass the d() to pathtools to get bboxes when needed.


<!---
What is the change that we're proposing and/or doing?
-->
# Decision


<!---
What becomes easier or more difficult to do because of this change? (Consequences)
-->
## Pros


## Cons


<!---
What is the status, such as proposed, accepted, rejected, deprecated, superseded, etc.?
-->
# Status
