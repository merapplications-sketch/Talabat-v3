"""One-shot health observer. No DB writes, no real message transport or schedule.
Run later under an approved scheduler; JSON outbox must be connected to a named
on-call receiver before it can be considered an operational alert service.
"""
import argparse, hashlib, json, os, pathlib, tempfile, time, urllib.request

def check(config, prior=None):
    prior = prior or {}
    state, events = {}, []
    for endpoint in config['endpoints']:
        name = endpoint['name']
        healthy, error = False, None
        started = time.monotonic()
        try:
            headers = {key: os.environ[value] for key,value in endpoint.get('headers_env', {}).items()}
            with urllib.request.urlopen(urllib.request.Request(endpoint['url'],headers=headers), timeout=endpoint.get('timeout_s',5)) as response:
                body=response.read(1024*1024)
                healthy=response.status==200 and endpoint.get('contains','').encode() in body
                if not healthy:error='status_or_content_mismatch'
        except Exception as e:
            error=type(e).__name__  # no credentials, response data or URLs in alerts
        state[name]={'healthy':healthy,'observed_at':int(time.time()),'latency_ms':round((time.monotonic()-started)*1000,1),'error':error}
        previous=prior.get(name)
        if not healthy and (not previous or previous['healthy']):
            events.append({'type':'incident','endpoint':name,'at':state[name]['observed_at'],'id':hashlib.sha256((name+str(state[name]['observed_at'])).encode()).hexdigest()[:20]})
        elif healthy and previous and not previous['healthy']:
            events.append({'type':'recovery','endpoint':name,'at':state[name]['observed_at']})
    return state,events

def atomic_json(path,value):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,indent=2);f.write('\n')
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);parser.add_argument('--state',required=True);parser.add_argument('--outbox',required=True);args=parser.parse_args()
    previous=json.loads(pathlib.Path(args.state).read_text()) if pathlib.Path(args.state).exists() else {}
    current,events=check(json.loads(pathlib.Path(args.config).read_text()),previous)
    atomic_json(args.state,current)
    if events:
        with open(args.outbox,'a')as f:
            for event in events:f.write(json.dumps(event)+'\n')
    print(json.dumps({'healthy':all(v['healthy']for v in current.values()),'events_written':len(events)}))
