# OpenAI connection handoff — 2026-10-30

## What is prepared on PR #64

`openai-connection-check.yml` is a manual, protected-main-only workflow using the existing owner-approved `pulse-ai-paid` environment. It requires `PAID_AI_ENABLED=NO` both in the job condition and the runtime gate. Only the owner can start it. The gate validates the exact current run/attempt, environment approval and main provenance before the secret is available to the probe step. No write token permissions, artifact upload, reservation, model inference or publication are used.

The probe makes one fixed `GET https://api.openai.com/v1/models/gpt-6.1-sol` request. Redirects and retries are disabled; raw responses and exceptions are not logged. It reports absent/invalid secret, rejected authentication, missing permission/model access, rate/quota errors or network failure as distinct sanitized results. Success means model metadata was readable; it does not validate Responses permissions, billing balance, pricing or research output quality. A Models-read restriction can prevent this probe even if another API permission exists. No automatic model fallback is allowed.

Official endpoint: https://developers.openai.com/api/reference/resources/models/methods/retrieve

Scheduled analysis now requires a separate `PAID_AI_SCHEDULE_ENABLED=YES` in addition to the existing paid switch and environment approval. Leave the schedule variable unset/NO for a manual trial. No repository variables were enabled by this change. CI records these non-secret repository switch values and checks live GitHub evidence without accessing the OpenAI secret.

## Merge impact to review

PR #64 remains Draft and unmerged. Merging the whole PR includes its accumulated research/UI changes, not just this connection probe. The existing `pages.yml` runs on pushes to main and can collect, persist and deploy the updated site. It is therefore NOT a deployment-free merge. Approved research and target changes are not authorized by this connection step. Review the entire PR diff before explicitly authorizing merge/deployment.

## After explicit merge approval

1. Keep `PAID_AI_ENABLED=NO`; keep scheduled paid analysis unset/NO.
2. Dispatch **PULSE OpenAI — connection check only (no generation)** on main.
3. The owner reviews the exact commit/run and approves `pulse-ai-paid` in GitHub. Do not bypass the approval gate. A rerun is blocked; start a fresh dispatch if necessary.
4. Read the sanitized result. Never copy the secret into chat, logs, files or repository variables.
5. Only after separate spending authorization, verify current provider pricing/billing, review a specific queued source and estimate, enable the paid switch, dispatch one `run-one` and approve that run. Keep the schedule switch off and return the paid switch to NO after the trial. The result is an unapproved draft.

Budget code remains: $10 monthly goal, stop starting at $9, $1 estimated maximum per call; durable reservation before a paid request and holds for uncertain outcomes. These are application controls, not a provider hard billing cap. This change performs no live OpenAI authentication or paid request before merge.

## Current external verification limitation

The user's screenshot shows `OPENAI_API_KEY` saved under an environment restricted to main; the environment title was cropped. Browser runtime initialization fails, so the secret's exact environment cannot be independently re-verified here. GitHub never returns secret values. Do not mark live authentication as passed based only on a saved secret or offline tests.
