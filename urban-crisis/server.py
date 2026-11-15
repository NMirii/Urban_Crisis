"""Zero-dependency local HTTP API. Single SQLite transaction per mutation."""
import copy
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from engine import seed, route, coordinates, change, analyze

ROOT=Path(__file__).parent
DB=os.environ.get('DB_PATH',str(ROOT/'data'/'crisis.db'))
TOKEN=os.environ.get('ADMIN_TOKEN') or secrets.token_urlsafe(24)
LOCK=threading.RLock()

def transaction(fn):
    with LOCK:
        Path(DB).parent.mkdir(parents=True,exist_ok=True)
        with sqlite3.connect(DB,timeout=10) as con:
            con.execute('CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, value TEXT NOT NULL)')
            con.execute('BEGIN IMMEDIATE')
            row=con.execute('SELECT value FROM state WHERE id=1').fetchone()
            state=json.loads(row[0]) if row else seed()
            result=fn(state)
            con.execute('INSERT OR REPLACE INTO state VALUES (1,?)',(json.dumps(state,ensure_ascii=False),))
            return result

class Handler(BaseHTTPRequestHandler):
    def reply(self,code,payload):
        body=json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)
    def admin(self):
        return hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+TOKEN)
    def do_GET(self):
        u=urlparse(self.path)
        try:
            if u.path=='/api/health': return self.reply(200,{'ok':True,'mode':'simulation'})
            if u.path=='/api/state':
                def snapshot(s):
                    analyze(s); out=copy.deepcopy(s)
                    if not self.admin():
                        out.pop('sos'); out.pop('audit'); out.pop('alerts'); out.pop('teams')
                    else:
                        for x in out['sos']: x.pop('citizen',None)
                    return out
                return self.reply(200,transaction(snapshot))
            if u.path=='/api/route':
                q={k:v[0] for k,v in parse_qs(u.query).items()}; p=coordinates(q)
                return self.reply(200,transaction(lambda s:route(s,p)))
            files={'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/styles.css':('styles.css','text/css')}
            if u.path not in files: return self.reply(404,{'error':'Tapılmadı'})
            name,mime=files[u.path]; body=(ROOT/'static'/name).read_bytes()
            self.send_response(200); self.send_header('Content-Type',mime+'; charset=utf-8'); self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(body)
        except (KeyError,ValueError): self.reply(400,{'error':'Sorğu parametrləri yanlışdır'})
    def do_POST(self):
        try:
            # Same-origin browser writes only; API clients may omit Origin.
            origin=self.headers.get('Origin')
            if origin and urlparse(origin).netloc!=self.headers.get('Host'): return self.reply(403,{'error':'Origin rədd edildi'})
            action=urlparse(self.path).path.removeprefix('/api/')
            if action not in ['sos','safe','road','occupancy','confirm','release','rules']: return self.reply(404,{'error':'Tapılmadı'})
            if action not in ['sos','safe'] and not self.admin(): return self.reply(401,{'error':'Operator tokeni tələb olunur'})
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=16384: return self.reply(413,{'error':'Sorğu ölçüsü uyğun deyil'})
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict): raise ValueError('JSON obyekt tələb olunur')
            result=transaction(lambda s:change(s,action,data))
            self.reply(200,result)
        except (KeyError,ValueError,TypeError,StopIteration) as e: self.reply(400,{'error':str(e) or 'Obyekt tapılmadı'})
        except sqlite3.Error: self.reply(503,{'error':'Məlumat bazası müvəqqəti əlçatan deyil'})

if __name__=='__main__':
    print('Urban Crisis • simulation only',flush=True)
    print('Operator token: '+TOKEN,flush=True)
    print('Open http://localhost:8000',flush=True)
    ThreadingHTTPServer((os.environ.get('HOST','127.0.0.1'),int(os.environ.get('PORT','8000'))),Handler).serve_forever()
