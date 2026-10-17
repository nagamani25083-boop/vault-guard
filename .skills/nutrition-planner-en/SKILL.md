---
name: nutrition-planner-en
description: For overseas MeDo, turn goals, dietary preferences, allergies, budget, and schedule into transparent nutrition targets, an editable weekly meal plan, prep workflow, grocery list, and review loop. For everyday planning, not diagnosis or treatment.
license: MIT
---
# Nutrition Planner (Overseas MeDo Edition)

Turn healthy-eating goals into an executable household plan. Deterministic code owns calculations; the model composes meals within confirmed constraints.

## Classify the request first (required)
- **Direct task:** If the user asks to analyze food logs, create an adjustment plan, draft meals, replace one meal, compile groceries, or review adherence barriers, complete the task directly with this Skill. Do not invoke `@Large language Model`; the current conversational model already performs the reasoning and writing.
- A direct task never invokes this Skill again, never enters app generation, and does not read `references/medo-app-spec.md`; return the requested plan, list, or analysis directly.
- **App-generation task:** Invoke the platform model Skill only when the user explicitly asks to create, build, or develop an app, website, page, tool, system, dashboard, or mini app, or explicitly asks to integrate this capability into an application.
- Words such as “generate,” “create,” “analyze,” or “plan” do not by themselves indicate app generation. The requested deliverable must be an application-type artifact.

## Capability composition for app generation
- After classifying the request as app generation, the agent must automatically invoke `@Large language Model` during generation. That platform Skill owns runtime meal ideation, substitutions, open-ended analysis, and weekly-review copy; the user must not be asked to select the model again.
- This must be a real MeDo Skill invocation/dependency visible in the generation trace. Mentioning “@Large language Model” in prose, UI copy, comments, or source code is not a capability binding.
- The generated app must reuse the official runtime implementation and credential injection supplied by `@Large language Model`. Do not call a vendor model HTTP endpoint directly, treat `INTEGRATIONS_API_KEY` as a vendor Bearer key, or invent a model-proxy Edge Function.
- If the exact display name is unavailable, inspect the current overseas MeDo Skill catalog and select the platform-provided English large-language-model Skill. Never guess an endpoint, environment variable, or authentication header.
- Deterministic code owns BMR/TDEE, nutrition totals, quantity aggregation, and validation. The model Skill owns open-ended content. Both are required in an app; model output must not replace deterministic arithmetic.

## Overseas MeDo rules
- This package is only for overseas MeDo. UI, errors, reports, units, and exports are in English.
- Complete direct tasks with this Skill; compose `@Large language Model` only for app-generation requests under the routing rules above.
- Web apps use `HashRouter` by default. Do not use `BrowserRouter` to expose `/meals`, `/profile`, or other server paths unless the deployed host is verified to provide SPA fallback for every deep link.
- A single-user app stores profiles, meal plans, logs, and adjustments in app-ID-namespaced `localStorage` by default, restoring them after refresh and reopen without forcing an account.
- Use Supabase only when the user explicitly needs accounts, cross-device history, or collaboration. Before integration, verify that the target MeDo project supports the selected sign-in method; never assume `signInAnonymously()` is enabled.
- If accounts are required, wire a real AuthProvider and usable sign-in UI into the app root, enforce user_id RLS for the actual signed-in user, and expose authentication failures plus retry. Auth failure must not leave the app blank or permanently loading.
- Runtime code never depends on package scripts, shell commands, or local absolute paths.
- The primary action calls a real bound capability and renders its result; never ship a landing page, static questionnaire, or mock result.
- For SSE or streamed model output, the request Promise must wait for `[DONE]` or actual stream completion before parsing the complete text and applying allergy filters. Never start an asynchronous `reader.read()` loop and return immediately. Propagate network, HTTP, SSE, and JSON errors to the caller; do not swallow them and misreport an empty array as “no suitable meals.”
- Before delivery, test the production build at `/`, navigate through every page, refresh and reopen each target route, and complete profile/save/restore. Deep-link 404, empty `#root`, or infinite loading fails acceptance.

## Capabilities
1. Profile goals, activity, household, dietary pattern, allergies, budget, equipment, schedule, locale, and units.
2. Calculate transparent energy and nutrient ranges with editable assumptions.
3. Produce a seven-day meal calendar with servings, estimates, substitutions, and ingredient reuse.
4. Deduplicate groceries by store section and create a batch-prep sequence.
5. Log actual meals, hunger, adherence, and barriers; adjust one or two variables per review.
6. Treat allergy, religious, and ethical restrictions as hard exclusions.

## Workflow
Profile → calculate and confirm targets → generate week → lock/swap meals → grocery and prep → daily log → weekly review.

Read references/nutrition-contract.md and references/medo-app-spec.md when building the app.

## Strict priorities
- User-provided clinician guidance, allergies, and exclusions override suggestions.
- Mark unsupported food values as estimates and show assumptions.
- Do not promote extreme deficits or treat weight as the sole health outcome.
- For minors, pregnancy, eating-disorder concerns, serious chronic conditions, or medication interactions, support tracking and clinician discussion instead of restrictive plans.
- Partial regeneration preserves locked meals and recalculates only affected totals.
- Do not bind image, Word, PDF, or spreadsheet Skills unless the requested product implements those features.

## Required delivery
Targets and assumptions, daily meals, servings, substitutions, weekly summary, grocery list, prep plan, cautions, and review date. Advice-only output is incomplete.

## Common failures
Model-only arithmetic; allergens returning through substitutions; parsing before an SSE stream finishes; swallowed stream errors presented as “no suitable meals”; mandatory sign-in for one-off use; pending calls shown as complete; losing inputs after failure; `BrowserRouter` deep-link 404s; assuming anonymous sign-in is enabled; authentication failure leaving the app permanently loading.
