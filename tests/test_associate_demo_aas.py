import unittest
from tools.associate_demo_aas import AasLocator, associate

class LocatorTests(unittest.TestCase):
    def locator(self):
        a=AasLocator.__new__(AasLocator)
        a.nodes=[(0,0,0),(0,-1,-2)]
        a.planes=[(1,0,0,0,0)]
        a.edges={(1,2)}
        return a
    def test_plane_boundary_uses_back_child(self):
        a=self.locator()
        self.assertEqual(a.area((1,0,0)),1)
        self.assertEqual(a.area((0,0,0)),2)
        self.assertEqual(a.area((-1,0,0)),2)
    def test_solid_does_not_become_area(self):
        a=self.locator();a.nodes[1]=(0,0,-2)
        self.assertEqual(a.area((1,0,0)),0)
    def test_cycles_rejected(self):
        a=self.locator();a.nodes[1]=(0,1,-2)
        with self.assertRaises(ValueError):a.area((1,0,0))
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):self.locator().area((float('nan'),0,0))
    def route(self):
        return dict(kind='rocket',pickup_ms=50,client=0,segment=0,
                    points=[dict(t=0,p=[1,0,0]),dict(t=50,p=[-1,0,0])])
    def test_direct_edge_is_not_execution_permission(self):
        r=associate(self.route(),self.locator())
        self.assertEqual(r['direct_aas_transitions'],1)
        self.assertFalse(r['ready_for_execution'])
        self.assertFalse(r['geometry_verified'])
    def test_missing_edge_preserved_for_review(self):
        a=self.locator();a.edges=set()
        r=associate(self.route(),a)
        self.assertEqual(r['unresolved_transitions'],1)
        self.assertEqual(r['areas'],[1,2])
    def test_time_gap_rejected(self):
        r=self.route();r['points'][1]['t']=101
        with self.assertRaises(ValueError):associate(r,self.locator())
    def test_teleport_gap_rejected(self):
        r=self.route();r['points'][1]['p']=[-500,0,0]
        with self.assertRaises(ValueError):associate(r,self.locator())

if __name__=='__main__':unittest.main()
