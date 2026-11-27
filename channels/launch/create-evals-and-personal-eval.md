# Launch drafts: create-evals and personal-eval (for Agnost to post; nothing posted)

Checked 27 Nov 2026: github.com/AgnostAI/create-evals (created 30 Oct) and AgnostAI/personal-eval (created 23 Nov)
have 0 stars each; HN search finds no post for either. Claims below are from each README; the validation examples link
to create-evals' docs/validation.md, which readers will open, so keep it accurate before posting.

---

## 1. Show HN: create-evals

Title (79 chars, measured): Show HN: create-evals – turn the failures your AI agent actually has into tests

Link: https://github.com/AgnostAI/create-evals

First comment:
Guessed evals tend to pass and catch nothing, so we built the opposite. In your agent's repo, `npx create-evals`, then
`/create-evals` in Claude Code, Codex or Cursor. It runs your real agent on realistic multi-turn cases (outside calls
like payments and email go to a test account or an in-memory fake; other network requests are blocked), reviews every
run by comparing what the agent said with what it did, groups what broke, and you answer y/n per case. Each "yes"
becomes a plain TypeScript test that fails today.

On agents it had never seen, it found, among others:
- a booking agent that tells guests their real booking is fake, then books them again (only shows up on turn three)
- a support agent that forgets a refund it already made and pays $300 on a $150 request
- OpenAI's customer-service example seating a lap infant in an exit row
- LangChain's LangGraph workshop agent crashing on every request after identity verification

All nine are in docs/validation.md. Takes about 20 to 30 minutes and produces around 10 evals. Feedback welcome,
especially on agents where it found nothing.

Before posting: re-run the four headline examples on the current release; if any changed, update the comment.

---

## 2. personal-eval: X reply + Reddit

The README says it was inspired by a post from @rauchg (x.com/rauchg/status/2124880074168242369). The most natural
first audience is that thread.

X reply (under 280 chars, as Agnost's account):
Built the thing you described: `npx personal-eval` scores the models you actually use from your own Claude Code, Codex,
Gemini CLI and opencode sessions. Runs locally, nothing leaves your machine. github.com/AgnostAI/personal-eval

Reddit (r/ClaudeAI or r/ChatGPTCoding; read each sub's self-promotion rule first):
Title: I scored my own models from my Claude Code and Codex history instead of trusting benchmarks
Body: Benchmarks tell you which model is best on average; I wanted to know which is best for the way I work.
`npx personal-eval` reads your local coding-agent sessions (Claude Code, Codex, Gemini CLI, opencode, fx) and compares
your two most-used models on your own history. Nothing leaves your machine unless you pass `--judge`, which sends short
snippets to Claude to label follow-ups. `--strict` calls a tie unless the gap is statistically significant. One
caveat: if your models ran in different agents, harness differences are part of the result. Code:
github.com/AgnostAI/personal-eval (made by Agnost, where I work).

(Reddit communities expect the affiliation stated, as in the last line.)
