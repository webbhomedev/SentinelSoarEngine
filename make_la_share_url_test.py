import unittest
from make_la_share_url.make_la_share_url import make_share_url
import pprint as pp

class TestMakeJob(unittest.TestCase):
    def setUp(self):
        self.test_query = "SigninLogs | take 1"
        self.sub_id = "some_guid"
        self.resource_g = "my_resources"
        self.workspace_n = "my_sentinel01"
        return super().setUp()

    def testReturnCode(self):
        exit_c, url = make_share_url(query=self.test_query,
                                     subscription_id=self.sub_id, 
                                     resource_group=self.resource_g,
                                     workspace_name=self.workspace_n)
        # non-zero exit code
        self.assertFalse(exit_c)
        

    def testReturnedExpectedUrl(self):
        expected_resource = "%2Fsubscriptions%2Fsome_guid%2FresourceGroups%2Fmy_resources%2Fproviders%2FMicrosoft.OperationalInsights%2Fworkspaces%2Fmy_sentinel01"
        exit_c, url = make_share_url(query=self.test_query,
                            subscription_id=self.sub_id, 
                            resource_group=self.resource_g,
                            workspace_name=self.workspace_n)
        
        
        self.assertTrue(expected_resource in url, 'Did not match expected URL')
    
    
    def testLongerStringWithQueryNow(self):
        exit_c, url_with = make_share_url(query=self.test_query,
                                     subscription_id=self.sub_id, 
                                     resource_group=self.resource_g,
                                     workspace_name=self.workspace_n, 
                                     set_query_now=True)
        exit_c, url_without = make_share_url(query=self.test_query,
                                     subscription_id=self.sub_id, 
                                     resource_group=self.resource_g,
                                     workspace_name=self.workspace_n, 
                                     set_query_now=False)


        self.assertGreater(len(url_with), len(url_without), 'Does not look like additional data got added')
        
        print("Manual test can be done with the below link:")
        print(url_with)
        

if __name__ == '__main__':
    unittest.main()