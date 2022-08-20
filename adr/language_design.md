



<!---
Decision record template by Michael Nygard

This is the template in [Documenting architecture decisions - Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

You can use [adr-tools] https://github.com/npryce/adr-tools for managing the ADR files.

In each ADR file, write these sections:
-->

# Title
Language Design

## Status
<!---
What is the status, such as proposed, accepted, rejected, deprecated, superseded, etc.?
-->

## Context
<!---
What is the issue that we're seeing that is motivating this decision or change?
-->
Should a new language be devised, or could needs be covered with json?

## Decision
<!---
What is the change that we're proposing and/or doing?
-->
Use JSON instead of devising something new.

## Consequences
<!---
What becomes easier or more difficult to do because of this change?
-->
- No design work invovled (only implementing the JSON-parsing part in Python)
- JSON is universal and easy to generate through any other language, i.e. can ea
sily write an interface for SMT for any language. 
- JSON covers inherently _all_ needs for describing a score (because it's syntax is near to XML)
