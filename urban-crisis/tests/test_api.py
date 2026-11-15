import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
import server
class APITests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();server.DB=cls.tmp.name+'/test.db';server.TOKEN='test-token';cls.http=ThreadingHTTPServer(('127.0.0.1',0),server.Handler);cls.url='http://127.0.0.1:'+str(cls.http.server_port);threading.Thread(target=cls.http.serve_forever,daemon=True).start()
 @classmethod
 def tearDownClass(cls):cls.http.shutdown();cls.http.server_close();cls.tmp.cleanup()
 def request(self,path,data=None,auth=False):
  req=urllib.request.Request(self.url+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer test-token'} if auth else {})})
  try:
   with urllib.request.urlopen(req) as r:return r.status,json.load(r)
  except urllib.error.HTTPError as e:return e.code,json.load(e)
 def test_unauthorized_mutation(self):self.assertEqual(self.request('/api/road',{'id':0,'blocked':True})[0],401)
 def test_private_signals(self):self.assertNotIn('sos',self.request('/api/state')[1])
 def test_persistence(self):
  self.assertEqual(self.request('/api/road',{'id':0,'blocked':True},True)[0],200);self.assertTrue(self.request('/api/state')[1]['roads'][0]['blocked'])
 def test_bad_json_shape(self):self.assertEqual(self.request('/api/sos',[])[0],400)
 def test_bad_coordinate(self):self.assertEqual(self.request('/api/route?lat=nan&lon=0')[0],400)
 def test_unknown_path(self):self.assertEqual(self.request('/api/unknown',{})[0],404)
 def test_concurrent_distinct_sos(self):
  from concurrent.futures import ThreadPoolExecutor
  def send(i):return self.request('/api/sos',dict(citizen=f'parallel-{i}',kind='yanğın',lat=40.403,lon=49.844))[0]
  with ThreadPoolExecutor(max_workers=5) as pool:self.assertEqual(list(pool.map(send,range(5))),[200]*5)
  state=self.request('/api/state',auth=True)[1];self.assertEqual(len(state['sos']),5);self.assertTrue(state['alerts']);self.assertTrue(all('citizen' not in x for x in state['sos']))
if __name__=='__main__':unittest.main()
