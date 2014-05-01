import bbanalytics as bba
import bblib as bbl

import unittest

class TestCyclicArrays(unittest.TestCase):
    def setUp(self):
        self.array_length = 3
        self.ca = bbl.CyclicArray(self.array_length)
    
    def test_ca_length(self):
        self.assertEqual(self.array_length,self.ca.get_array_length())
    
    def test_reset(self):
        self.ca.reset()
        self.assertEqual(self.array_length,self.ca.get_array_length())
        self.assertEqual(self.ca.get_list(),[None,None,None])

    def test_cycle_through(self):
        self.assertEqual(self.ca.get_current_entry(), None)
        self.ca.add(1)
        self.assertRaises(Exception,self.ca.add)
        self.assertEqual(self.ca.get_count(), 0)
        self.assertEqual(self.ca.get_current_entry(), 1)
        self.ca.increase_count()
        self.assertEqual(self.ca.get_count(), 1)
        self.assertRaises(Exception, self.ca.increase_count)
        self.ca.add(2)
        self.ca.increase_count()
        self.ca.add(3)
        self.assertEqual(self.ca.get_next_entry(),1)
        self.ca.increase_count()
        self.assertRaises(Exception,self.ca.get_next_entry)
        self.ca.cprint()
        self.assertEqual(self.ca.get_list(), [1,2,3])
        self.assertEqual(self.ca.get_count(), 0)
        self.ca.add(4)
        self.assertEqual(self.ca.get_list(), [4,2,3])
        self.assertEqual(self.ca.get_next_entry(),2)
        self.ca.reset()
        self.assertEqual(self.ca.get_list(),[None,None,None])
        self.ca.add(4)
        self.ca.increase_count()
        self.ca.add(4)
        self.ca.increase_count()
        self.ca.add(4)
        self.ca.increase_count()
        self.assertTrue(self.ca.isin(4))
        self.assertTrue(not self.ca.isin(5))
    

class TestBblibFunctionality(unittest.TestCase):
    def setUp(self):
        self.tweet = "What new methods or tools are #CIOs using to tackle #analytics and business intelligence? http://t.co/hGuZ5u8dIT Washington DC" 
        self.tweet2 = "What new methods or tools are #CIOs using to tackle #analytics and business intelligence? //t.co/hGuZ5u8dIT Washington DC" 
    
    def test_count_number_hashtags(self):
        self.assertEqual(bba.number_hashtags(self.tweet),2)
        
    def test_is_url_in_tweet(self):
        self.assertTrue(bba.is_url_in_tweet(self.tweet))
        self.assertTrue(not bba.is_url_in_tweet(self.tweet2))
    
class TestTweetSimilarity(unittest.TestCase):
    def setUp(self):
        self.t1 = "Offshore Bank Account | Business in Gujarat | Gateway to Startups and Entrepreneurship http://dlvr.it/5XXSYt" 
        self.t2 = "RT @fasiufa Offshore Bank Account | Business in Gujarat | Gateway to Startups and Entrepreneurship htt://adfr.i"
        self.t3 = "Six steps to a successful small business : 6 articles and videos | Business in Gujarat | Gateway to Startups and... http://dlvr.it/5XXSXq"
        self.CSim = bba.CosineStringSimilarity()
    def test_for_same(self):
        self.assertTrue(self.CSim.tweets_similar(self.t1, self.t1))
    def test_for_similar(self):
        self.assertTrue(self.CSim.tweets_similar(self.t1,self.t2))
    def test_for_not_similar(self):
        self.assertTrue(not self.CSim.tweets_similar(self.t1,self.t3))


if __name__ == "__main__":
    unittest.main()