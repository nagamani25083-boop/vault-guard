# Acceptance Cases
Record input, expected, actual, and pass/fail/not-tested for every case; never prefill passes. Run these when generating an app; their presence is not QA completion.
1. Solve from the start using only visible clues, recording calculations through the ending. Miniature expected chain: 472→312→26.
2. Empty, 47, and 4729 fail P1; 472 succeeds only once. Submitting 312 to P2 before P1 completes is rejected.
3. “ 472 ” succeeds only with declared trim normalization. Add a 007 code case: 007 succeeds, 7 fails.
4. Hints progress only to the final level and do not leak other puzzles. Reveal requires confirmation and a persistent label; assisted completion is not independent solving.
5. Refresh restores solved IDs, hints, and the same deadline. A new run gets a new runId without old progress. Corrupt saves offer recovery rather than a blank screen.
6. Reject drafts with missing references, dependency cycles, unreachable endings, or future-clue requirements and identify the defect. Valid branches merge according to all/any policies.
7. Check first load, deep-link refresh, narrow screens, keyboard interaction, repeated clicks, expiry, and untimed mode.
8. When composing a model: real request→parse→valid draft→save→play. Also test interruption, invalid structure, and incorrect solutions; preserve the old game and end loading.
9. For trusted competition, inspect responses/client assets for answer leakage and reject out-of-order submissions server-side. Label local-only games as not offering anti-cheat guarantees.
10. Report structure checks, logical walkthrough, build, browser testing, and platform QA separately; mark unexecuted stages not tested.
