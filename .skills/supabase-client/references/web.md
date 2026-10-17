# Supabase Frontend — Web (Vite + React)

## Environment Variables

- Prefix: `VITE_`
- Access: `import.meta.env.VITE_SUPABASE_URL` / `import.meta.env.VITE_SUPABASE_ANON_KEY`
- Written automatically into `.env` after `supabase_init`

## Type Definitions

- Define types in `@/types/types.ts` matching SQL schema
- When unsure whether a field exists, query the table structure first

## api.ts Coding Standards

- Use `.maybeSingle()` instead of `.single()`
- Always use `.order()` with `.limit()`
- When writing select queries, avoid `table_name(*)` — use `table_name!foreign_key_name` to explicitly specify relationships and prevent ambiguity
- Implement pagination for multiple results — **strictly prohibit** fetching all data without pagination
- **Prefer cursor-based pagination**
- Return arrays safely: `Array.isArray(data) ? data : []`
- Empty strings need to be converted to NULL to prevent SQL formatting misalignment
- Prefer `.insert()` without `.select()`
- Protect nulls: `meeting.participants?.length`, `meeting.title || 'Untitled'`
- Use Supabase Realtime for real-time data updates instead of polling

## Storage Upload (Frontend)

- Create for image/file uploads only
- **NEVER** store images/videos as Base64 in database
- Frontend validation: 1MB limit
- **Filenames MUST be hex-encoded before upload.** Supabase Storage rejects non-ASCII object keys, so a raw Chinese (or any non-ASCII) filename fails. Hex encoding (UTF-8 bytes → lowercase hex) yields a pure `[0-9a-f]` key, which is always accepted — unlike `encodeURIComponent`, whose `%` escapes are themselves re-encoded/normalized along the request path and break round-tripping. Encode the filename **stem** only; keep the extension so `contentType` and previews still work, and never touch the `/` separators.
- Web: upload directly using `File` / `Blob`:

```ts
const toHex = (s: string) =>
  Array.from(new TextEncoder().encode(s), (b) => b.toString(16).padStart(2, '0')).join('');
const fromHex = (h: string) =>
  new TextDecoder().decode(Uint8Array.from(h.match(/../g) ?? [], (x) => parseInt(x, 16)));

// encode the stem only, NOT the whole path
const dot = file.name.lastIndexOf('.');
const stem = dot > 0 ? file.name.slice(0, dot) : file.name;
const ext = dot > 0 ? file.name.slice(dot) : '';
const safeName = `${toHex(stem)}${ext}`; // "报表.jpg" -> "e68aa5e8a1a8.jpg"

const { data, error } = await supabase.storage
  .from(bucket)
  .upload(`${userId}/${safeName}`, file, { contentType: file.type });

const { data: urlData } = supabase.storage.from(bucket).getPublicUrl(data.path);
// Store urlData.publicUrl in database
```

- `data.path` comes back still hex-encoded. Pass it to `getPublicUrl` as-is; use `fromHex` on the stem only when displaying the original name to a user. Keep the original filename in a DB column if you need it for display — decoding is then optional.

### Image display — default to thumbnails

Images MUST be rendered via a resized transform, not the full-size original, so lists and grids load fast. Use the `transform` option on `getPublicUrl`:

```ts
const { data } = supabase.storage.from(bucket).getPublicUrl(path, {
  transform: { width: 400, height: 400, resize: 'cover', quality: 75 },
});
```

- Size the transform to the actual rendered box (list/grid/avatar), not the largest possible viewport.
- Request the original only where full resolution is genuinely needed — a detail view or download.
- Store the plain path or public URL in the database; apply the transform at render time so thumbnail sizes stay changeable without a data migration.

## Edge Function Invocation

- Always use `supabase.functions.invoke`, except when a non-standard or custom Content-Type is required
- Read `error.context.text()` for the real error message
- For GET requests with parameters, append query parameters directly to the function name: `supabase.functions.invoke('test-fn?id=123', { method: 'GET' })`

```ts
// Type signature
supabase.functions.invoke<T = any>(
  functionName: string,
  options?: {
    body?: any
    headers?: Record<string, string>
    method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
    signal?: AbortSignal
  }
): Promise<{
  data: T | null
  error: FunctionsHttpError | null // Read error.context.text() for real message
}>

const { data, error } = await supabase.functions.invoke('hello_world', {
  body: { key: 'value' },
  method: 'POST',
});

if (error) {
  const errorMsg = await error?.context?.text();
  console.error("edge function error in <hello_world>:", errorMsg || error?.message);
}
```

## Realtime Subscription (low-frequency feature)

Use only when realtime capability is genuinely needed. Full spec (server-side publication switch, subscription template, per-stack differences) is in `supabase-server/references/realtime.md`.

## Auth

For login/signup/OAuth/SSO implementation, follow the `login` skill — **MUST** call `skill_action(skill="login")` to get the latest spec.
