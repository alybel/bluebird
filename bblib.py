#Basic functionality used for the bluebird project"
import tweepy
import json
import config as cfg
import bbanalytics

def connect_app_to_twitter():
    """
    Use credential in config file and use OAuth to connect to twitter. return the authentication and the api.
    """
    auth = tweepy.OAuthHandler(cfg.consumer_key, cfg.consumer_secret)
    auth.set_access_token(cfg.access_token, cfg.access_token_secret)
    api = tweepy.API(auth)
    api.rate_limit_status()
    return auth, api

def ru(s = ""):
    """
    resolve unicode and return printable string
    """
    return None if not s else s.encode('ascii', 'ignore')

def get_first_level_content(data, key):
    return None if not key in data else ru(data[key])

def tweet2obj(data):
    class t:pass
    data = json.loads(data)
    t.text = get_first_level_content(data,"text")
    t.lan = get_first_level_content(data,"lang")
    t.created = get_first_level_content(data,"created_at")
    user = data["user"]
    t.description = get_first_level_content(user,"description")
    return t

###
###
#Test Connect to Stream
###
###

class DummyListener(tweepy.StreamListener):
    def on_data(self, data):
        tweet = tweet2obj(data)
        print tweet.text
        print tweet.created
        return True
    def on_error(self, status):
        print "error: ",
        print status

def test_stream():
    auth, api = connect_app_to_twitter()
    l = DummyListener()
    stream = tweepy.Stream(auth, l)
    stream.filter(track=cfg.keywords)
    
if __name__ == '__main__':
    connect_app_to_twitter()
    test_stream()