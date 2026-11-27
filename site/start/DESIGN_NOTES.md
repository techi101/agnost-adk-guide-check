# /start design notes (rebuild, 27 Nov 2026)

User verdict on v1: "uninteresting, AI slop". v1 failures, named: three identical cards, stat tiles as the hero,
all-caps mono eyebrows, middle-dot meta strings, nothing from Agnost's world.

Reader: Shubham Palriwala, CEO of Agnost AI, opening a link from a YC thread, likely on a laptop, 10 seconds of attention.
Main interaction: flip one switch and see the tool calls his product misses appear.

References inspected (screenshots in tmp, 27 Nov):
- agnost.ai home (1440 px): white canvas inside a hairline frame, Instrument Serif 54 px headline, "Agnost Sans" body,
  DM Mono / Fragment Mono for product labels, violet accent, black solid primary button + dashed secondary button,
  hero visual = a conversation timeline of blocks labelled USER INPUT / TOOL CALL / AGENT OUTPUT.
- premium-web refs: Linear (real product screen as the hero visual), Stripe Press (editorial serif + small mono
  labels), Cursor (calm canvas, the product window carries the page).

Decisions:
1. Speak Agnost's visual language so the page feels like it belongs to them: Instrument Serif display, Instrument Sans
   body (closest open pairing to their sans), DM Mono only inside the trace visual, violet accent, hairline frame,
   their black/dashed button pair.
2. The hero visual IS the finding: a trace of the 9 test scenarios, drawn like Agnost's own timeline. A segmented switch
   "Your docs setup / With the fix" turns the missing tool-call blocks from dashed ghosts into recorded blocks; the
   counter moves 5/10 to 10/10. Auto-plays once; respects reduced motion. Data = channels/pipecat-test/results.json.
3. Below the hero, each proof gets a different form, not a card grid: the OpenAI evidence as a CI-style check run,
   the audit as an editorial numbered list, and "about me" as a short signed note.
