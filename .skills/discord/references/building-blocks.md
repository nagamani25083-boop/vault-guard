# Building blocks

Read this whole file before writing any Discord function, page, table or policy. It contains, in order:

- **Access control**
  - Administrator role: use the login setup's roles and check that nobody can change their own role. Needed for any app with sign-in.
  - Visitor submissions: policies for bookings, orders and contact forms, where visitors insert but cannot read or change rows.
- **Shared helpers**
  - Function helpers: CORS headers, JSON responses and how to turn a `DiscordError` into a response. Every function uses them.
  - Browser helper: `callDiscordFunction`, which shows setup guidance instead of a generic error. Every page that calls a function uses it.

## Access control

### Administrator role (apps with login)

Use the roles the login setup creates in its roles/admin step: `profiles.role` (`user_role` enum), an administrator account created while building, and profile policies under which users edit their own row except `role`. Do not write a second role table, role column or trigger on `auth.users`; if the app already has its own roles, use its administrator role. Later sign-ups are ordinary users. Tell the owner in your closing summary which account is the administrator (the login setup's finish summary gives its credentials).

Check the profile policies after the login setup's roles/admin step has created them:

```sql
select policyname, cmd, roles, qual, with_check from pg_policies
where schemaname = 'public' and tablename = 'profiles';
```

Ordinary users have no INSERT policy, and every UPDATE policy they match keeps `role` unchanged, as in `with check (role is not distinct from get_user_role(auth.uid()))`; `pg_policies` shows it as `NOT (role IS DISTINCT FROM get_user_role(auth.uid()))`. The login setup's administrator-only ALL policy is fine. `auth.uid() = id` alone fails: a user could make themselves an administrator and use every Discord function. A `role` default of `'admin'` fails too. Fix it with a migration and check again.

The Discord functions check this role on every call, as in [workflows.md](workflows.md#owner-picks-the-channel-apps-with-login). A signed-in account without the role gets `403 FORBIDDEN`; no session gets `401 LOGIN_REQUIRED`.

### Visitor submissions (bookings, orders, contact forms)

Add `discord_message_id text` to the record table; only the alert function writes it. Visitors may insert a booking but cannot read, change or delete bookings, so the browser creates the ID itself and does not read the row back:

```sql
alter table public.bookings enable row level security;
drop policy if exists "visitors add bookings" on public.bookings;
create policy "visitors add bookings" on public.bookings for insert to anon, authenticated
  with check (discord_message_id is null);
-- No select, update or delete policy for visitors: drop any existing policy that lets them read or change bookings.
```

Only when the app has an administrator screen for bookings, add a read policy that reuses the `profiles.role` check, never `using (true)`:

```sql
drop policy if exists "admins read bookings" on public.bookings;
create policy "admins read bookings" on public.bookings for select to authenticated
  using (exists (select 1 from public.profiles where id = (select auth.uid()) and role = 'admin'));
```

If signed-in customers have a "my bookings" page, add a select policy limited to their own rows (`user_id = (select auth.uid())`) and make the insert check also require `user_id is null or user_id = (select auth.uid())`. Never `using (true)` or `using (id is not null)`: either lets anyone read every submission.

## Shared helpers

Every Discord call runs in a Supabase Edge Function with the shared helper [discord-client.ts](discord-client.ts) copied to `supabase/functions/_shared/discord.ts`. Browser code calls these functions and never sees `DISCORD_BOT_TOKEN`, a Discord URL, or a raw Discord response.

Adapt the examples in this file and in [workflows.md](workflows.md) to the app: rename tables and columns, keep the checks. Each browser-facing function answers CORS from any origin and resolves the caller itself; the platform also requires a Supabase key on every call, which `supabase.functions.invoke` sends.

### Function helpers

Each browser-facing example starts with the same CORS and response helpers; the build-time channel lookup is server-only and has none:

```ts
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, "Content-Type": "application/json" } });
```

Map a `DiscordError` to its `status` and `code` and send the browser only `{ error: { code, message } }`; the helper already logs Discord's status for the owner. Any other exception becomes `500 INTERNAL_ERROR` without details.

### Browser helper

On any non-2xx answer `supabase.functions.invoke` returns only a generic error, so the page would show "Edge Function returned a non-2xx status code" instead of the setup guidance. Browser code calls the functions through one helper that reads the code from the response:

```ts
// Browser
const DISCORD_GUIDANCE: Record<string, string> = {
  DISCORD_NOT_CONFIGURED: "Discord is not connected yet. The app owner saves the bot token in the app's Discord configuration.",
  DISCORD_TOKEN_INVALID: "The saved Discord bot token no longer works. The app owner resets it in the Discord Developer Portal and saves the new token.",
  DISCORD_FORBIDDEN: "The bot cannot use this channel. The app owner adds the bot to the server and gives it the missing permission.",
  LOGIN_REQUIRED: "Sign in as the app administrator to do this.",
  FORBIDDEN: "Only the app administrator can do this.",
};

async function callDiscordFunction<T>(name: string, body?: Record<string, unknown>): Promise<T> {
  const { data, error } = await supabase.functions.invoke(name, { body });
  if (!error) return data as T;
  let code = "INTERNAL_ERROR";
  let message = "";
  try {
    // error.context is the function's response; network failures have no JSON body.
    const payload = await error.context.json();
    code = payload?.error?.code ?? code;
    message = payload?.error?.message ?? "";
  } catch { /* keep INTERNAL_ERROR */ }
  throw Object.assign(new Error(DISCORD_GUIDANCE[code] ?? (message || "Something went wrong. Try again later.")), { code });
}
```

Show the thrown message where the feature would appear, and keep the rest of the page working.

A Supabase anonymous session counts as a visitor, not a signed-in user.
