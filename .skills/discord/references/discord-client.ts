// Copy to supabase/functions/_shared/discord.ts. Never import into browser code.
// Exports: DiscordError (code, status, notSent), discordId, listServers, listChannels, isTextChannel,
// listMessages, sendMessage, and discordApi for other bot endpoints. Call Discord only through these:
// they read DISCORD_BOT_TOKEN, keep it out of errors, and stop @everyone and @here from notifying anyone.
const DISCORD_API = "https://discord.com/api/v10";
const DISCORD_ID = /^[0-9]{15,25}$/;
const MAX_RESPONSE_BYTES = 1024 * 1024;

export class DiscordError extends Error {
    code: string;
    status: number;
    // true only when Discord certainly did not act: the request never left, or Discord refused it with a 4xx.
    // Timeouts, 5xx and unreadable replies leave a write's outcome unknown.
    notSent: boolean;
    constructor(code: string, status: number, message: string, notSent = false) {
        super(message);
        this.code = code;
        this.status = status;
        this.notSent = notSent;
    }
}

export type DiscordServer = { serverId: string; name: string; iconUrl: string | null };
export type DiscordChannel = {
    channelId: string;
    name: string;
    type: number;
    parentId: string | null;
    position: number;
    topic: string | null;
};
export type DiscordMessage = {
    messageId: string;
    content: string;
    timestamp: string;
    editedTimestamp: string | null;
    hasAttachments: boolean;
    hasEmbeds: boolean;
    author: { userId: string; username: string; globalName: string | null; bot: boolean };
};

// Discord IDs exceed Number.MAX_SAFE_INTEGER: accept and return them only as strings of digits.
export function discordId(value: unknown, name: string): string {
    if (typeof value !== "string" || !DISCORD_ID.test(value)) {
        throw new DiscordError("INVALID_ARGUMENTS", 400, `${name} must be a Discord ID as a string of digits`, true);
    }
    return value;
}

function botToken(): string {
    const token = Deno.env.get("DISCORD_BOT_TOKEN")?.trim();
    if (!token) {
        throw new DiscordError("DISCORD_NOT_CONFIGURED", 503,
            "Discord is not configured. Save the bot token in the app's Discord Skill configuration.", true);
    }
    return token;
}

async function discordRequest(path: string, init: { method?: string; body?: unknown } = {}): Promise<unknown> {
    let response: Response;
    try {
        response = await fetch(`${DISCORD_API}${path}`, {
            method: init.method ?? "GET",
            redirect: "error",
            headers: {
                Authorization: `Bot ${botToken()}`,
                "Content-Type": "application/json",
                "User-Agent": "DiscordBot (https://medo.dev, 1.0)",
            },
            body: init.body === undefined ? undefined : JSON.stringify(init.body),
            signal: AbortSignal.timeout(10000),
        });
    } catch (error) {
        if (error instanceof DiscordError) throw error;
        throw new DiscordError("DISCORD_UNAVAILABLE", 503, "Discord is temporarily unavailable. Try again later.");
    }
    const text = await response.text();
    if (text.length > MAX_RESPONSE_BYTES) {
        throw new DiscordError("DISCORD_INVALID_RESPONSE", 502, "Discord returned an unexpectedly large response.");
    }
    let body: unknown = null;
    try {
        body = text ? JSON.parse(text) : null;
    } catch {
        body = null;
    }
    if (response.ok) return body;
    const discordCode = typeof (body as { code?: unknown })?.code === "number" ? (body as { code: number }).code : null;
    // Server log only: Discord's error text can echo channel or message content.
    console.error(JSON.stringify({ discordFailure: { status: response.status, code: discordCode } }));
    if (response.status === 401) {
        throw new DiscordError("DISCORD_TOKEN_INVALID", 503,
            "The Discord bot token was rejected. Reset the token in the Discord Developer Portal and save it again.", true);
    }
    if (response.status === 403) {
        throw new DiscordError("DISCORD_FORBIDDEN", 403,
            "The bot lacks access or a permission for this action. Check that it is in the server and has the permission.", true);
    }
    if (response.status === 404) {
        throw new DiscordError("DISCORD_NOT_FOUND", 404, "The Discord server, channel or message was not found.", true);
    }
    if (response.status === 429) {
        throw new DiscordError("DISCORD_RATE_LIMITED", 429, "Discord is rate limiting this bot. Try again shortly.", true);
    }
    if (response.status >= 400 && response.status < 500) {
        throw new DiscordError("DISCORD_REJECTED", 400, "Discord rejected the request.", true);
    }
    throw new DiscordError("DISCORD_ERROR", 502, "Discord could not complete the request.");
}

const API_METHODS = new Set(["GET", "POST", "PATCH", "PUT", "DELETE"]);
const API_PATH = /^\/[A-Za-z0-9@%._~\/:-]*$/;
const API_QUERY = /^[A-Za-z0-9%._~=&,-]*$/;
const MENTION_RULES = { parse: ["users", "roles"] };

function carriesMessage(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value)
        && ("content" in value || "embeds" in value || "components" in value);
}

// Any other Discord REST call, e.g. discordApi("PATCH", `/channels/${channelId}/messages/${messageId}`, { content }).
// JSON bodies only. Pass every ID through discordId() and every emoji through encodeURIComponent before building the path.
// A body (or its nested `message`) that carries message content always gets sendMessage's mention rules.
export async function discordApi(method: string, path: string, body?: Record<string, unknown>): Promise<unknown> {
    const verb = typeof method === "string" ? method.toUpperCase() : "";
    if (!API_METHODS.has(verb)) {
        throw new DiscordError("INVALID_ARGUMENTS", 400, "method must be GET, POST, PATCH, PUT or DELETE", true);
    }
    // Reject encoded dots and slashes too: fetch resolves %2e%2e like "..", which would let an ID rewrite the route.
    const [route, query = "", extra] = typeof path === "string" ? path.split("?") : [];
    if (typeof route !== "string" || !API_PATH.test(route) || !API_QUERY.test(query) || extra !== undefined
        || route.includes("..") || /%2e|%2f|%5c/i.test(route)) {
        throw new DiscordError("INVALID_ARGUMENTS", 400, "path must be a Discord API path such as /channels/{id}", true);
    }
    if (body !== undefined && (body === null || typeof body !== "object" || Array.isArray(body))) {
        throw new DiscordError("INVALID_ARGUMENTS", 400, "body must be a JSON object", true);
    }
    if (body !== undefined && verb === "GET") {
        throw new DiscordError("INVALID_ARGUMENTS", 400, "GET requests take no body", true);
    }
    let payload = body;
    if (carriesMessage(payload)) payload = { ...payload, allowed_mentions: MENTION_RULES };
    // Forum and media posts nest the first message under `message`.
    if (payload && carriesMessage(payload.message)) {
        payload = { ...payload, message: { ...payload.message, allowed_mentions: MENTION_RULES } };
    }
    return discordRequest(path, { method: verb, body: payload });
}

export async function listServers(): Promise<DiscordServer[]> {
    const body = await discordRequest("/users/@me/guilds?limit=200");
    if (!Array.isArray(body)) throw new DiscordError("DISCORD_INVALID_RESPONSE", 502, "Unexpected Discord response.");
    return body.map((guild) => ({
        serverId: String(guild.id),
        name: String(guild.name),
        iconUrl: guild.icon ? `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png?size=128` : null,
    }));
}

export async function listChannels(serverId: string): Promise<DiscordChannel[]> {
    const body = await discordRequest(`/guilds/${discordId(serverId, "serverId")}/channels`);
    if (!Array.isArray(body)) throw new DiscordError("DISCORD_INVALID_RESPONSE", 502, "Unexpected Discord response.");
    return body
        .map((channel) => ({
            channelId: String(channel.id),
            name: String(channel.name),
            type: Number(channel.type),
            parentId: channel.parent_id ? String(channel.parent_id) : null,
            position: Number(channel.position ?? 0),
            topic: typeof channel.topic === "string" ? channel.topic : null,
        }))
        .sort((a, b) => a.position - b.position);
}

// Text (0) and announcement (5) channels accept messages.
export function isTextChannel(channel: DiscordChannel): boolean {
    return channel.type === 0 || channel.type === 5;
}

export async function listMessages(
    channelId: string,
    options: { beforeMessageId?: string; limit?: number } = {},
): Promise<{ messages: DiscordMessage[]; contentHidden: boolean }> {
    const limit = options.limit ?? 50;
    if (!Number.isInteger(limit) || limit < 1 || limit > 100) {
        throw new DiscordError("INVALID_ARGUMENTS", 400, "limit must be an integer from 1 to 100", true);
    }
    const query = new URLSearchParams({ limit: String(limit) });
    if (options.beforeMessageId !== undefined) query.set("before", discordId(options.beforeMessageId, "beforeMessageId"));
    const body = await discordRequest(`/channels/${discordId(channelId, "channelId")}/messages?${query}`);
    if (!Array.isArray(body)) throw new DiscordError("DISCORD_INVALID_RESPONSE", 502, "Unexpected Discord response.");
    const messages = body.map((message) => ({
        messageId: String(message.id),
        content: typeof message.content === "string" ? message.content : "",
        timestamp: String(message.timestamp),
        editedTimestamp: message.edited_timestamp ? String(message.edited_timestamp) : null,
        hasAttachments: Array.isArray(message.attachments) && message.attachments.length > 0,
        hasEmbeds: Array.isArray(message.embeds) && message.embeds.length > 0,
        author: {
            userId: String(message.author?.id ?? ""),
            username: String(message.author?.username ?? ""),
            globalName: message.author?.global_name ? String(message.author.global_name) : null,
            bot: message.author?.bot === true,
        },
    }));
    // Without the Message Content intent Discord returns other members' messages with empty text.
    const contentHidden = messages.some((m) => !m.author.bot && !m.content && !m.hasAttachments && !m.hasEmbeds);
    return { messages, contentHidden };
}

// Plain text only. Mentions notify users and roles; @everyone and @here never notify.
export async function sendMessage(
    channelId: string,
    content: string,
): Promise<{ messageId: string; channelId: string; timestamp: string }> {
    if (typeof content !== "string" || !content.trim()) {
        throw new DiscordError("INVALID_ARGUMENTS", 400, "content must be non-empty text", true);
    }
    if (content.length > 2000) {
        throw new DiscordError("INVALID_ARGUMENTS", 400, "content must be at most 2,000 characters", true);
    }
    const body = await discordRequest(`/channels/${discordId(channelId, "channelId")}/messages`, {
        method: "POST",
        body: { content, allowed_mentions: { parse: ["users", "roles"] } },
    }) as { id?: unknown; channel_id?: unknown; timestamp?: unknown } | null;
    if (!body || typeof body.id !== "string") {
        throw new DiscordError("DISCORD_INVALID_RESPONSE", 502, "Discord did not confirm the message.");
    }
    return { messageId: body.id, channelId: String(body.channel_id), timestamp: String(body.timestamp) };
}
