# Mandatory Complete Application Workflow

Creation returning a task ID means submitted, not completed. The application must poll automatically, extract a video URL, render a playable preview, and provide download/save.

## Completion Contract

Complete means: create returned `data.id`; exact-task polling reached `succeeded`; `outputs[type=video].url` exists; `<video controls playsInline>` is visible; download/save works; ownership and result are stored for refresh recovery; the 30-day URL is transferred to Supabase Storage.

Use the registered Singapore API Plugin endpoint and the platform-injected `INTEGRATIONS_API_KEY`.

## Creation Edge Function

```typescript
// supabase/functions/kling-motion-control-overseas-create/index.ts
import { serve } from "https://deno.land/std/http/server.ts";
const CREATE_ENDPOINT =
  "https://app-f58c4fdcbbpd-api-m9xKdopkqvMa.gateway.appmedo.com/motion-control/kling-3.0";

serve(async (req) => {
  if (req.method !== "POST") return Response.json({ error: "Method Not Allowed" }, { status: 405 });
  try {
    const body = await req.json();
    const imageUrl = String(body.image_url || "").trim();
    const videoUrl = String(body.video_url || "").trim();
    const prompt = String(body.prompt || "").trim();
    const orientation = body.character_orientation;
    if (!imageUrl || !videoUrl) return Response.json({ error: "Reference image and motion video are required" }, { status: 400 });
    if (!['image', 'video'].includes(orientation)) return Response.json({ error: "Invalid character orientation" }, { status: 400 });
    if (prompt.length > 2500) return Response.json({ error: "Prompt must not exceed 2500 characters" }, { status: 400 });
    if (!['720p', '1080p'].includes(body.resolution || '720p')) return Response.json({ error: "Invalid resolution" }, { status: 400 });
    if (!['original', 'off'].includes(body.audio || 'original')) return Response.json({ error: "Invalid audio option" }, { status: 400 });

    const key = Deno.env.get("INTEGRATIONS_API_KEY");
    if (!key) return Response.json({ error: "Video service is not configured" }, { status: 500 });
    const auth = key.startsWith("Bearer ") ? key : `Bearer ${key}`;
    const contents = [
      ...(prompt ? [{ type: "prompt", text: prompt }] : []),
      { type: "image", url: imageUrl },
      { type: "video", url: videoUrl },
    ];
    if (body.element_id) {
      if (orientation !== 'video') return Response.json({ error: "Element input requires video orientation" }, { status: 400 });
      contents.push({ type: "element", element_id: body.element_id, id: body.element_index || "element_1" });
    }
    const upstream = await fetch(CREATE_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Gateway-Authorization": auth },
      body: JSON.stringify({
        contents,
        settings: { character_orientation: orientation, resolution: body.resolution || "720p", audio: body.audio || "original" },
        options: {
          external_task_id: body.external_task_id || crypto.randomUUID(),
          watermark_info: { enabled: Boolean(body.watermark_enabled) },
          ...(body.callback_url ? { callback_url: body.callback_url } : {}),
        },
      }),
    });
    const json = await upstream.json().catch(() => ({}));
    if (!upstream.ok || json.code !== 0) return Response.json({ error: json.message || "Task creation failed", code: json.code, request_id: json.request_id }, { status: upstream.status || 502 });
    if (!json.data?.id) return Response.json({ error: "Creation response is missing data.id" }, { status: 502 });
    return Response.json({ task_id: String(json.data.id), external_task_id: json.data.external_id, status: json.data.status });
  } catch (error) {
    console.error("[motion create]", error);
    return Response.json({ error: "Task creation service failed" }, { status: 502 });
  }
});
```

The creation function returns `submitted`; it never waits, transfers media, or reports generation success.

## Query and Storage Edge Function

```typescript
import { serve } from "https://deno.land/std/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
const QUERY_ENDPOINT = "https://app-f58c4fdcbbpd-api-qYGWzQv1x4GY.gateway.appmedo.com/tasks";
const supabase = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);

async function persistVideo(taskId: string, output: { id?: string; url: string }) {
  const response = await fetch(output.url);
  if (!response.ok || !response.body) throw new Error(`Download failed: ${response.status}`);
  const contentType = response.headers.get("content-type") || "video/mp4";
  if (!contentType.startsWith("video/") && contentType !== "application/octet-stream") throw new Error(`Unexpected media type: ${contentType}`);
  const path = `kling-motion-control/${taskId}/${output.id || crypto.randomUUID()}.mp4`;
  const { error } = await supabase.storage.from("generated-media").upload(path, response.body, { contentType, upsert: true, cacheControl: "31536000" });
  if (error) throw error;
  return supabase.storage.from("generated-media").getPublicUrl(path).data.publicUrl;
}

serve(async (req) => {
  if (req.method !== "POST") return Response.json({ error: "Method Not Allowed" }, { status: 405 });
  try {
    const body = await req.json();
    const taskId = String(body.task_id || "").trim();
    const externalTaskId = String(body.external_task_id || "").trim();
    if (Boolean(taskId) === Boolean(externalTaskId)) return Response.json({ error: "Provide exactly one task identifier" }, { status: 400 });
    const key = Deno.env.get("INTEGRATIONS_API_KEY");
    if (!key) return Response.json({ error: "Video service is not configured" }, { status: 500 });
    const auth = key.startsWith("Bearer ") ? key : `Bearer ${key}`;
    const query = taskId ? `task_ids=${encodeURIComponent(taskId)}` : `external_task_ids=${encodeURIComponent(externalTaskId)}`;
    const upstream = await fetch(`${QUERY_ENDPOINT}?${query}`, { headers: { "Content-Type": "application/json", "X-Gateway-Authorization": auth } });
    const json = await upstream.json().catch(() => ({}));
    if (!upstream.ok || json.code !== 0) return Response.json({ error: json.message || "Task query failed", code: json.code, request_id: json.request_id }, { status: upstream.status || 502 });
    const tasks = Array.isArray(json.data) ? json.data : [];
    const task = tasks.find((item: { id?: string; external_id?: string }) => taskId ? String(item.id) === taskId : item.external_id === externalTaskId);
    if (!task) return Response.json({ error: "Target task was not found" }, { status: 502 });
    if (task.status === "failed") return Response.json({ status: "failed", task_id: String(task.id), message: task.message || "Generation failed" });
    if (task.status !== "succeeded") return Response.json({ status: task.status, task_id: String(task.id) });
    const outputs = (task.outputs || []).filter((item: { type?: string; url?: string }) => item.type === "video" && item.url);
    if (!outputs.length) return Response.json({ error: "Succeeded task contains no video output" }, { status: 502 });
    const videos = await Promise.all(outputs.map(async (output: { id?: string; url: string; duration?: string }) => {
      try { return { id: output.id, url: await persistVideo(String(task.id), output), source_url: output.url, duration: output.duration, storage_transfer_success: true }; }
      catch (error) { console.error("[video transfer]", error); return { id: output.id, url: output.url, duration: output.duration, storage_transfer_success: false }; }
    }));
    return Response.json({ status: "succeeded", task_id: String(task.id), videos });
  } catch (error) {
    console.error("[motion query]", error);
    return Response.json({ error: "Task query service failed" }, { status: 502 });
  }
});
```

## Frontend Polling

```typescript
async function queryMotionTask(taskId: string) {
  const { data, error } = await supabase.functions.invoke("kling-motion-control-overseas-query", { body: { task_id: taskId } });
  if (error) throw error;
  return data;
}

async function pollMotionTask(taskId: string, onStatus: (status: string) => void) {
  const startedAt = Date.now();
  const deadline = startedAt + 10 * 60 * 1000;
  while (Date.now() < deadline) {
    const result = await queryMotionTask(taskId);
    onStatus(result.status);
    if (result.status === "succeeded") {
      if (!result.videos?.length) throw new Error("No video result was returned");
      return result.videos;
    }
    if (result.status === "failed") throw new Error(result.message || "Video generation failed");
    await new Promise((resolve) => setTimeout(resolve, Date.now() - startedAt < 30000 ? 3000 : 7000));
  }
  throw new Error("Generation timed out. Continue checking from task history.");
}

async function handleGenerate() {
  setStatus("submitting"); setVideoUrl("");
  const { data, error } = await supabase.functions.invoke("kling-motion-control-overseas-create", { body: formValues });
  if (error) throw error;
  const taskId = String(data.task_id || data.data?.id || "");
  if (!taskId) throw new Error("Creation response is missing the task ID");
  setTaskId(taskId); setStatus("submitted");
  const videos = await pollMotionTask(taskId, setStatus);
  setVideoUrl(videos[0].url); setStatus("succeeded");
}
```

## Mandatory Result UI

```tsx
{["submitted", "processing"].includes(status) && <section aria-live="polite"><p>{status === "submitted" ? "Task submitted" : "Generating video"}</p><progress /><small>Task ID: {taskId}</small></section>}
{status === "succeeded" && videoUrl && <section className="video-result"><h2>Generated video</h2><video src={videoUrl} controls playsInline preload="metadata" /><div><a href={videoUrl} download="kling-motion-control.mp4">Download video</a><button type="button" onClick={() => window.open(videoUrl, "_blank")}>Open preview</button></div></section>}
```

If cross-origin behavior prevents download, add a server proxy returning `Content-Type: video/mp4` and `Content-Disposition: attachment; filename="kling-motion-control.mp4"`.

Required states: `idle`, `submitting`, `submitted`, `processing`, `succeeded`, `failed`, `timeout`. Persist the authenticated user ID, task ID, status, and final URL. Resume nonterminal polling or restore the completed preview after refresh. User history reads only records owned by the current application user.
