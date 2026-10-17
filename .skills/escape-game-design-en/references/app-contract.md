# Web Application Contract
## Data and Publication
Puzzle fields: id,title,requires[],requireMode(all/any),clues[],answerSpec{type,accepted[],trim,caseInsensitive},hints[],reward,solution. Game fields: gameId,version,startIds[],finalIds[],durationSeconds(nullable). IDs and references must be unique and valid. All prerequisites is the default; any must be explicit. Publish only an acyclic graph completable from its starts.
Session fields: gameId,version,runId,solvedIds[],revealedIds[],hintLevels{},startedAt,deadline(nullable),status. Save per-puzzle hint levels. Namespace local storage by APP_ID. Validate fields and version on restoration; offer a new run for incompatible versions rather than silently mixing data.
## State and Grading
- Puzzle states: locked→available→solved; record revealed separately. If revealing permits progression, explicitly count it as assisted completion and label the ending; do not insert it into independently solved answers.
- Check availability before grading. Normalize according to answerSpec and compare full strings with accepted values. Store digit codes as strings, preserving leading zeros; no parseInt or includes. Wrong answers retain input, display feedback, and grant no reward.
- Correct resubmissions are idempotent; repeated clicks never duplicate rewards. Restart clears only this run's namespace, not other project data.
- deadline = startedAt + duration. Recompute remaining time from the clock after refresh, never component mount time. Do not force timers; declare whether practice may continue after expiry.
- Complete only after all finalIds are resolved, or an explicitly designed alternative ending. Save state before displaying results and debrief.
## Answer Isolation and Dependencies
Fixed solo play needs neither mandatory accounts nor a backend. Technical users can inspect a local bundle; do not promise secrecy. Trusted competition requires server-held answers and sessions; send only unlocked clues, not a full answer payload hidden by UI.
For dynamic generation/hosting, compose the regional model skill specified in the entrypoint and use its actual implementation. Validate generated schemas, solutions, and dependencies before freezing a published version. Reject invalid drafts without deleting the old game. Keep grading and unlocking deterministic; model explanations never override decisions. Preserve input and prior content on request failures; show error/retry rather than fabricated fallback results.
## Minimum Playable UI
Briefing→investigate clues→submit→progressive hints/confirmed reveal→unlock→ending. Show progress, feedback, save state, and restart. Locked puzzles expose neither clues nor submission. Provide keyboard operation, readable text, textual equivalents for color clues, and narrow-screen layouts. Do not force generated media or 3D.
Follow platform routing and deployment requirements; do not add CSP meta. Actually check first load, deep-link refresh, and saved-state restoration. A passing build is not a playthrough.
