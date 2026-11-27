# Voiceover for agnost_walkthrough.mp4 (64 s, 1440x810, captions burned in, no audio)

Upload the MP4 to Loom (New video > Upload) or YouTube (unlisted). If you want your own voice on it, read these
lines as each caption appears; they are the same words as the captions.

0:00  I set up Agnost the way your customers do, and tested it.
0:07  On Pipecat, following your docs exactly, 5 of 10 tool calls can't be recovered.
0:12  The missing ones: end call and transfer tools, hang-ups, interruptions, and bots on Claude.
0:18  An 80-line observer sends each call as an execute_tool span. 10 of 10.
0:27  Why: Pipecat writes no span for a tool, and Agnost reads the next request. Sometimes there isn't one.
0:35  The fix needs no backend change, and the whole test runs in one command.
0:44  You got Agnost into Vercel's and Mastra's docs. OpenAI's list is next: 9 compatibility checks pass.
0:52  Plus 12 onboarding gaps, each with a fix ready, including 8 skill patches.
0:59  Happy to walk through all of it on our call. Nitesh

Re-record any time: python video/record.py (records the live pages, so it always shows the current site).
