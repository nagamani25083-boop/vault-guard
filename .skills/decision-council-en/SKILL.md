---
name: decision-council-en
description: For overseas MeDo, convene four isolated decision voices for ambiguous choices, tradeoffs, and go/no-go calls, then synthesize visible disagreement into an actionable verdict. Use for second opinions and competing credible paths, not factual questions, code review, or obvious execution tasks.
license: MIT
---

# Decision Council (Overseas MeDo Edition)

Convene Architect, Skeptic, Pragmatist, and Critic perspectives for ambiguous decisions with no obvious winner. The value is not unanimity; it is making assumptions, tradeoffs, and disagreement legible before choosing.

## Prerequisites

- A static prompt cannot reproduce the source skill's independent opinions. When generating a MeDo application, load the real `large-language-model` Skill.
- Plain `@name` text does not bind an integration. The app-generation query or platform configuration must load the real Skill tag, and trajectory evidence must show the dependency.
- At runtime, issue four isolated model requests. Run them in parallel when supported; otherwise run sequentially without exposing earlier answers to later roles.
- Use Supabase only when users need accounts, cross-device history, team sharing, or decision tracking. Apply `user_id`-based RLS. Do not add a database to a one-off council.

## Scope

Use the council when:

- multiple credible paths exist with no obvious winner;
- the user wants explicit tradeoffs, dissent, or second opinions;
- conversational anchoring is a material risk;
- a go/no-go, scope, technical-direction, or resource-allocation decision needs adversarial challenge.

Do not use it for correctness verification, code or security review, detailed implementation planning, system architecture design, straight factual questions, or obvious execution work. Handle those requests directly instead of forcing a council.

## Voices

| Voice | Lens |
|---|---|
| Architect | correctness, maintainability, long-term implications, system integrity |
| Skeptic | framing challenge, assumption breaking, simplest credible alternative |
| Pragmatist | shipping speed, user impact, resource limits, operational reality |
| Critic | downside risk, edge cases, failure modes, irreversible cost |

Read [Role Contracts](references/role-contracts.md) for isolated prompts.

## Workflow

1. **Extract the real question:** state what is being decided, which constraints matter, and what success means. Ask at most one clarifying question only when the answer could change the available paths; otherwise state reasonable assumptions and proceed.
2. **Gather minimum context:** include only facts, metrics, snippets, and constraints that affect the decision. Do not pass the full conversation transcript to each voice.
3. **Form the Architect's initial position first:** record the position, its three strongest reasons, and its main risk before reading other voices, preventing majority mirroring.
4. **Run four isolated voices:** each request receives the normalized question, minimum context, and one role contract—never another voice's output. Each returns a position, three reasons, the biggest risk, and one surprise others may miss.
5. **Synthesize with bias guardrails:** explain why any view is rejected; state when another voice changed the recommendation; treat two or more voices opposing the initial position as a real signal; always preserve the strongest dissent.
6. **Deliver a compact verdict:** show the four raw positions first, followed by consensus, strongest dissent, premise check, recommendation, switch conditions, and next action.

One round is the default. For a second round, keep the new question narrow, include the previous verdict only when necessary, and preserve a clean Skeptic context as much as possible.

## Application requirements

When building a MeDo app, read [Overseas App Specification](references/medo-app-spec.md). The required flow is:

`Enter decision and constraints → normalize question → run four isolated voices → show raw positions → synthesize verdict → export/save`

Do not build four fixed text blocks or use one model response disguised as four independent voices. Show separate request states and outputs. If one voice fails, retry only that voice.

## Output

Use [Verdict Template](references/verdict-template.md). Keep it scannable on mobile, preserve disagreement, and do not invent numerical votes or confidence. Separate facts from assumptions and never fabricate evidence missing from the input.

## Persistence

Do not save by default. Persist only when the verdict changes a real project decision and the user requests it. Store the question, constraints, four raw outputs, verdict, version, and timestamp in the application or user-selected system—never in a hidden host path.

## Source and adaptation

Adapted from the MIT-licensed [ECC Council](https://github.com/gongyijie85/dsh-ecc/blob/HEAD/skills/council/SKILL.md). The source has no scripts, references, or assets; its core capability is role isolation plus bias-aware synthesis. This edition reproduces the subagent mechanism with four isolated model calls and adds MeDo application states, targeted retries, and optional user-isolated persistence. See `LICENSE`.
