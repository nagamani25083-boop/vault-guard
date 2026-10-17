#!/usr/bin/env python3
"""Overseas Kling Motion Control 3.0 gateway CLI. Reads INTEGRATIONS_API_KEY."""
import argparse,json,os,sys,time,urllib.error,urllib.parse,urllib.request
from pathlib import Path
CREATE="https://app-f58c4fdcbbpd-api-m9xKdopkqvMa.gateway.appmedo.com/motion-control/kling-3.0"; TASKS="https://app-f58c4fdcbbpd-api-qYGWzQv1x4GY.gateway.appmedo.com/tasks"
class ApiError(RuntimeError): pass
def emit(v): print(json.dumps(v,ensure_ascii=False,indent=2))
def key():
 v=os.environ.get("INTEGRATIONS_API_KEY","").strip()
 if not v: raise ApiError("Missing environment variable INTEGRATIONS_API_KEY")
 return v.removeprefix("Bearer ").strip()
def request(method,url,body=None):
 req=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,method=method,headers={"X-Gateway-Authorization":f"Bearer {key()}","Content-Type":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=60) as resp: payload=json.loads(resp.read().decode()); status=resp.status
 except urllib.error.HTTPError as e:
  raw=e.read().decode(errors="replace")
  try: payload=json.loads(raw)
  except json.JSONDecodeError: payload={"message":raw[:500]}
  raise ApiError(f"HTTP {e.code}: {payload.get('message','Request failed')}") from e
 except urllib.error.URLError as e: raise ApiError(f"Network request failed: {e.reason}") from e
 if not 200<=status<300 or payload.get("code")!=0: raise ApiError(f"API {payload.get('code',status)}: {payload.get('message','Request failed')}")
 return payload
def create(a):
 if len(a.prompt or "")>2500: raise ApiError("prompt must not exceed 2500 characters")
 if a.element_id and a.character_orientation!="video": raise ApiError("Element input requires character_orientation=video")
 contents=([{"type":"prompt","text":a.prompt}] if a.prompt else [])+[{"type":"image","url":a.image_url},{"type":"video","url":a.video_url}]
 if a.element_id: contents.append({"type":"element","element_id":a.element_id,"id":a.element_index})
 options={"watermark_info":{"enabled":a.watermark}}
 if a.callback_url: options["callback_url"]=a.callback_url
 if a.external_task_id: options["external_task_id"]=a.external_task_id
 p=request("POST",CREATE,{"contents":contents,"settings":{"character_orientation":a.character_orientation,"audio":a.audio,"resolution":a.resolution},"options":options}); d=p.get("data") or {}
 emit({"task_id":str(d.get("id","")),"external_task_id":d.get("external_id"),"status":d.get("status"),"request_id":p.get("request_id")})
def query_payload(ids=None,eids=None):
 if bool(ids)==bool(eids): raise ApiError("Choose exactly one task identifier type")
 return request("GET",TASKS+"?"+urllib.parse.urlencode({"task_ids":ids} if ids else {"external_task_ids":eids}))
def query(a): emit(query_payload(a.task_ids,a.external_task_ids))
def download(url,dst):
 p=Path(dst).expanduser().resolve(); p.parent.mkdir(parents=True,exist_ok=True)
 with urllib.request.urlopen(url,timeout=120) as src,p.open("wb") as out:
  while chunk:=src.read(1048576): out.write(chunk)
 return str(p)
def wait(a):
 deadline=time.time()+a.timeout
 while time.time()<deadline:
  tasks=query_payload(a.task_id,None).get("data") or []; task=next((x for x in tasks if str(x.get("id"))==str(a.task_id)),None)
  if not task: raise ApiError("Target task was not found")
  if task.get("status")=="failed": raise ApiError(task.get("message") or "Generation failed")
  if task.get("status")=="succeeded":
   videos=[x for x in task.get("outputs",[]) if x.get("type")=="video" and x.get("url")]
   if not videos: raise ApiError("Succeeded task contains no video output")
   result={"task_id":str(task.get("id")),"status":"succeeded","videos":videos}
   if a.download: result["downloaded_to"]=download(videos[0]["url"],a.download)
   emit(result); return
  time.sleep(a.interval)
 raise ApiError(f"Task did not finish within {a.timeout} seconds")
def parser():
 p=argparse.ArgumentParser(description=__doc__); s=p.add_subparsers(dest="command",required=True)
 c=s.add_parser("create"); c.add_argument("--image-url",required=True); c.add_argument("--video-url",required=True); c.add_argument("--prompt"); c.add_argument("--character-orientation",choices=["image","video"],required=True); c.add_argument("--audio",choices=["original","off"],default="original"); c.add_argument("--resolution",choices=["720p","1080p"],default="720p"); c.add_argument("--element-id"); c.add_argument("--element-index",default="element_1"); c.add_argument("--callback-url"); c.add_argument("--external-task-id"); c.add_argument("--watermark",action="store_true"); c.set_defaults(func=create)
 q=s.add_parser("query"); g=q.add_mutually_exclusive_group(required=True); g.add_argument("--task-ids"); g.add_argument("--external-task-ids"); q.set_defaults(func=query)
 w=s.add_parser("wait"); w.add_argument("--task-id",required=True); w.add_argument("--interval",type=float,default=7); w.add_argument("--timeout",type=int,default=600); w.add_argument("--download"); w.set_defaults(func=wait); return p
def main():
 try: a=parser().parse_args(); a.func(a)
 except ApiError as e: emit({"error":str(e)}); return 2
 return 0
if __name__=="__main__": sys.exit(main())
