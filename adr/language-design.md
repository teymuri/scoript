<!---
Decision record template by Michael Nygard

This is the template in [Documenting architecture decisions - Michael Nygard](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions).

You can use [adr-tools] https://github.com/npryce/adr-tools for managing the ADR files.

In each ADR file, write these sections:
-->

# Context
<!---
What is the issue that we're seeing that is motivating this decision or change?
-->
Should a new language be devised, or could needs be covered with json?

# Decision
<!---
What is the change that we're proposing and/or doing?
-->
Use JSON instead of devising something new.


<!---
What becomes easier or more difficult to do because of this change?
## Consequences
-->
## Pros
- No design work will be invovled (only implementing the JSON-parsing part in Python).
- JSON is universal and easy to generate through any other language, i.e. can ea
sily write an interface for SMT for any language. 
- JSON covers inherently _most_ of the needs for describing a score (because it's syntax is near to XML).

## Cons
- I will be restricted to the syntax json provides, e.g. can't define variables, can't have loops etc. (the interface will be as static as json is).
- No chance for re-using parts, like having violins in one file, piano in another and import them in a third file to combine (the interface will not be modular).

# Status
<!---
What is the status, such as proposed, accepted, rejected, deprecated, superseded, etc.?
-->

Anderes Beispiel:
` 
1 Nc#;Nfb;
  2 Scnt:(Vcnt:(Nnm:c#,xo:-3.14,hdc:red;Npc:60;);Vcnt:(Nnm:c##4,;));
  3 
  4 S
  5     cnt: (
  6         V
  7             cnt: (
  8 
  9             )
 10     )
 11 
 12 sf cnt:(vo cnt:(no nm: getname N nm:c#4;))
 13 stf cnt: (vc cnt: (nt nm: Getname n nm: c#4;, hdcl:blue;))
 14 obj k1:v1, kN:vN; obj2 k1:v1, kN:vN;
 15 DF my-c N nm: c4;
 16 DF my-list (1+2+3+4; 2; 3; 4);
 17 
 18 Dfn mylst sq 1; 2; 3; 4;
`
