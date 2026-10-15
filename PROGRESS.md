# Standalone last30days trial

Owner authorization (2026-10-14): configure existing providers, add
twitterapi.io support and run one bounded report for each approved niche:
AI agents/enterprise automation, developer automation/Codex, and B2B email
infrastructure. Paid-call allowance: USD 1 for the trial. Keep this work
independent of the live trend-news alert service.

## Adapter implementation

- Owned fork: `mustimoger/last30days-skill`; branch `feat/twitterapi-io`
  starts from current main, with the original project retained as `upstream`.
- Added an exclusive, opt-in X backend using the existing HTTP layer and tweet
  parser. Search, discovery and FROM/ABOUT lanes share it. Pagination, stopping,
  auth/payment errors and malformed responses remain observable; full post
  text and provider IDs are retained. Paid requests stay unknown rather than
  being represented as zero cost when the provider omits USD billing.
- Focused adapter, routing, accounting and secret-store tests passed. The
  full suite reached 84.45% coverage (81% required); existing instruction
  size and security-copy assertions exposed documentation constraints.
  The compact security text now retains the existing bearer/header contract,
  and those focused checks pass. The final full suite passed with 84.45%
  coverage. Review checked transport bounds, credential stores, exclusive
  routing, supplemental lanes and paid accounting. PR #1 is merged at
  `279bdba9a69fb81c4def98dad4199c96c795a971`; relevant regression checks passed
  on main, and the installed Codex copy matches 136 source files. The previous
  installed copy is retained for rollback.

## Provider setup and three-niche trial

Existing twitterapi.io and OpenAI keys are configured privately (mode 0600),
with the X backend pinned and all browser access disabled. The private trial
harness reserves conservative request costs
before transport, limits AI output to 4,096 tokens and stops at USD 1; its
output/input limits, reservation and stop-before-transport checks passed
without live calls. Three real reports then completed for September 14 through
October 14, 2026, using X, Reddit, Hacker News, GitHub and dev.to:

- Enterprise agents: 109 retained items, 73.1 seconds.
- Developer automation/Codex: 64 retained items, 84.8 seconds.
- B2B email infrastructure: 80 retained items, 59.3 seconds.

These counts are research evidence, not verified new stories. Direct Reddit
search was blocked with HTTP 403; the engine used its public Arctic Shift
archive/listing fallback. Codex and email X coverage was partial at the trial's
two-page limit. YouTube and ScrapeCreators platforms were not tested.

Forty twitterapi.io requests returned 412 tweets; six OpenAI calls reported
19,776 input and 6,854 output tokens. The published-rate estimate is USD
0.0814268 in total, or about USD 2.44 for the same three reports daily for
30 days, excluding host-agent/web usage and infrastructure. Invoiced USD
remains unknown; the accounting journal does not substitute this estimate.
The conservative reservation was USD 0.1909104, below the USD 1 allowance.

Nine subsequent host-web searches produced 15 source records, retained
separately from engine discoveries and appended to each raw Markdown report.
They verified that the Codex bridge project exists but its latest documented
release is July 20, outside the window. The recent Outlook filter-loosening
claim remains unverified by first-party announcements. A generic repository
root or a fresh discussion of old requirements is not a new development;
weakly related items grouped across platforms are not independent confirmation.

Decision: retain live alerts and use this skill for separate on-demand research.
Broad retrieval is useful, but promotions, commentary and event dates require
review before automatic reuse. No schedule, production connector, watched
account changes or alert replacement was enabled. B2.5/B2.8 in the companion
project remain open; the live service started today, so the 30-day reports
cannot establish comparative recall or alert latency. Private receipts,
plans, caches, journals and the full assessment are under
`/home/codex/.local/share/last30days-install/trial-20261014/`.

## Owner-requested GPT-6 Luna settings (2026-10-15)

The owner added a ScrapeCreators key and requested GPT-6 Luna for both planner
and reranker. Key presence is confirmed without printing its value; no
ScrapeCreators request or new research run is authorized by this settings step.

The existing OpenAI client always sent temperature=0. Current official guidance
requires an explicit reasoning setting for a compatible GPT-6 request. Added
optional reasoning-effort and output-token settings, preserving existing
non-reasoning payloads and rejecting invalid limits before transport. The
planned private setting is effort=none to preserve the previous workload role,
with the previous model's 32,768-token output ceiling retained explicitly.

The focused provider, configuration, endpoint/proxy, usage-accounting and
logging regression tests passed before and after merging PR #3 at
`698070425594267cb79eba23872789d8514187bd`. The installed Codex copy is synced
to that commit. Both private model pins now resolve to gpt-6-luna, with
effort=none and max_output_tokens=32768. Configuration was replaced atomically
with mode 0600; previous settings and the previous installed copy are retained
privately for rollback.

A read-only model lookup confirmed account access. One model-only JSON check
then passed using a temporary 64-token output cap: 17 input and nine output
tokens, one request and no retry. No research run or ScrapeCreators request
was made. No fallback occurred in that check. The complete package suite was
not rerun for this focused request/configuration change.

Activation evidence is retained under
`/home/codex/.local/share/last30days-install/backups/gpt6-luna-20261015T123756Z/`.
The three saved trial reports remain historical GPT-4.1 mini results, not
evaluations of GPT-6 Luna or the newly configured sources.
