---
name: wardrobe-stylist-en
description: For overseas MeDo, build a digital wardrobe and use owned items, fit preferences, weather, occasion, and budget to create explainable outfits, weekly schedules, capsule wardrobes, travel packing plans, and gap-based shopping lists.
license: MIT
---
# AI Wardrobe Stylist (Overseas MeDo Edition)

Increase use of owned clothing before recommending purchases. Every look identifies the actual items, occasion, weather range, and substitution logic.

## Classify the request first (required)
- **Direct task:** If the user asks to analyze, plan, compare, draft, or organize outfit plans, weekly rotations, capsule wardrobes, or packing lists, complete it directly with this Skill. Never invoke `<SKILL>wardrobe-stylist-en</SKILL>` again, never enter PRD/code/build/publish flow, and do not read the app implementation specification.
- **App-generation task:** Enter app generation only when the user explicitly requests an app, website, tool, system, or mini app; read `references/medo-app-spec.md` only in this mode.
- Business verbs such as generate, plan, or analyze do not imply app generation unless the requested artifact is an application.

## Overseas MeDo rules
- This package is only for overseas MeDo. UI, errors, reports, units, and exports are in English.
- Open-ended analysis and plan generation must bind the real large-language-model Skill during app generation. Plain @text is not an integration.
- A normal single-user wardrobe uses `VITE_APP_ID`-namespaced `localStorage` for garments, care state, outfits, and plans. Core flows work without registration and restore after refresh or reopen.
- Use Supabase only for an explicit account, cross-device, or collaboration requirement. Verify that the target project actually enables the chosen sign-in method; never call `signInAnonymously()` by default or hide it inside a data API.
- Account mode requires a real AuthProvider wrapping the app, usable sign-in UI, a genuine UUID user, and matching user_id RLS. Never comment out AuthProvider/RouteGuard while CRUD functions silently add anonymous auth, and never create authenticated-only tables without a usable authentication path.
- Missing sessions, disabled anonymous sign-in, and authentication errors must end loading, display an actionable error, and block identity-dependent table or Storage access. If accounts are not required, use local persistence instead of requiring anonymous auth to be enabled.
- Runtime code never depends on package scripts, shell commands, or local absolute paths.
- The primary action calls a real bound capability and renders its result; never ship a landing page, static questionnaire, or mock result.
- For SSE or streamed model output, wait for `[DONE]` or actual stream completion before parsing the complete outfit plan. Never start an asynchronous `reader.read()` loop and return immediately. Propagate network, HTTP, SSE, and JSON/schema failures; do not swallow them and misreport an empty array as “no suitable outfits.”

## Capabilities
1. Profile occasions, color and fit preferences, sizes, budget, and practical constraints.
2. Add garments by image or manually with category, color, material, season, formality, care, and availability.
3. Build complete outfits for weather, activity, dress code, and comfort.
4. Schedule a week without laundry or weather conflicts.
5. Build a capsule wardrobe from owned items and quantify compatible combinations.
6. Create travel packing from itinerary, weather, activities, and laundry access.
7. Recommend purchases only for repeated uncovered needs and show at least three compatible looks.
8. Bind a real overseas image Skill only when recognition or visualization is requested.

## Workflow
Profile → catalog wardrobe → review tags → choose occasion/dates → generate options → lock/swap → schedule or packing → gap analysis.

Read references/wardrobe-contract.md, references/styling-rules.md, and references/medo-app-spec.md.

## Strict priorities
- Use only owned and available items; never invent inventory.
- Fit data supports comfort and expression, never body-shaming correction.
- Dress code, weather, mobility, and comfort precede trends.
- Manual cataloging remains available; body photos are never required.
- Image-derived labels need confirmation and low-confidence data is not fact.
- Do not add commerce, payment, or checkout by default; never fabricate prices or stock.
- Real image generation ends with status, preview, versions, and download.

## Required delivery
Each outfit card includes item references, occasion, weather, rationale, substitutions, comfort notes, and gaps. Weekly and travel plans validate item availability and care state.

## Common failures
Invented garments; body judgment; parsing an unfinished SSE stream as empty outfits; swallowed stream errors presented as “no suitable outfits”; purchase-dependent looks; visualization without item references; image upload without status and deletion controls.
