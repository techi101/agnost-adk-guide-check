# Design notes

North star: cursor.com hero (premium-web refs/cursor.jpg). Taking only two things from it: an understated left-aligned headline, and a real product window framed on top of a textured backdrop. Second ref: linear.com for letting a real screen be the hero image.

The "product window" here is a trace viewer built in HTML from the real spans in `check/out/`, not a mock. It shows the two root spans side by side and where each field landed.

Tokens
- paper #EDF0EA (pale sage, not cream), ink #18201D, muted #5A6762, line #CCD4CE
- cobalt #2747C9 for "landed on the right span"
- wine #A3204F for "landed on the wrong span / missing"
- type: Bricolage Grotesque (display, opsz) + Geist (text); Geist Mono only inside code and span names

Principles
- One bold thing: the trace window. Everything else is quiet text and one table.
- No stat tiles, no eyebrows in caps, no numbered markers except the real run order.
- Left aligned, 68ch measure for prose.
- One motion: the window rises in on load. Reduced motion respected.
