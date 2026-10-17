# Overseas MeDo App Specification
Screens: style profile, wardrobe grid, outfit builder, weekly calendar, capsule wardrobe, travel packing, shopping gaps, export/delete.
Image flow exposes uploading, analyzing, review, ready, and failed. Save tags only after confirmation. Generated visuals complete polling, preview, versioning, and download.
The default data layer uses `${VITE_APP_ID}:wardrobe:`-namespaced `localStorage` for garments, care state, outfits, weekly plans, capsules, and packing lists. Add Supabase only for explicit accounts or cross-device use.
Acceptance:
1. With five items, every outfit references only those five.
2. Laundry items are unavailable for next-day looks.
3. Deleting an item marks dependent outfits for repair.
4. Every packed item maps to a day or explicit backup purpose.
5. With anonymous sign-in disabled, account-free mode still catalogs, saves, generates, and restores; account mode accesses RLS data only after real sign-in.

## Authentication and data layer (required)
- Never call `signInAnonymously()` automatically inside shared API or CRUD initialization. Anonymous auth is valid only when the product explicitly chooses it, the target environment is verified to enable it, and the UI handles that session model.
- AuthProvider, sign-in UI, session restoration, UUID owner columns, and RLS must form one complete design. Do not comment out authentication components while retaining `owner_id uuid default auth.uid()` and authenticated-only policies, and do not use hidden anonymous login to compensate for missing sign-in UI.
- On `Anonymous sign-ins are disabled`, 4xx/422, or a missing session, end loading, show an actionable authentication error and retry path, and block identity-dependent table and Storage calls. Never present this failure as an empty wardrobe.
- Without an account requirement, remove authentication dependencies and use app-ID-namespaced local persistence. A media-upload feature must not force anonymous authentication onto the entire product unless that identity design is intentional and supported.

## Streamed model calls and outfit parsing (required)
1. An SSE consumer settles only after `[DONE]`, `reader.done`, or explicit failure. Await the reader loop or an equivalent completion Promise; starting recursive reads and returning immediately is invalid.
2. Assemble complete daily outfits, weekly plans, capsules, and packing lists before JSON/schema, owned-inventory, care-state, and context validation. Do not decide empty or end loading while streaming continues.
3. Distinguish HTTP/gateway failure, SSE interruption, JSON/schema failure, and valid candidates removed by constraints. Only the last case may display that available owned items cannot satisfy the requested outfit.
4. Throwing inside a callback does not reject the outer Promise. Acceptance covers JSON split across chunks, 4xx/5xx, interrupted streams, invalid JSON, and all candidates referencing unavailable items while preserving wardrobe data and user constraints.
