# OnecCall API — Weather Data Endpoints

This file covers the following four synchronous GET endpoints:
1. **Current weather + forecast** (`/data/3.0/onecall`) — `api-wL1zlmgJGAlY`
2. **Historical weather for a timestamp** (`/data/3.0/onecall/timemachine`) — `api-Aa2PZmgJq5OL`
3. **Daily aggregated statistics** (`/data/3.0/onecall/day_summary`) — `api-2Y00zmgJ8lBY`
4. **AI weather overview** (`/data/3.0/onecall/overview`) — `api-oYA6ZxVqenDa`

---

## Endpoint 1 — Current Weather + Forecast

**Endpoint**: `GET https://app-f58c4fdcbbpd-api-wL1zlmgJGAlY.gateway.appmedo.com/data/3.0/onecall`

Returns current weather conditions, minute-by-minute precipitation forecast (1 hour), hourly forecast (48 hours), daily forecast (8 days), and national weather alerts.

### Request parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | `decimal` | Yes | Latitude, range −90 to 90 |
| `lon` | `decimal` | Yes | Longitude, range −180 to 180 |
| `exclude` | `string` | No | Comma-separated list of data blocks to exclude: `current`, `minutely`, `hourly`, `daily`, `alerts` |
| `units` | `string` | No | Unit system: `standard` (default, Kelvin), `metric` (Celsius), `imperial` (Fahrenheit) |
| `lang` | `string` | No | Language code for translating `weather.description` and other text fields |

### Response fields

| Field path | Type | Description |
|------------|------|-------------|
| `lat` | `number` | Location latitude |
| `lon` | `number` | Location longitude |
| `timezone` | `string` | Timezone name (e.g. `America/Chicago`) |
| `timezone_offset` | `number` | Offset from UTC in seconds |
| `current.dt` | `number` | Current data timestamp (Unix UTC) |
| `current.temp` | `number` | Current temperature |
| `current.feels_like` | `number` | Perceived temperature |
| `current.pressure` | `number` | Atmospheric pressure (hPa) |
| `current.humidity` | `number` | Humidity (%) |
| `current.wind_speed` | `number` | Wind speed |
| `current.weather` | `array` | Weather condition array with `id`, `main`, `description`, `icon` |
| `minutely` | `array` | Minute-by-minute precipitation forecast (`dt`, `precipitation`), 1 hour |
| `hourly` | `array` | Hourly forecast (48 hours) with temperature, precipitation probability, and weather conditions |
| `daily` | `array` | Daily forecast (8 days) with high/low temperature, sunrise/sunset, and moon phase |
| `alerts?` | `array` | National weather alerts with issuing agency, event name, start/end time, and description |

---

## Endpoint 2 — Historical Weather for a Timestamp

**Endpoint**: `GET https://app-f58c4fdcbbpd-api-Aa2PZmgJq5OL.gateway.appmedo.com/data/3.0/onecall/timemachine`

Returns historical weather data for a specific Unix timestamp. Supports 1979-01-01 to +4 days in the future.

### Request parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | `decimal` | Yes | Latitude |
| `lon` | `decimal` | Yes | Longitude |
| `dt` | `integer` | Yes | UTC Unix timestamp; range 1979-01-01 to +4 days |
| `units` | `string` | No | Unit system: `standard`, `metric`, `imperial` |
| `lang` | `string` | No | Language code |

### Response fields

| Field path | Type | Description |
|------------|------|-------------|
| `lat` | `number` | Location latitude |
| `lon` | `number` | Location longitude |
| `timezone` | `string` | Timezone name |
| `data` | `array` | Weather data array; each item contains temperature, pressure, humidity, wind speed, visibility, and weather conditions |

---

## Endpoint 3 — Daily Aggregated Statistics

**Endpoint**: `GET https://app-f58c4fdcbbpd-api-2Y00zmgJ8lBY.gateway.appmedo.com/data/3.0/onecall/day_summary`

Returns daily aggregated weather statistics for a given date. Supports 1979-01-02 to +1.5 years in the future.

### Request parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | `decimal` | Yes | Latitude |
| `lon` | `decimal` | Yes | Longitude |
| `date` | `string` | Yes | Date in `YYYY-MM-DD` format; range 1979-01-02 to +1.5 years |
| `units` | `string` | No | Unit system: `standard`, `metric`, `imperial` |
| `lang` | `string` | No | Language code |
| `tz` | `string` | No | Timezone in `±HH:MM` format |

### Response fields

| Field path | Type | Description |
|------------|------|-------------|
| `lat` | `number` | Location latitude |
| `lon` | `number` | Location longitude |
| `tz` | `string` | Timezone |
| `date` | `string` | Requested date |
| `temperature.min` | `number` | Daily minimum temperature |
| `temperature.max` | `number` | Daily maximum temperature |
| `temperature.afternoon` | `number` | Afternoon temperature |
| `temperature.night` | `number` | Nighttime temperature |
| `temperature.evening` | `number` | Evening temperature |
| `temperature.morning` | `number` | Morning temperature |
| `precipitation.total` | `number` | Total precipitation (mm) |
| `wind.max.speed` | `number` | Maximum wind speed |
| `wind.max.direction` | `number` | Direction of maximum wind speed (degrees) |
| `cloud_cover.afternoon` | `number` | Afternoon cloud cover percentage |
| `humidity.afternoon` | `number` | Afternoon humidity percentage |
| `pressure.afternoon` | `number` | Afternoon atmospheric pressure (hPa) |

---

## Endpoint 4 — AI Weather Overview

**Endpoint**: `GET https://app-f58c4fdcbbpd-api-oYA6ZxVqenDa.gateway.appmedo.com/data/3.0/onecall/overview`

Returns an AI-generated natural-language weather summary for today or tomorrow.

### Request parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | `decimal` | Yes | Latitude |
| `lon` | `decimal` | Yes | Longitude |
| `date` | `string` | No | Date in `YYYY-MM-DD` format; only today or tomorrow is supported |
| `units` | `string` | No | Unit system: `standard`, `metric`, `imperial` |

### Response fields

| Field path | Type | Description |
|------------|------|-------------|
| `lat` | `number` | Location latitude |
| `lon` | `number` | Location longitude |
| `tz` | `string` | Timezone |
| `date` | `string` | Summary date |
| `units` | `string` | Unit system used |
| `weather_overview` | `string` | AI-generated natural-language weather description |

---

## Generation-time usage (Agent calls directly)

Use the built-in script for generation-time calls — do not hand-write TypeScript request code. Bash tool timeout must be set to `600000` ms.

```bash
# Endpoint 1 — current weather + forecast
python3 <skill-path>/scripts/call_weather.py --endpoint onecall \
  --lat 40.7128 --lon -74.0060 \
  [--units metric] [--lang en] [--exclude minutely,alerts]

# Endpoint 2 — historical weather for a timestamp
python3 <skill-path>/scripts/call_weather.py --endpoint timemachine \
  --lat 40.7128 --lon -74.0060 --dt 1684929490 [--units metric]

# Endpoint 3 — daily aggregated statistics
python3 <skill-path>/scripts/call_weather.py --endpoint day_summary \
  --lat 40.7128 --lon -74.0060 --date 2024-06-15 [--units metric]

# Endpoint 4 — AI weather overview
python3 <skill-path>/scripts/call_weather.py --endpoint overview \
  --lat 40.7128 --lon -74.0060 [--units metric]
```

The script reads `INTEGRATIONS_API_KEY`, calls the selected endpoint, and prints one JSON line to stdout: `{"status":"succeed","result":{...}}`. On failure it prints an error to stderr and exits with a non-zero code.

---

## Post-generation usage (in-app via Edge Function)

Deploy a separate Edge Function for each endpoint. The example below uses "Current weather + forecast"; all other endpoints follow the same structure — only the parameter parsing and upstream URL need to be changed.

### Edge Function — current-forecast.ts

```typescript
// edge-functions/current-forecast.ts
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  let lat: string, lon: string, exclude: string | undefined,
      units: string | undefined, lang: string | undefined;
  try {
    const body = await req.json();
    lat = body.lat;
    lon = body.lon;
    if (!lat || !lon) throw new Error("Missing lat or lon");
    exclude = body.exclude;
    units = body.units;
    lang = body.lang;
  } catch {
    return new Response(JSON.stringify({ error: "Invalid request body" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const apiKey = Deno.env.get("INTEGRATIONS_API_KEY");
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Server configuration error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }

  const params = new URLSearchParams({ lat, lon });
  if (exclude) params.set("exclude", exclude);
  if (units) params.set("units", units);
  if (lang) params.set("lang", lang);

  const upstream = await fetch(
    `https://app-f58c4fdcbbpd-api-wL1zlmgJGAlY.gateway.appmedo.com/data/3.0/onecall?${params}`,
    {
      method: "GET",
      headers: {
        "Accept": "application/json",
        "X-Gateway-Authorization": `Bearer ${apiKey}`,
      },
    }
  );

  if (upstream.status === 429 || upstream.status === 402) {
    const errText = await upstream.text();
    return new Response(errText, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!upstream.ok) {
    return new Response(
      JSON.stringify({ error: `Upstream error: ${upstream.status}` }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }

  const data = await upstream.json();
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
});
```

**Replacement reference for other endpoint Edge Functions:**

| Endpoint | Function filename | Required parameters | Upstream URL |
|----------|-------------------|---------------------|--------------|
| Historical weather for a timestamp | `weather-timemachine.ts` | `lat`, `lon`, `dt` | `https://app-f58c4fdcbbpd-api-Aa2PZmgJq5OL.gateway.appmedo.com/data/3.0/onecall/timemachine` |
| Daily aggregated statistics | `weather-day-summary.ts` | `lat`, `lon`, `date` | `https://app-f58c4fdcbbpd-api-2Y00zmgJ8lBY.gateway.appmedo.com/data/3.0/onecall/day_summary` |
| AI weather overview | `weather-overview.ts` | `lat`, `lon` | `https://app-f58c4fdcbbpd-api-oYA6ZxVqenDa.gateway.appmedo.com/data/3.0/onecall/overview` |

### Frontend invocation examples

**Preferred (when supabase client is available):**

```typescript
async function fetchCurrentForecast(lat: number, lon: number, units = "metric") {
  const { data, error } = await supabase.functions.invoke("current-forecast", {
    body: { lat: String(lat), lon: String(lon), units },
  });
  if (error) throw error;
  return data;
}
```

**Fallback (when supabase client is not available):**

```typescript
async function fetchCurrentForecast(lat: number, lon: number, units = "metric") {
  const res = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/current-forecast`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lat: String(lat), lon: String(lon), units }),
  });

  if (res.status === 429) {
    const err = await res.json();
    throw new Error(`Quota exceeded: ${err.message ?? res.statusText}`);
  }
  if (res.status === 402) {
    const err = await res.json();
    throw new Error(`Insufficient balance: ${err.message ?? res.statusText}`);
  }
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);

  return res.json();
}
```
