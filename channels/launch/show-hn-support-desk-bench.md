# Show HN draft: Support Desk Bench (for Agnost to post; nothing posted)

Why now (checked 27 Nov 2026): github.com/AgnostAI/support-desk-bench has 0 stars; the v1.0 dataset release
(13 MB, published 12 Nov) has 3 downloads; HN search finds no post about it. It's real, reproducible work that
hasn't been launched. Every number below is from the repo README.

## Title options (HN limit 80 characters; lengths measured)
1. Show HN: 400 real Wix support tickets, Claude vs. GPT, judged by Wix experts (76)
2. Show HN: Support Desk Bench, frontier models on 400 real support tickets (72)
3. Show HN: Claude resolved more tickets; GPT made 12x fewer unsupported claims (76)

(Option 1 is the safest: concrete, no claim of superiority. Option 3 gets clicks but invites "benchmark wars".)

## Link
https://github.com/AgnostAI/support-desk-bench

## First comment (post right after submitting)
Hi HN, we're Agnost (YC S26). We monitor AI agents in production, and we wanted to know which frontier model makes
the better support agent on real tickets, not synthetic ones. So we built a benchmark from real data.

Wix published 400 real customer tickets plus expert answers (WixQA, MIT). Each model plays Wix's support agent using
only the real help center (6,221 articles), a simulated customer replies, and every conversation is judged against
Wix's expert answer. 3 runs per model, plus one at "high" effort.

What surprised us:
- Claude Fable 5.2 resolved more tickets (97.1% vs 94.4%) and was more consistent (370 of 400 tickets fully resolved
  in all 3 runs vs 335).
- But it went beyond its sources in 8.3% of conversations; GPT-6 Astra did in 0.7%. GPT handed off to a human more
  (9.9% vs 3.0%) and cost less than half per resolved ticket ($0.080 vs $0.188).
- "High" reasoning effort didn't improve either model's resolution rate.

Everything is published: all 3,400 conversations, every tool call and judge verdict, and a script that regenerates
every table from the dataset. Standard library Python, no SDKs. You can add your own model or agent endpoint.

Caveats we know about: one company's tickets, a simulated customer, an LLM judge panel (with a tie-breaker) against
expert answers. Methodology and confidence intervals are in METHODOLOGY.md and RESULTS.md. Happy to answer questions,
and we'd love PRs adding models.

## Before posting (checklist)
- [ ] `scripts/reproduce.sh` and `tools/results.py dataset` run cleanly on a fresh clone (someone will try in minutes)
- [ ] README results table matches RESULTS.md exactly
- [ ] One founder free for 3 hours after posting to answer every comment
- [ ] Post Tuesday to Thursday, 8 to 10 AM US Pacific
- [ ] Do not ask anyone to upvote (HN penalises vote rings); share the link in your own channels after it's live

## What success looks like
Stars and dataset downloads in the first 48 hours, and inbound from teams running support agents. Those are exactly
Agnost's buyers, so add a line to the README: "Running a support agent in production? Agnost checks every real
conversation for the same failures this benchmark measures."
