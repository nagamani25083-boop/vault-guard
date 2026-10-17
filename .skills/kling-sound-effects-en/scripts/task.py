#!/usr/bin/env python3
"""Call the deployed, user-isolated Edge endpoint. JSON stdout; no credentials in arguments.
Environment: KLING_EDGE_URL, APP_SESSION_TOKEN. Create once, then query saved local task UUID.
"""
import argparse,json,os,sys,urllib.request,urllib.error

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('action',choices=['create','query','list','save']);p.add_argument('--id');p.add_argument('--kind',choices=['text','video']);p.add_argument('--params',default='{}')
 a=p.parse_args()
 try:
  body={'action':a.action,'id':a.id,'kind':a.kind,'params':json.loads(a.params)}
  req=urllib.request.Request(os.environ['KLING_EDGE_URL'],data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+os.environ['APP_SESSION_TOKEN'],'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=90) as r: result=json.load(r)
  print(json.dumps(result,ensure_ascii=False));return 1 if result.get('error') else 0
 except urllib.error.HTTPError as e:
  print(json.dumps({'error':'Edge HTTP '+str(e.code)}));return 1
 except Exception as e:
  print(json.dumps({'error':type(e).__name__}));return 1
if __name__=='__main__':sys.exit(main())
