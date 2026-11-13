"""Boundary checks independent of model inference and CVAT availability."""
import copy
import unittest
from run import reviewed, deduplicate, signature, SCHEMA, protect_annotations, fingerprint
from collections import Counter

class Boundaries(unittest.TestCase):
    def prediction(self):
        return {'image':'x.jpg','key':'key','width':100,'height':100,
                'objects':[{'points':[[50,50,.01] for _ in range(17)]}]}

    def test_confidence_is_not_visibility(self):
        p=self.prediction()
        self.assertEqual({x['v'] for x in reviewed(p,'persons',{})[0]['points']},{0})
        review={'x.jpg':{'prediction_key':'key','objects':{'0':{'default_v':2}}}}
        self.assertEqual({x['v'] for x in reviewed(p,'persons',review)[0]['points']},{2})

    def test_outside_and_occlusion(self):
        p=self.prediction(); p['objects'][0]['points'][0]=[100,50,.99]
        review={'x.jpg':{'prediction_key':'key','objects':{'0':{'default_v':2,'points':{'left_eye':{'v':1}}}}}}
        pts=reviewed(p,'persons',review)[0]['points']
        self.assertEqual([pts[0]['v'],pts[1]['v'],pts[2]['v']],[0,1,2])

    def test_stale_review_and_invalid_coordinate(self):
        p=self.prediction()
        with self.assertRaises(ValueError): reviewed(p,'persons',{'x.jpg':{'prediction_key':'old'}})
        p['objects'][0]['points'][0][0]=float('nan')
        with self.assertRaises(ValueError): reviewed(p,'persons',{})

    def test_duplicate_and_distinct_people(self):
        items=[{'bbox':[0,0,100,200],'score':.9},{'bbox':[2,2,100,200],'score':.8},
               {'bbox':[120,0,200,200],'score':.7}]
        self.assertEqual(len(deduplicate(items)),2)

    def test_contained_low_score_fragment(self):
        items=[{'bbox':[0,0,100,100],'score':.9},{'bbox':[0,0,100,250],'score':.3},
               {'bbox':[120,0,200,200],'score':.8}]
        self.assertEqual(len(deduplicate(items)),2)

    def test_signature_preserves_visibility_ignores_order(self):
        s={'frame':0,'label_id':1,'type':'skeleton','elements':[
            {'label_id':2,'points':[1,2],'outside':False,'occluded':False},
            {'label_id':3,'points':[3,4],'outside':True,'occluded':False}]}
        t=copy.deepcopy(s); t['elements'].reverse()
        self.assertEqual(signature(s),signature(t))
        t['elements'][0]['outside']=False
        self.assertNotEqual(signature(s),signature(t))

    def test_external_edits_and_pending_save_recovery(self):
        shape={'frame':0,'label_id':1,'type':'skeleton','elements':[
            {'label_id':2,'points':[1,2],'outside':False,'occluded':False}]}
        saved={'shapes':[shape],'tags':[],'tracks':[],'version':1}
        row={'annotations_hash':fingerprint(saved)}
        changed=copy.deepcopy(saved);changed['shapes'][0]['elements'][0]['points'][0]=5
        desired=Counter(map(signature,changed['shapes']))
        with self.assertRaises(RuntimeError):protect_annotations(changed,row,desired)
        row['pending_signature']=dict(desired)
        self.assertEqual(protect_annotations(changed,row,desired),desired)
        changed['tags']=[{'label_id':3}]
        with self.assertRaises(RuntimeError):protect_annotations(changed,row,desired)

if __name__=='__main__': unittest.main()
