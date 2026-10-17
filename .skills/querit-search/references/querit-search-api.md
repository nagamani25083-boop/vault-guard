# Querit Search API — Full Specification & Code

Gateway marker host uses Traefik rewrite: `api-w9Rb5Jdedqq9@app-f58c4fdcbbpd-api-w9Rb5Jdedqq9.gateway.appmedo.com` → `{app_id}-api-w9Rb5Jdedqq9{gateway_suffix}`.

## Endpoint Information

| Item | Value |
|------|-------|
| Endpoint | `POST https://app-f58c4fdcbbpd-api-w9Rb5Jdedqq9.gateway.appmedo.com/v1/search` |
| Auth | `platform_managed` — header `X-Gateway-Authorization: Bearer ${INTEGRATIONS_API_KEY}` |
| Content type | `application/json` |
| Billing | Billed per call |

## Generation-Time Usage (Direct Agent Call)

```typescript
const apiKey = process.env["INTEGRATIONS_API_KEY"]!;

export interface QueritHit {
  url?: string;
  title?: string;
  snippet?: string;
  site_name?: string;
  site_icon?: string;
  page_age?: string;
}

export interface QueritSearchResponse {
  took?: string;
  error_code?: number | string;
  error_msg?: string;
  search_id?: number;
  query_context?: { query?: string };
  results?: { result?: QueritHit[] };
}

export async function callQueritSearch(
  query: string,
  options?: {
    count?: number;
    chunksPerDoc?: number; // keep 1 on Free/PAYG
    filters?: {
      sites?: { include?: string[]; exclude?: string[] };
      timeRange?: { date?: string };
      geo?: { countries?: { include?: string[] } };
      languages?: { include?: string[] };
    };
  }
): Promise<QueritSearchResponse> {
  const body = {
    query,
    count: options?.count ?? 10,
    chunksPerDoc: options?.chunksPerDoc ?? 1,
    filters: options?.filters ?? {},
  };

  const response = await fetch(
    "https://app-f58c4fdcbbpd-api-w9Rb5Jdedqq9.gateway.appmedo.com/v1/search",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    }
  );

  const data = (await response.json()) as QueritSearchResponse;
  if (!response.ok || String(data.error_code) !== "200") {
    throw new Error(
      `Querit search failed: http=${response.status} code=${data.error_code} msg=${data.error_msg} search_id=${data.search_id}`
    );
  }
  return data;
}
```

### Examples

```typescript
await callQueritSearch("artificial intelligence", {
  count: 5,
  filters: { timeRange: { date: "d7" }, languages: { include: ["english"] } },
});

await callQueritSearch("東京 天気", {
  count: 5,
  filters: { languages: { include: ["japanese"] } },
});

await callQueritSearch("climate research", {
  filters: {
    sites: { include: ["nature.com", "science.org"] },
    timeRange: { date: "m3" },
  },
});
```

## Post-Generation Usage (In-App via Edge Function)

### Edge Function (`edge-functions/querit-search.ts`)

```typescript
// edge-functions/querit-search.ts
import { serve } from "https://deno.land/std/http/server.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

const jsonHeaders = { ...corsHeaders, "Content-Type": "application/json" };

serve(async (req: Request): Promise<Response> => {
  // Preflight must be answered and must allow x-client-info: supabase-js sends it on
  // every invoke, and a missing entry makes the browser drop the request before it is
  // sent (surfaces as "Failed to send a request to the Edge Function").
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405, headers: corsHeaders });
  }

  let payload: Record<string, unknown>;
  try {
    payload = await req.json();
    if (!payload.query || typeof payload.query !== "string") {
      throw new Error("Missing query");
    }
  } catch {
    return new Response(JSON.stringify({ error: "Invalid request body" }), {
      status: 400,
      headers: jsonHeaders,
    });
  }

  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: jsonHeaders,
    });
  }

  const body = {
    query: payload.query,
    count: payload.count ?? 10,
    chunksPerDoc: payload.chunksPerDoc ?? 1,
    filters: payload.filters ?? {},
  };

  const upstream = await fetch(
    "https://app-f58c4fdcbbpd-api-w9Rb5Jdedqq9.gateway.appmedo.com/v1/search",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    }
  );

  const text = await upstream.text();
  if (upstream.status === 429 || upstream.status === 402) {
    return new Response(text, {
      status: upstream.status,
      headers: jsonHeaders,
    });
  }
  if (!upstream.ok) {
    return new Response(
      JSON.stringify({ error: `Upstream error: ${upstream.status}`, body: text }),
      { status: 502, headers: jsonHeaders }
    );
  }

  return new Response(text, {
    status: 200,
    headers: jsonHeaders,
  });
});
```

### Frontend Call to Edge Function

```typescript
async function fetchQueritSearch(
  query: string,
  options?: { count?: number; filters?: Record<string, unknown> }
) {
  const { data, error } = await supabase.functions.invoke("querit-search", {
    body: { query, chunksPerDoc: 1, ...options },
  });
  if (error) throw error;
  return data;
}
```

## Error handling

| Condition | Action |
|-----------|--------|
| `401` | Check gateway / INTEGRATIONS_API_KEY binding |
| `429` | Bounded retry (1–2 attempts with backoff); then fall back to `@ai-search` |
| `400` / `500` | Surface `error_msg` + `search_id`; do not loop |
| Empty `results.result` | Valid success — try a broader query or fewer filters |

## Country / language enums

- Countries include: argentina, australia, brazil, canada, colombia, france, germany, india, indonesia, japan, mexico, nigeria, philippines, south korea, spain, united kingdom, united states
- Languages include: english, japanese, korean, german, french, spanish, portuguese

Full enum list: https://www.querit.ai/en/docs/reference/post
