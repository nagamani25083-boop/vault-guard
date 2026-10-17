# Overseas MeDo App Specification

## Screens

1. Decision input: question, candidate paths, constraints, success criteria, and optional context.
2. Normalized question: editable decision, facts, and assumptions.
3. Council run: four voice cards with idle, processing, succeeded, and failed states.
4. Raw positions: preserve all four independent outputs before synthesis.
5. Verdict: consensus, strongest dissent, premise check, recommendation, switch conditions, and next action.
6. History and export: enable only when requested; support Markdown copy or download.

## Model execution

- Load `large-language-model` during app generation.
- Execute four isolated calls. They may share the normalized question and minimum context but never one another's output.
- The synthesizer may read all raw outputs only after the four voices finish and must also receive the Architect's recorded initial position.
- Retry only a failed voice. Use finite timeouts and bounded retries.
- If the integration emits SSE, accumulate `candidates[0].content.parts[].text` before parsing structured output.

## Optional data

For history, use `decision_cases`, `council_runs`, `voice_outputs`, and `verdict_versions`, all scoped by `user_id` with RLS. Keep one-off sessions in frontend state.
