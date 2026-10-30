import unittest
from fractions import Fraction as Q
from fm_control.scalar import interval as I, safe_actions, obstruction

class Certificate(unittest.TestCase):
    def test_genuine_disjoint_witness(self):
        # Both current states x=1/2 are safe and give exactly the same y.
        # Drift -1 requires u>=1/2; drift +1 requires u<=-1/2.
        self.assertTrue(obstruction([(Q(1,2),1,-1),(Q(1,2),1,1)], Q(1,2),0,I(0,1),I(-2,2)))
    def test_touching_is_not_disjoint(self):
        self.assertFalse(obstruction([(0,1,0),(1,1,0)],Q(1,2),Q(1,2),I(0,1),I(-2,2)))
    def test_inconsistent_measurement_rejected(self):
        self.assertFalse(obstruction([(0,1,-1),(1,1,1)],0,0,I(0,1),I(-2,2)))
    def test_individual_infeasibility_rejected(self):
        self.assertFalse(obstruction([(0,0,-1),(1,1,1)],Q(1,2),1,I(0,1),I(-2,2)))
    def test_unsafe_current_state_rejected(self):
        self.assertFalse(obstruction([(-1,1,-1),(1,1,1)],0,2,I(0,1),I(-2,2)))
    def test_signed_zero_gains(self):
        self.assertEqual(safe_actions(0,-2,0,I(0,1),I(-2,2)),I(Q(-1,2),0))
        self.assertEqual(safe_actions(0,0,0,I(0,1),I(-2,2)),I(-2,2))
        self.assertIsNone(safe_actions(0,0,2,I(0,1),I(-2,2)))
    def test_exact_grid_equivalence(self):
        for x in [Q(0),Q(1,2),Q(1)]:
            for gain in [-2,-1,0,1,2]:
                for drift in [-2,-1,0,1,2]:
                    ans=safe_actions(x,gain,drift,I(0,1),I(-2,2))
                    for k in range(-24,25):
                        u=Q(k,8)
                        analytic=(-2<=u<=2 and 0<=x+gain*u+drift<=1)
                        accepted=ans is not None and ans[0]<=u<=ans[1]
                        self.assertEqual(accepted,analytic)
    def test_raw_float_touching_boundary(self):
        self.assertFalse(obstruction([(1,3,0),(1,1,-Q(1,3))],1,0,(1.0,2.0),I(0,2)))
        result=safe_actions(0,10,0,(0.0,1.0),(0.0,1.0))
        self.assertEqual(result,(Q(0),Q(1,10)))
        self.assertEqual(10*result[1],1)
    def test_invalid_intervals_rejected_including_zero_gain(self):
        bad=[None,(),(1,), (1,2,3),(2,1),(0,float('nan')),(0,float('inf')),'01']
        for bounds in bad:
            for gain in [0,1]:
                with self.subTest(bounds=bounds,gain=gain):
                    with self.assertRaises(ValueError): safe_actions(0,gain,0,bounds,I(0,1))
                    with self.assertRaises(ValueError): safe_actions(0,gain,0,I(0,1),bounds)
                    with self.assertRaises(ValueError): obstruction([(0,gain,0)]*2,0,0,bounds,I(0,1))
    def test_zero_gain_normalizes_allowed_interval(self):
        result=safe_actions(0,0,0,(0.0,1.0),(-1.0,1.0))
        self.assertEqual(result,I(-1,1))
        self.assertTrue(all(type(v) is Q for v in result))
    def test_binary_float_and_decimal_string_are_distinct_contracts(self):
        self.assertTrue(obstruction([(Q(1,2),1,0.1),(Q(1,2),1,-0.9)],Q(1,2),0,(0,1),(-2,2)))
        self.assertFalse(obstruction([(Q(1,2),1,'0.1'),(Q(1,2),1,'-0.9')],Q(1,2),0,(0,1),(-2,2)))
if __name__=='__main__': unittest.main()
