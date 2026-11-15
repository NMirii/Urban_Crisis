import unittest
from engine import seed,route,change,analyze,distance
class EngineTests(unittest.TestCase):
 def setUp(self): self.s=seed();self.p={'lat':40.403,'lon':49.844}
 def sos(self,i,at=1000,**kw):return change(self.s,'sos',dict(citizen=f'citizen-{i}',kind='yanğın',**(self.p|kw)),now=at)
 def pending(self):return [a for a in self.s['alerts'] if a['status']=='pending']
 def test_nearest(self):
  r=route(self.s,self.p);self.assertEqual(r['recommended']['meters'],min(x['meters'] for x in r['options']))
 def test_road_reroute(self):
  before=route(self.s,self.p)['recommended'];a,b=before['path'][:2];next(r for r in self.s['roads'] if {r['a'],r['b']}=={a,b})['blocked']=True
  after=route(self.s,self.p)['recommended'];self.assertNotEqual(before['path'],after['path']);self.assertFalse(any({a,b}==set(after['path'][i:i+2]) for i in range(len(after['path'])-1)))
 def test_90(self):
  s=self.s['shelters'][0];s['occupied']=89;self.assertTrue(next(x for x in route(self.s,self.p)['options'] if x['id']=='s1')['eligible']);s['occupied']=90;self.assertFalse(next(x for x in route(self.s,self.p)['options'] if x['id']=='s1')['eligible'])
 def test_95(self):
  change(self.s,'occupancy',{'id':'s1','occupied':95});self.assertFalse(self.pending());change(self.s,'occupancy',{'id':'s1','occupied':96});self.assertEqual(len(self.pending()),1)
 def test_five_unique(self):
  for i in range(4):self.sos(i)
  self.assertFalse(self.pending());self.sos(4);self.assertEqual(len(self.pending()),1)
 def test_duplicate(self):
  for _ in range(10):self.sos(1)
  self.assertEqual(len(self.s['sos']),1);self.assertFalse(self.pending())
 def test_window(self):
  for i in range(5):self.sos(i)
  analyze(self.s,1300);self.assertEqual(len(self.pending()),1);analyze(self.s,1300.01);self.assertFalse(self.pending())
 def test_safe(self):
  for i in range(5):self.sos(i)
  change(self.s,'safe',{'citizen':'citizen-1'},now=1001);self.assertFalse(self.pending())
 def test_cross_zone_radius(self):
  for i in range(5):self.sos(i,lat=40.4014 if i<3 else 40.4016)
  self.assertTrue(any(a['key'].startswith('radius:') for a in self.pending()))
 def test_far(self):
  for i in range(4):self.sos(i,lat=40.4,lon=49.84)
  self.sos(4,lat=40.409,lon=49.852);self.assertFalse(self.pending())
 def test_no_route(self):
  for r in self.s['roads']:r['blocked']=True
  self.assertIsNone(route(self.s,self.p)['recommended'])
 def test_outside(self):self.assertIsNone(route(self.s,{'lat':0,'lon':0})['recommended'])
 def test_confirm(self):
  change(self.s,'occupancy',{'id':'s1','occupied':96});a=self.pending()[0];change(self.s,'confirm',{'id':a['id']});change(self.s,'confirm',{'id':a['id']});self.assertEqual(sum(t['status']=='dispatched' for t in self.s['teams']),1);self.assertTrue(self.s['shelters'][-1]['active'])
 def test_resource_failure(self):
  change(self.s,'occupancy',{'id':'s1','occupied':96});a=self.pending()[0]
  for t in self.s['teams']:t['status']='dispatched'
  with self.assertRaises(ValueError):change(self.s,'confirm',{'id':a['id']})
  self.assertEqual(a['status'],'pending');self.assertFalse(self.s['shelters'][-1]['active'])
 def test_validation(self):
  for v in [-1,101,2.5,True]:
   with self.assertRaises(ValueError):change(self.s,'occupancy',{'id':'s1','occupied':v})
 def test_rules(self):
  change(self.s,'rules',{'sos_count':3})
  for i in range(3):self.sos(i)
  self.assertTrue(self.pending())
  with self.assertRaises(ValueError):change(self.s,'rules',{'radius_m':0})
 def test_distance(self):self.assertAlmostEqual(distance({'lat':0,'lon':0},{'lat':0,'lon':1}),111195,delta=1)
if __name__=='__main__':unittest.main()
