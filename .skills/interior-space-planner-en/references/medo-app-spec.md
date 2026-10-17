# Overseas MeDo App Specification
Screens: project setup, plan/photo and dimensions, diagnosis, A/B/C comparison, room editor, budget/shopping, optional visualization, professional review/export.
Default data layer: app-ID-namespaced `localStorage` stores the project list, active project, workflow step, retained furniture, and locked options. Restore by project ID after refresh; React Context memory alone is insufficient.
If an image Skill is bound, implement submit → poll → succeeded/failed/timeout → URL or Base64 handling → Storage when needed → preview → download. Resume pending work after refresh; status retry never creates another billable task.
Acceptance:
1. Dimension changes update conflicts.
2. Structural walls never enter removal suggestions.
3. Locked retained furniture survives partial regeneration.
4. Without an image Skill, layout and prompts remain complete without claiming a render.
5. The production build survives initial entry, in-app navigation, refresh, and reopening of every deep link without a route 404 or empty `#root`.
6. Account-free mode creates, saves, and restores a project; account mode writes UUID-owned rows only after real sign-in.

## Streamed model calls and plan parsing (required)
1. An SSE consumer settles only after `[DONE]`, `reader.done`, or explicit failure. Await the reader loop or an equivalent completion Promise; starting recursive reads and returning immediately is invalid.
2. Assemble the complete diagnosis, layout candidates, and room specifications before JSON/schema, dimension, and locked-decision validation. Do not decide empty, end loading, or show completion while streaming continues.
3. Distinguish HTTP/gateway failure, SSE interruption, JSON/schema failure, and a valid result removed by hard constraints. Only the last case may display “no plan satisfies all constraints.”
4. Throwing inside a callback does not reject the outer Promise. Acceptance covers JSON split across chunks, 4xx/5xx, interrupted streams, invalid JSON, and all options failing hard constraints while preserving project inputs and locked decisions.

## Release routing, project recovery, and authentication (required)
- Overseas MeDo static delivery uses `HashRouter` by default, with `/#/input`, `/#/diagnosis`, `/#/compare`, `/#/detail`, and `/#/adjust`. Use `BrowserRouter` only after verifying that the deployed host serves `index.html` for every deep route.
- For every page, test in-app navigation, refresh, and a copied URL reopened in a new session. Network must not return a page-route 404 and `#root` must contain rendered UI.
- `ProjectContext` is not the sole data source. Restore the active project from persisted currentProjectId during initialization; if it no longer exists, show an actionable message and return to the project list.
- Account-free mode uses local persistence and does not create owner_id, RLS, or Auth dependencies.
- Add Supabase only for explicit account/cross-device requirements. The real AuthProvider wraps the app, sign-in UI works, and a genuine UUID user exists before writing `owner_id uuid`.
- Never use a public anon-token `sub: "anon"` as a UUID. PostgreSQL `22P02`, `invalid input syntax for type uuid: "anon"`, or project-creation 4xx is a blocking authentication/type mismatch.
- Every loading flow uses `try/catch/finally`; authentication, network, RLS, and query failures end loading and expose an error plus retry.
