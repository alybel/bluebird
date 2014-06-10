#Basic functionality used for the bluebird project"
import tweepy
import json
import config as cfg
import bbanalytics
import logging
import pickle
import os.path

logr = logging.getLogger("logger")

class CyclicArray(object):
    def __init__(self, len = 0):
        self.l = len*[None]
        self.count = 0
        self.array_length = len
        self.add_lock = False
        self.inc_lock = False

    def reset(self):
        self.count = 0
        self.l = self.array_length*[None]
        self.add_lock = False
        self.inc_lock = False
        
    def cprint(self):
        print "Count: ", self.count
        print self.l
    
    def increase_count(self):
        if self.inc_lock:
            raise Exception("count increase is locked. First add new value to the cyclic array.")
        self.count += 1
        if self.count == self.array_length:
            self.count = 0
        self.inc_lock = True
        self.add_lock = False
            
    def add(self, entry, auto_increase = False):
        if self.add_lock:
            raise  Exception("add is locked. First increase count the add new values.")
        self.l[self.count] = entry
        self.add_lock = True
        self.inc_lock = False
        if auto_increase:
            self.increase_count()
    
    def get_current_entry(self):
        return self.l[self.count]
    
    def get_next_entry(self):
        if self.inc_lock:
            raise Exception("counter has already been incremented. Use current entry instead")
        if self.count == self.array_length - 1:
            return self.l[0]
        else:
            return self.l[self.count+1]

    def get_count(self):
        return self.count
    
    def get_array_length(self):
        return len(self.l)

    def get_list(self):
        return self.l
    
    def isin(self, x = 0):
        try:
            return self.l.index(x) >= 0
        except ValueError:
            return False
        
    def change_array_length(self, new_length):
        if new_length < len(self.l):
            self.l = self.l[:new_length -1]
        elif new_length > len(self.l):
            self.l.extend((new_length - len(self.l)) * [None])
        self.array_length = len(self.l)
        self.count = min(self.count, self.array_length -1)
        
    def release_add_lock_if_necessary(self):
        if self.add_lock:
            self.increase_count()
        
def get_ca_len(name = ""):
    if name == "favorites":
        return cfg.number_active_favorites
    if name == "retweets":
        return cfg.number_active_retweets
    if name == "follows":
        return cfg.number_active_follows

def ca_initialize(name = ""):
    if not os.path.isfile(name+".sav"):
        return CyclicArray(len = get_ca_len(name))
    else:
        ca = pickle.load(open(name+".sav", "rb"))
        if ca.get_array_length() != get_ca_len(name):
            print "length in config file has changed, tailoring..."
            ca.change_array_length(get_ca_len(name))
            print "new array length", ca.get_array_length()
        return ca

def ca_save_state(ca = None, name = ""):
    with open(name+".sav", 'w') as f:
        pickle.dump(ca, f)    

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
    if type(s) == type(1): return s
    return None if not s else s.encode('ascii', 'ignore')

def get_first_level_content(data, key):
    if not key in data:
        if cfg.verbose:
            print "key", key, "not found in tweet"
        return None
    return ru(data[key])

def tweet2obj(data):
    class t:pass
    data = json.loads(data)
    if cfg.verbose:
        print data
    t.text = get_first_level_content(data,"text")
    t.lan = get_first_level_content(data,"lang")
    t.created = get_first_level_content(data,"created_at")
    t.id = get_first_level_content(data, "id")
    t.favorite_count  = get_first_level_content(data, "favorite_count")
    t.retweet_count = get_first_level_content(data, "retweet_count")
    t.retweeted = get_first_level_content(data, "retweeted")
    user = data["user"]
    t.description = get_first_level_content(user,"description")
    t.loc = get_first_level_content(user, "location")
    t.user_lang = get_first_level_content(user, "lang")
    t.user_id = get_first_level_content(user, "id")
    t.user_name = get_first_level_content(user, "name")
    t.user_screen_name = get_first_level_content(user, "screen_name")
    t.user_description = get_first_level_content(user, "description")
    t.user_no_followers = get_first_level_content(user, "followers_count")
    return t

def print_tweet(t):
    print "-----"
    print t.text
    print t.loc
    print t.lan
    print t.retweet_count
    print t.favorite_count
    print t.created
    print t.retweeted
    print t.user_name
    print t.user_id
    print t.user_lang
    print t.user_screen_name
    print t.user_description
    print t.user_no_followers
    print "#####"

def add_favorite(id, api):
    try:
        api.create_favorite(id)
        print "favorite added"
        logr.info("Favorite;%s"%(id))
        return True
    except tweepy.error.TweepError, e:
        logr.info("FavoriteDenied;%s"%(id))
        logr.error(e)
        print e[0]
        return False

def remove_favorite(id, api):
    try:
        api.destroy_favorite(id)
        print "favorite removed"
        logr.info("FavoriteDestroyed;%s"%(id))
        return True
    except tweepy.error.TweepError, e:
        print e
        logr.debug(e)
        return False

def retweet(id, api):
    try:
        status = api.retweet(id)
        print "retweeted"
        logr.info("Retweet;%s;%s"%(id,status.id))
        return status.id
    except tweepy.error.TweepError, e:
        print e
        logr.info("RetweetDenied;%s"%(id))
        logr.error(e)
        return False
    
def remove_retweet(id, api):
    try:
        api.destroy_status(id)
        logr.info("RetweetDestroyed;%s"%(id))
        return True
    except tweepy.error.TweepError, e:
        print e
        logr.info("RetweetDestroyDenied;%s"%(id))
        logr.error(e)
        return False

def add_as_follower(t, api):
    if not t.user_lang in cfg.languages:
        logr.info("follow not carried out because language did not match")
        return False 
    try:
        status = api.create_friendship(t.user_id)
        print "followed", t.user_name, t.user_screen_name
        logr.info("following;%s,%s;%s;%s",t.user_id, t.user_name, t.user_screen_name, t.user_description)
        return True
    except tweepy.error.TweepError, e:
        print e
        logr.error(e)
        return False
        
def remove_follow(screen_name, api):
    if screen_name in cfg.accounts_never_delete:
        logr.info("unfollowprevented;%s"%(screen_name))
        return 
    try:
        status = api.destroy_friendship(screen_name)
        print "destroyed friendship", id
        logr.info("destroyedfriendship;%s",screen_name)
    except tweepy.error.TweepError, e:
        print e
        logr.error(e)
        
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