#/usr/bin/python -u

__author__ = 'alex'
import bblib as bbl
import tweepy
import bbanalytics as bba

class DummyListener(tweepy.StreamListener):
    def __init__(self, accounts, topics):
        self.accounts = accounts
        self.topics = topics
    def on_data(self, data):
        tweet = bbl.tweet2obj(data)
        if not tweet: return True
        t = bba.split_and_clean_text(tweet.text)
        #t = ["vw", "big data"]
        check_account = False
        check_topic = False
        for key in self.accounts:
            if key in t:
                check_account = True
                break
        for key in self.topics:
            if key in t:
                check_topic = True
                break
        if check_account and check_topic:
            print
            print t
            print
        print '.',
        return True
    def on_error(self, status):
        print "error: ",
        print status
        return False

def test_stream():
    print "running test_stream"
    auth, api = bbl.connect_app_to_twitter()
    accounts = ["bmw","daimler","vw","audi","gm","ford","toyota","kia","honda","porsche"]
    topics = ["data science","datascience","bigdata", "big data", "data analytics", "big data analytics", "smart data"]
    l = DummyListener(accounts = accounts, topics = topics)
    stream = tweepy.Stream(auth, l)
    keywords = accounts + topics
    print keywords
    while True:
        try:
            stream.filter(track=keywords)
        except Exception, e:
            print e
            pass



def monitor_activity():
    test_stream()


if __name__ == "__main__":
    auth, api = bbl.connect_app_to_twitter()
    monitor_activity()

