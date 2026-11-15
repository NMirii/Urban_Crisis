"""Deterministic simulation domain, persisted in SQLite by server.py."""
import heapq
import math
import time
import uuid

DEFAULT_RULES = dict(reroute_percent=90, critical_percent=95, sos_count=5, window_seconds=300, radius_m=500)
KINDS = ['yanğın', 'dağıntı', 'su basması', 'tibbi yardım']

def distance(a, b):
    lat1, lat2 = map(math.radians, (a['lat'], b['lat']))
    dlat = lat2-lat1
    dlon = math.radians(b['lon']-a['lon'])
    v = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371000*2*math.asin(min(1, math.sqrt(v)))

def seed():
    nodes = []
    for y in range(4):
        for x in range(4):
            nodes.append(dict(id=y*4+x, lat=40.400+y*.003, lon=49.840+x*.004, zone=['Yasamal','Nəsimi','Nərimanov','Səbail'][y]))
    roads = []
    for n in nodes:
        for target in (n['id']+1 if n['id']%4<3 else -1, n['id']+4):
            if 0<=target<16:
                roads.append(dict(id=len(roads), a=n['id'], b=target, blocked=False, meters=round(distance(n,nodes[target]))))
    return dict(nodes=nodes, roads=roads, shelters=[
        dict(id='s1', name='Yasamal parkı • DEMO', node=0, capacity=100, occupied=25, active=True),
        dict(id='s2', name='Nəsimi sığınacağı • DEMO', node=7, capacity=100, occupied=65, active=True),
        dict(id='s3', name='Şimal stansiyası • DEMO', node=15, capacity=100, occupied=40, active=True),
        dict(id='s4', name='Ehtiyat toplanış sahəsi • DEMO', node=12, capacity=150, occupied=0, active=False)],
        teams=[dict(id='B1',status='available',alert=None),dict(id='B2',status='available',alert=None),dict(id='B3',status='available',alert=None)],
        sos=[], alerts=[], audit=[], rules=DEFAULT_RULES.copy())

def coordinates(data):
    lat, lon = float(data['lat']), float(data['lon'])
    if not math.isfinite(lat+lon) or not (-90<=lat<=90 and -180<=lon<=180):
        raise ValueError('Koordinatlar etibarsızdır')
    return dict(lat=lat, lon=lon)

def route(state, point):
    start = min(state['nodes'], key=lambda n:distance(n, point))
    if distance(start, point)>2000:
        return dict(options=[], recommended=None, reason='Koordinat demo xəritəsinin əhatəsindən kənardadır')
    graph = {n['id']:[] for n in state['nodes']}
    for r in state['roads']:
        if not r['blocked']:
            graph[r['a']].append((r['b'],r['meters']))
            graph[r['b']].append((r['a'],r['meters']))
    queue=[(0,start['id'],[start['id']])]; best={}; paths={}
    while queue:
        cost,n,path=heapq.heappop(queue)
        if n in best: continue
        best[n]=cost; paths[n]=path
        for nxt,d in graph[n]:
            if nxt not in best: heapq.heappush(queue,(cost+d,nxt,path+[nxt]))
    options=[]
    for s in state['shelters']:
        if not s['active']: continue
        percent=s['occupied']/s['capacity']*100
        reachable=s['node'] in best
        options.append(dict(**s,percent=percent,reachable=reachable,eligible=reachable and percent<state['rules']['reroute_percent'],
                            meters=round(best[s['node']]+distance(start,point)) if reachable else None,path=paths.get(s['node'],[])))
    options.sort(key=lambda s:s['meters'] if s['meters'] is not None else float('inf'))
    rec=next((s for s in options if s['eligible']),None)
    return dict(options=options,recommended=rec,reason=None if rec else 'Əlçatan və doluluq həddindən aşağı məntəqə yoxdur', snapped_node=start['id'])

def analyze(state, now=None):
    now=time.time() if now is None else now
    r=state['rules']; recent=[s for s in state['sos'] if s['status']=='active' and 0<=now-s['at']<=r['window_seconds']]
    triggers={}
    for s in recent:
        groups=[('zone:'+s['zone'],[x for x in recent if x['zone']==s['zone']]),
                ('radius:'+s['id'],[x for x in recent if distance(s,x)<=r['radius_m']])]
        for key,group in groups:
            if len({x['citizen'] for x in group})>=r['sos_count']:
                # Radius keys use participant identity for stable incident grouping.
                if key.startswith('radius:'): key='radius:'+','.join(sorted(x['id'] for x in group))
                triggers[key]=dict(kind='sos',label=s['zone']+' — SOS klasteri',count=len({x['citizen'] for x in group}),members=[x['id'] for x in group],node=min(state['nodes'],key=lambda n:distance(n,s))['id'])
    # Suppress radius alerts wholly covered by a qualifying zone incident.
    zones=[set(v['members']) for k,v in triggers.items() if k.startswith('zone:')]
    triggers={k:v for k,v in triggers.items() if not(k.startswith('radius:') and any(set(v['members'])<=z for z in zones))}
    for s in state['shelters']:
        if s['active'] and 100*s['occupied']/s['capacity']>r['critical_percent']:
            triggers['shelter:'+s['id']]=dict(kind='capacity',label=s['name']+' — kritik doluluq',node=s['node'])
    for a in state['alerts']:
        if a['key'] not in triggers and a['status']!='resolved': a['status']='resolved'
    for key,v in triggers.items():
        if not any(a['key']==key and a['status']!='resolved' for a in state['alerts']):
            state['alerts'].append(dict(id=str(uuid.uuid4()),key=key,status='pending',at=now,**v))
    return state

def change(state, action, data, now=None):
    now=time.time() if now is None else now
    if action=='sos':
        point=coordinates(data); citizen=str(data['citizen'])
        if not 8<=len(citizen)<=100 or data['kind'] not in KINDS: raise ValueError('SOS məlumatları yanlışdır')
        nearest=min(state['nodes'],key=lambda n:distance(n,point))
        if distance(nearest,point)>2000: raise ValueError('Demo əhatəsindən kənar koordinat')
        old=next((x for x in state['sos'] if x['citizen']==citizen and x['status']=='active'),None)
        if old: return old  # idempotent active SOS; cannot inflate count
        item=dict(id=str(uuid.uuid4()),citizen=citizen,kind=data['kind'],zone=nearest['zone'],status='active',at=now,**point)
        state['sos'].append(item)
    elif action=='safe':
        for x in state['sos']:
            if x['citizen']==data['citizen']: x['status']='safe'
        item={'status':'safe'}
    elif action=='road':
        if type(data['blocked']) is not bool: raise ValueError('blocked boolean olmalıdır')
        item=next(x for x in state['roads'] if x['id']==int(data['id'])); item['blocked']=data['blocked']
    elif action=='occupancy':
        item=next(x for x in state['shelters'] if x['id']==data['id'])
        value=data['occupied']
        if type(value) is not int or not 0<=value<=item['capacity']: raise ValueError('Doluluq tutum sərhədində tam ədəd olmalıdır')
        item['occupied']=value
    elif action=='confirm':
        analyze(state,now)
        item=next(x for x in state['alerts'] if x['id']==data['id'])
        if item['status']=='confirmed': return item
        if item['status']!='pending': raise ValueError('Xəbərdarlıq artıq aktiv deyil')
        team=next((x for x in state['teams'] if x['status']=='available'),None)
        shelter=next((x for x in state['shelters'] if not x['active']),None)
        if not team or not shelter: raise ValueError('Boş briqada və ehtiyat məntəqə tələb olunur; qərar icra edilmədi')
        team.update(status='dispatched',alert=item['id']); shelter['active']=True
        item.update(status='confirmed',team=team['id'],opened=shelter['id'])
    elif action=='release':
        item=next(x for x in state['teams'] if x['id']==data['id']); item.update(status='available',alert=None)
    elif action=='rules':
        proposed=state['rules']|data
        if set(proposed)!=set(DEFAULT_RULES): raise ValueError('Naməlum qayda')
        if any(type(v) is not int for v in proposed.values()): raise ValueError('Qaydalar tam ədəd olmalıdır')
        if not(1<=proposed['reroute_percent']<=proposed['critical_percent']<=100 and 2<=proposed['sos_count']<=100 and 1<=proposed['window_seconds']<=3600 and 1<=proposed['radius_m']<=5000): raise ValueError('Qayda sərhədləri yanlışdır')
        state['rules']=proposed; item=proposed
    else: raise ValueError('Naməlum əməliyyat')
    state['audit'].append(dict(at=now,action=action))
    analyze(state,now)
    return item
