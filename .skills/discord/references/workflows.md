# Workflows

Complete examples for each Discord feature. Read the whole file once, then adapt the sections the app needs; each assumes [building-blocks.md](building-blocks.md). It contains, in order:

- **Owner settings and channel lookup**
  - `discord_setup`: an administrator picks the server and channel (apps with sign-in).
  - `discord_channel_lookup`: find a channel ID while building (apps without sign-in).
- **Public announcements board**: `discord_announcements` shows one fixed channel's latest messages.
- **Booking or order alert**: the browser snippet and `notify_booking_on_discord`, which posts each new record once.

## Owner settings and channel lookup

Two ways to fix which channel a function uses: an administrator picks it in the app (apps with login), or you find its ID while building (apps without login). Set up the administrator role from [building-blocks.md](building-blocks.md#administrator-role-apps-with-login) first; the settings function relies on it.

### Owner picks the channel (apps with login)

The owner chooses which server and channel receive alerts. This function lists the servers the bot has joined and each server's text channels. It is for administrators only: channel names and topics can be internal.

```ts
// discord_setup/index.ts
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { DiscordError, isTextChannel, listChannels, listServers } from "../_shared/discord.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });
  if (req.method !== "POST") return json({ error: { code: "METHOD_NOT_ALLOWED" } }, 405);
  try {
    const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
    const jwt = req.headers.get("Authorization")?.replace("Bearer ", "") ?? "";
    const { data: { user } } = await supabase.auth.getUser(jwt);
    if (!user || user.is_anonymous) return json({ error: { code: "LOGIN_REQUIRED" } }, 401);
    const { data: profile } = await supabase.from("profiles").select("role").eq("id", user.id).maybeSingle();
    if (profile?.role !== "admin") return json({ error: { code: "FORBIDDEN" } }, 403);

    const servers = await listServers();
    const result = [];
    for (const server of servers) {
      const channels = (await listChannels(server.serverId)).filter(isTextChannel);
      result.push({ ...server, channels: channels.map(({ channelId, name }) => ({ channelId, name })) });
    }
    return json({ servers: result });
  } catch (error) {
    if (error instanceof DiscordError) return json({ error: { code: error.code, message: error.message } }, error.status);
    console.error(JSON.stringify({ discordSetupFailure: String(error) }));
    return json({ error: { code: "INTERNAL_ERROR" } }, 500);
  }
});
```

Store the chosen IDs as strings in an owner-only settings table (`discord_settings` with `server_id text`, `channel_id text`), written by an administrator-only function or policy. Show an empty server list as setup guidance: the bot has not been invited to a server yet.

Apps without login have no administrator screen. Ask the owner in chat which channel to use, find its ID with the lookup below, and write the channel ID into the function as a string constant.

### Look up channels while building

Only for finding a channel ID during generation, when your tools can call the app's deployed functions. It answers only callers that send the project's service role key, so visitors and browsers can never use it.

```ts
// discord_channel_lookup/index.ts
import { DiscordError, isTextChannel, listChannels, listServers } from "../_shared/discord.ts";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  const serviceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  if (!serviceKey || req.headers.get("Authorization") !== `Bearer ${serviceKey}`) {
    return json({ error: { code: "FORBIDDEN" } }, 403);
  }
  try {
    const servers = [];
    for (const server of await listServers()) {
      const channels = (await listChannels(server.serverId)).filter(isTextChannel);
      servers.push({ serverId: server.serverId, name: server.name,
        channels: channels.map(({ channelId, name }) => ({ channelId, name })) });
    }
    return json({ servers });
  } catch (error) {
    if (error instanceof DiscordError) return json({ error: { code: error.code, message: error.message } }, error.status);
    return json({ error: { code: "INTERNAL_ERROR" } }, 500);
  }
});
```

Call it with the service role key, match the channel name the owner gave, and never print the key.

## Public announcements board

Visitors see the latest messages of one channel. The function fixes the channel; the browser sends only an optional `beforeMessageId` for older messages.

```ts
// discord_announcements/index.ts
import { DiscordError, discordId, listMessages } from "../_shared/discord.ts";

// The owner chose this channel; keep it a string.
const ANNOUNCEMENTS_CHANNEL_ID = "1559556587130069024";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, "Content-Type": "application/json" } });

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });
  if (req.method !== "POST") return json({ error: { code: "METHOD_NOT_ALLOWED" } }, 405);
  try {
    const body = await req.json().catch(() => ({}));
    const before = body?.beforeMessageId === undefined ? undefined : discordId(body.beforeMessageId, "beforeMessageId");
    const { messages, contentHidden } = await listMessages(ANNOUNCEMENTS_CHANNEL_ID, { beforeMessageId: before, limit: 20 });
    return json({
      messages: messages.map((m) => ({
        messageId: m.messageId,
        author: m.author.globalName ?? m.author.username,
        content: m.content,
        timestamp: m.timestamp,
      })),
      contentHidden,
    });
  } catch (error) {
    if (error instanceof DiscordError) return json({ error: { code: error.code, message: error.message } }, error.status);
    console.error(JSON.stringify({ discordAnnouncementsFailure: String(error) }));
    return json({ error: { code: "INTERNAL_ERROR" } }, 500);
  }
});
```

Render message text as plain text, never as HTML. When `contentHidden` is true, members' messages arrive without text: show the owner a note to turn on **Message Content Intent** for the bot in the Discord Developer Portal, and show visitors only the messages that have text.

## Booking or order alert

Create the table and policies from [building-blocks.md](building-blocks.md#visitor-submissions-bookings-orders-contact-forms) first: visitors insert only, and the browser does not read the row back. The browser snippet uses `callDiscordFunction` from building-blocks.md.

The browser never sends a channel or finished message text. It sends the record ID after the record exists; the function reads the record with the service role, builds the message, posts once, and stores the Discord message ID so a repeated call does not post twice.

```ts
// Browser: no .select() after insert, because visitors cannot read bookings.
const bookingId = crypto.randomUUID();
const { error } = await supabase.from("bookings").insert({ id: bookingId, guest_name, room_name, check_in, nights });
if (!error) await callDiscordFunction("notify_booking_on_discord", { bookingId }).catch((e) => console.warn(e.code));
```

The browser cannot update `discord_message_id`; only the function writes it, with the service role. A failed alert must not fail the booking itself: show the booking as saved and log the alert failure. The function marks the record `sending` before posting; a record left at `sending` had an unknown result, so the owner checks the channel instead of the app posting again.

A contact or support form follows the same shape: save the submission first, then post a summary built from the saved row.

```ts
// notify_booking_on_discord/index.ts
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { DiscordError, sendMessage } from "../_shared/discord.ts";

const ALERT_CHANNEL_ID = "1559556587130069024";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, "Content-Type": "application/json" } });
// Visitor text goes into the message as data. A zero-width space after "<" breaks mention tags such as <@id>,
// so nobody is pinged by it, while an ordinary "@" (as in an email address) stays readable.
const plain = (value: unknown, max = 200) =>
  String(value ?? "").replace(/\s+/g, " ").trim().slice(0, max).replace(/<(?=[@#])/g, "<\u200b");

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders });
  if (req.method !== "POST") return json({ error: { code: "METHOD_NOT_ALLOWED" } }, 405);
  try {
    const { bookingId } = await req.json().catch(() => ({}));
    if (typeof bookingId !== "string" || !bookingId) return json({ error: { code: "INVALID_ARGUMENTS" } }, 400);
    const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
    const { data: booking, error } = await supabase
      .from("bookings")
      .select("id, guest_name, room_name, check_in, nights, created_at, discord_message_id")
      .eq("id", bookingId)
      .maybeSingle();
    if (error) throw error;
    if (!booking) return json({ error: { code: "NOT_FOUND" } }, 404);
    if (booking.discord_message_id) return json({ notified: true });
    // Only fresh records: an old ID cannot be replayed to spam the channel.
    if (Date.now() - Date.parse(booking.created_at) > 10 * 60 * 1000) return json({ notified: false });

    const content = [
      `**New booking** — ${plain(booking.room_name, 80)}`,
      `Guest: ${plain(booking.guest_name, 80)}`,
      `Check-in: ${plain(booking.check_in, 20)} · ${Number(booking.nights) || 1} night(s)`,
    ].join("\n");
    // Claim the record before posting, so two concurrent calls cannot both post.
    const { data: claimed, error: claimError } = await supabase
      .from("bookings")
      .update({ discord_message_id: "sending" })
      .eq("id", booking.id)
      .is("discord_message_id", null)
      .select("id");
    if (claimError) throw claimError;
    if (!claimed?.length) return json({ notified: true });
    let sent;
    try {
      sent = await sendMessage(ALERT_CHANNEL_ID, content);
    } catch (sendError) {
      // Certainly not sent: release the claim so a later call can try again.
      // Unknown result (timeout, Discord 5xx, unreadable reply): keep "sending" rather than risk a second post.
      if (sendError instanceof DiscordError && sendError.notSent) {
        await supabase.from("bookings").update({ discord_message_id: null })
          .eq("id", booking.id).eq("discord_message_id", "sending");
      }
      throw sendError;
    }
    await supabase.from("bookings").update({ discord_message_id: sent.messageId })
      .eq("id", booking.id).eq("discord_message_id", "sending");
    return json({ notified: true });
  } catch (error) {
    if (error instanceof DiscordError) return json({ error: { code: error.code, message: error.message } }, error.status);
    console.error(JSON.stringify({ discordAlertFailure: String(error) }));
    return json({ error: { code: "INTERNAL_ERROR" } }, 500);
  }
});
```
