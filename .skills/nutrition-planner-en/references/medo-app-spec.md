# Overseas MeDo App Specification
Screens: onboarding, Today, seven-day plan, grocery list, prep plan, weekly review, settings/export/delete.
State: idle → validating → generating → ready or failed. Partial retries preserve profile and locked meals.
Default to app-ID-namespaced `localStorage` for profiles, weekly plans, meals, food logs, and reviews so refresh and reopen restore data without registration. Add Supabase only for explicit accounts or cross-device history, with user_id RLS for real signed-in users.
Acceptance:
1. A peanut allergy excludes peanuts from meals and substitutions.
2. Swapping one dinner updates totals and groceries.
3. A saved week survives refresh.
4. Model failure preserves all inputs.
5. The production build survives initial entry, navigation, refresh, and reopening of every page without a route 404 or empty `#root`.
6. With anonymous sign-in disabled, account-free mode still completes profile, save, and refresh recovery; account mode provides a working sign-in flow and actionable authentication errors.


## Model capability binding and runtime contract (required)
1. This section applies only to an explicit app-generation request. Direct nutrition analysis, meal planning, review, and adjustment requests are answered by the business Skill without another model Skill. After confirming the requested artifact is an app, automatically invoke `@Large language Model`; do not require the user to name a model again.
2. The generation trace must confirm that the model Skill was loaded. Plain `@` text, a displayed model name, or stub code is not a binding.
3. Meal generation, single-meal replacement, and weekly reviews must use the official implementation supplied by that Skill. Do not call a vendor model endpoint directly or construct `Authorization: Bearer ${INTEGRATIONS_API_KEY}`.
4. A single-meal replacement sends only the target day and meal type, locked meals, remaining nutrition budget, and all hard constraints. It updates exactly one slot, then deterministic code recalculates daily/weekly totals and groceries. Never generate a full week and repeatedly overwrite one slot.
5. On failure, update the newly created record by its captured ID to `failed` while preserving profile inputs and locked meals. React async logic must not rely on stale closure state.
6. If any ingredient, seasoning, sauce, processed component, or substitution hits an allergen, reject the entire candidate meal and regenerate it. Do not make an unsafe meal appear safe by deleting the matched ingredient.
7. Nutrition values come from deterministic structured data or clearly labelled estimates; model output must not impersonate an authoritative food database.

### Streamed model calls and parsing (required)
1. An SSE consumer settles its Promise only after `[DONE]`, `reader.done`, or an explicit failure. Await a `while (true) { await reader.read() }` loop or an equivalent completion Promise; a recursive read started without awaiting completion is invalid.
2. Do not extract JSON, filter candidates, decide that results are empty, or end loading before the stream completes. Assemble the full text, remove optional code fences, parse and validate the schema, then apply allergy exclusions.
3. Distinguish HTTP/gateway failure, SSE read failure, JSON/schema failure, and a successfully parsed list that becomes empty after business filtering. Only the last case may display “no meals satisfy all constraints.”
4. Throwing inside an `onError` callback does not replace rejecting the outer Promise. Stream errors must reject into the recipe request and reach the page-level error handler.
5. Acceptance covers complete normal output, JSON split across chunks, upstream 4xx/5xx, interrupted streams, invalid JSON, and all candidates rejected by allergies. Every case ends loading, preserves inputs, and shows an accurate retryable state.

## Release routing and authentication contract (required)

### Routing
- Overseas MeDo static delivery uses `HashRouter` by default, with routes such as `/#/meals` and `/#/profile`. Do not combine `BrowserRouter` with `<Navigate to="/meals">` unless the deployed host has been verified to serve `index.html` for every deep route.
- Production acceptance covers first load at `/`, in-app navigation to every page, refresh on each target page, and reopening a copied URL. The response must serve the app HTML and `#root` must contain rendered UI.
- Routing and runtime errors use a visible Error Boundary with retry and return-home actions, not console-only logging.

### Data and authentication
- Account-free mode does not create Supabase tables, RLS, or anonymous-auth dependencies. Persist locally with keys prefixed by `${VITE_APP_ID}:nutrition:`.
- Add Supabase only for an explicit account or cross-device requirement. Verify the selected auth provider is enabled; never assume `signInAnonymously()` works.
- If anonymous auth is selected, verify a successful session before reading or writing tables that depend on `auth.uid()`. On 4xx/422, end loading immediately, show that anonymous sign-in is unavailable, and provide retry or a real sign-in path.
- Auth initialization uses `try/catch/finally`; network, CORS, auth, and query failures always end loading. Core pages must not depend on a missing user.
- RLS tables are written only by a real authenticated user. Do not continue database writes after authentication fails.

### Minimum release acceptance
1. Production build succeeds.
2. `/` renders a non-empty `#root`.
3. `/#/meals`, `/#/profile`, and other routes survive refresh and reopen.
4. Account-free mode completes profile → generate plan → save → refresh recovery.
5. If accounts are enabled, complete the same flow after real sign-in; sign-in failure is visible and retryable.
6. No unhandled browser exception and no page-route 404 in Network.
