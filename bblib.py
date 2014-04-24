#Basic functionality used for the bluebird project"
import tweepy
import json


def load_config_file(config_file = "config"):
    """
    Load app specific credentials for the OAuth authentification
    """
    config = {}
    with open(config_file,'r') as f:
        for line in f:
            key,val = line.strip("\n").split("=")
            config[key] = val
    q = set(config.keys())^set(["consumer_key","consumer_secret", "access_token", "access_token_secret"])
    if len(q) == 0:
        return config
    else:
        print "Error: Config file needs consumer_key, consumer_secret, access_token, access_token_secret"

def connect_app_to_twitter(config_file = "config"):
    """
    Use credential in config file and use OAuth to connect to twitter. return the authentication and the api.
    """
    cfg = load_config_file(config_file)
    print cfg
    auth = tweepy.OAuthHandler(cfg["consumer_key"], cfg["consumer_secret"])
    auth.set_access_token(cfg["access_token"], cfg["access_token_secret"])
    api = tweepy.API(auth)
    api.rate_limit_status()
    return auth, api

###
###
#Test Connect to Stream
###
###

class DummyListener(tweepy.StreamListener):
    def on_data(self, data):
        d = json.loads(data)
        print d["text"]
        return True
    def on_error(self, status):
        print "error: ",
        print status

def test_stream():
    auth, api = connect_app_to_twitter("config")
    l = DummyListener()
    stream = tweepy.Stream(auth, l)
    stream.filter(track=['analytics','data'])
    

if __name__ == '__main__':
    load_config_file()
    connect_app_to_twitter()
    test_stream()