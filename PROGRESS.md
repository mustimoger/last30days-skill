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
  routing, supplemental lanes and paid accounting; merge and installation
  sync are the next steps.

## Provider setup and three-niche trial

Existing twitterapi.io and OpenAI keys are configured privately (mode 0600),
with the X backend pinned and all browser access disabled. No paid research
run has started. The private trial harness reserves conservative request costs
before transport, limits AI output to 4,096 tokens and stops at USD 1; its
output/input limits, reservation and stop-before-transport checks passed
without live calls. Research uses API keys and cookie-free sources.
Do not enable scheduled research, replace alert components or delete data as
part of this trial. Assess topic fit and added research value; a successful
research run does not establish minute-level breaking-news latency.
