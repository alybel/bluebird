import bbanalytics as bba
import bblib as bbl
import config as cfg
import logging

#Set up the Logger that is used throughout the whole program
LOGFILE = "bluebird.log"
logging.basicConfig(filename = LOGFILE,    
                    level = logging.INFO, 
                    format = "%(asctime)s [%(levelname)-8s] %(message)s") 
logr = logging.getLogger("logger")
handler = logging.handlers.RotatingFileHandler(
              LOGFILE", maxBytes=20, backupCount=1)
logr.addHandler(handler)

def favorite_management(id, ca, api):
    #check if ID is already favorited. If yes, interrupt.
    if ca.isin(id):
        return True
    bbl.add_favorite(id, api)
    ca.add(id)
    next_entry = ca.get_next_entry()
    if next_entry:
        bbl.remove_favorite(next_entry, api)           
    ca.increase_count()
    bbl.ca_save_state(ca, "favorites")
    return True

def retweet_management(id, ca, api):
    if ca.isin(id):
        return True
    rt_id = bbl.retweet(id, api)
    ca.add(rt_id)
    next_entry = ca.get_next_entry()
    if next_entry:
        bbl.remove_retweet(next_entry, api)
    ca.increase_count()
    bbl.ca_save_state(ca, "retweets")
    return True

def follow_management(t, ca, api):
    if ca.isin(t.user_id):
        return True
    status = bbl.add_as_follower(t,api)
    if not status:
        return True
    ca.add(t.user_id)
    next_entry = ca.get_next_entry()
    if next_entry:
        bbl.remove_follow(next_entry, api)
    ca.increase_count()
    bbl.ca_save_state(ca, "follows")
    return True
    

class FavListener(bbl.tweepy.StreamListener):
    def __init__(self, api):
        self.api = api
        #ca is a cyclic array that contains the tweet ID's there were favorited. Once the number_active_favorites is reached, 
        #the oldest favorite is automatically removeedd.
        self.ca = bbl.ca_initialize("favorites")
        print "current favorites"
        self.ca.cprint()
        self.ca_r = bbl.ca_initialize("retweets")
        print "current retweets"
        self.ca_r.cprint()
        self.ca_f = bbl.ca_initialize("follows")
        print "current follows"
        self.ca_f.cprint()
        
    def on_data(self, data):
        t = bbl.tweet2obj(data)
        if t.user_screen_name == "AlexanderD_Beck":
            return True
        #Filter Tweets for language and location as in configuration
        if not bba.filter_tweets(t):
            return True
        #add score if tweet is relevant
        score = bba.score_tweets(t.text)
        if score > 2:
            bbl.print_tweet(t)
            favorite_management(t.id, self.ca, self.api)
            retweet_management(t.id, self.ca_r, self.api)
        if score > 2:
            follow_management(t, self.ca_f, self.api)
            
    def on_error(self, status):
        print "error: ",
        print status

if __name__ == "__main__":
    auth, api = bbl.connect_app_to_twitter()
    l = FavListener(api)
    stream = bbl.tweepy.Stream(auth, l)
    logr.info("FavoritesEngineStarted")
    try:
        stream.filter(track=cfg.keywords)
    except KeyboardInterrupt:
        logr.info("FavoritesEngineEnded")
        logging.shutdown()