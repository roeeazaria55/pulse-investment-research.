#!/usr/bin/env bash
# Publish settlement without replaying the API when collection advances pulse-data.
set -euo pipefail
state=$1
private=$2
for attempt in 1 2 3; do
  python3 scripts/pulse_ai_actions.py --phase settle --state-dir "$state" --private-dir "$private" > "$private/settlement.json"
  git -C "$state" add -- public/data/ai-analysis-queue.json public/data/ai-cost-ledger.json
  if test -f "$state/public/data/ai-research-drafts.json"; then
    git -C "$state" add -- public/data/ai-research-drafts.json
  fi
  git -C "$state" commit -m 'Record PULSE AI billing and pending analyst draft [skip ci]'
  commit=$(git -C "$state" rev-parse HEAD)
  if git -C "$state" push origin HEAD:pulse-data; then
    exit 0
  fi
  git -C "$state" fetch --no-tags origin refs/heads/pulse-data
  if git -C "$state" merge-base --is-ancestor "$commit" FETCH_HEAD; then
    exit 0
  fi
  # Replay settlement against fresh state. The Python transaction rechecks the
  # processing job, reservation and entire ledger before writing anything.
  if test "$attempt" -lt 3; then
    git -C "$state" reset --hard FETCH_HEAD
  fi
done
echo 'Settlement was not published. The remote reservation remains for recovery.' >&2
exit 1
