import unittest
import os
from make_job import *

class TestMakeJob(unittest.TestCase):
    def setUp(self):
        self.sample_incident_fn = 'payload.json'
        
        self.sample_enrichment_job = {
            "item-type": "SOAR-trigger",
            "entity-type": "url",
            "query": "let LookFor = \"%ENTITY%\";\nSignInLogs | where UserPricipalName == LookFor",
            "additional_params": {
                "severity_change": [
                    {
                        "results_count_mt": 1,
                        "severity": "Informational"
                    }
                ]
            }
        }

        return super().setUp()

    def makeSampleJob(self):
        import json
        
        with open(self.sample_incident_fn, "r") as f:
            SAMPLE_SENTINEL_INC = json.load(f)
        SAMPLE_SENTINEL_INC = SAMPLE_SENTINEL_INC["body"]
        
        AZ_FUNC_PAYLOAD = {"enrichment_job":self.sample_enrichment_job, "sentinel_incident":SAMPLE_SENTINEL_INC}
        return AZ_FUNC_PAYLOAD
    
    def testIncidentFile(self):
        self.assertTrue(os.path.exists(self.sample_incident_fn), 'sample incident filename does not exist')
    
    def testIncidentFileJson(self):
        import json
        opened=False
        
        try:
            with open(self.sample_incident_fn, "r") as f:
                SAMPLE_SENTINEL_INC = json.load(f)
                 
            opened=True
        except:
            opened = False
            
        self.assertTrue(opened, "Supplied file is not JSON")
        
    def testGenerateJob(self):
        import json
        import pprint as pp
        from make_job import main_funct
        
        sample_job = self.makeSampleJob()

        resp, result_code  = main_funct(sample_job)
        pp.pprint(resp)
        
        self.assertTrue(result_code >= 200 and result_code < 300, 'Returned non 200 result code')

    def testNoWarningsResp(self):
        from make_job import main_funct
        
        sample_job = self.makeSampleJob()
        resp, result_code  = main_funct(sample_job)
        
        self.assertFalse(resp['warnings'])
        
    def testNoErrors(self):
        from make_job import main_funct
        
        sample_job = self.makeSampleJob()
        resp, result_code  = main_funct(sample_job)
        
        self.assertFalse(resp['errors'])
        
if __name__ == '__main__':
    unittest.main()