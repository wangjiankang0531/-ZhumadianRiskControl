import copy
import json
import unittest
from verify_native_lod_outcomes import PREFIX, reconcile


class OutcomeReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.events = [
            {'category':'root_runtime_budget','tile':141,'depth':3,'parent':'','reason':'Budget reached'},
            {'category':'family_runtime_budget','tile':141,'depth':4,'parent':'Tile_141_L19_0uuuu.osgb','reason':'Family budget reached'}]
        self.data = {'passed':True,'stations':[
            {'outcome_counts':{'root_runtime_budget':1},'failures':1,'budget_fallbacks':1},
            {'outcome_counts':{'root_runtime_budget':1,'family_runtime_budget':1},'failures':1,'budget_fallbacks':2}]}
    def lines(self):
        return [PREFIX+json.dumps(e) for e in self.events]
    def test_runtime_budget_has_distinct_legacy_failure_semantics(self):
        result=reconcile(self.data,self.lines())
        self.assertEqual((result['events'],result['failures'],result['runtimeBudgetFallbacks'],result['errorCount']),(2,1,2,0))
    def test_missing_or_duplicate_log_event_rejected(self):
        for lines in [self.lines()[:1],self.lines()+self.lines()[:1]]:
            with self.subTest(lines=lines),self.assertRaises(AssertionError):reconcile(self.data,lines)
    def test_counter_drift_and_decreasing_counter_rejected(self):
        for patch in [{'failures':0},{'budget_fallbacks':1},{'outcome_counts':{'family_runtime_budget':2}}]:
            data=copy.deepcopy(self.data);data['stations'][-1].update(patch)
            with self.subTest(patch=patch),self.assertRaises(AssertionError):reconcile(data,self.lines())
    def test_real_decode_error_is_retained(self):
        self.events.append({'category':'family_decode_error','tile':141,'depth':5,'parent':'Tile_141_L20_0uuuu0.osgb','reason':'Corrupt source'})
        end=self.data['stations'][-1];end['outcome_counts']['family_decode_error']=1;end['failures']=2
        result=reconcile(self.data,self.lines());self.assertEqual(result['errorCount'],1)
        self.assertEqual(result['errors'][0]['reason'],'Corrupt source')
    def test_unknown_category_and_wrong_family_parent_rejected(self):
        for patch in [{'category':'ignore_this_failure'},{'parent':'Tile_140_L19_0uuuu.osgb'}]:
            events=copy.deepcopy(self.events);events[1].update(patch)
            with self.subTest(patch=patch),self.assertRaises(AssertionError):reconcile(self.data,[PREFIX+json.dumps(e) for e in events])


if __name__=='__main__':unittest.main()