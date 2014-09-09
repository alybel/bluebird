#! /usr/bin/python -u

import bbanalytics as bba
import bblib as bbl
import config as cfg
import logging
import logging.handlers
import httplib
import sys
import pickle


formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# first file logger
logr = logging.getLogger('logger')
hdlr_1 = logging.handlers.RotatingFileHandler("bluebird.log", maxBytes=20000000, backupCount=1)
#hdlr_1 = logging.FileHandler('bluebird.log')
hdlr_1.setFormatter(formatter)
logr.setLevel(logging.INFO)
logr.addHandler(hdlr_1)

print "Retweet Score", cfg.retweet_score

verbose = True

def lp(s):
    """print this line if verbose is true """
    if verbose:
        print s

if cfg.dump_score > 0:
    # second file logger
    logr_2 = logging.getLogger('logger2')
    hdlr_2 = logging.handlers.RotatingFileHandler("bb_dump.log", maxBytes=20000000, backupCount=1)
    #hdlr_2 = logging.FileHandler('bb_dump.log')    
    hdlr_2.setFormatter(formatter)
    logr_2.setLevel(logging.INFO)
    logr_2.addHandler(hdlr_2)

def favorite_management(id, ca, api):
    #check if ID is already favorited. If yes, interrupt.
    if ca.isin(id):
        return True
    status = bbl.add_favorite(id, api)
    if not status:
        return False
    ca.add(id)
    next_entry = ca.get_next_entry()
    if next_entry:
        bbl.remove_favorite(next_entry, api)           
    ca.increase_count()
    bbl.ca_save_state(ca, "favorites")
    return True

def retweet_management(id, ca, api):
    logr.info("Entering Retweet Management")
    if ca.isin(id):
        return False
    rt_id = bbl.retweet(id, api)
    if not rt_id:
        return False
    ca.add(rt_id)
    next_entry = ca.get_next_entry()
    if next_entry:
        bbl.remove_retweet(next_entry, api)
    ca.increase_count()
    bbl.ca_save_state(ca, "retweets")
    return True

def follow_management(t, ca, api):
    if ca.isin(t.user_id):
        return False
    status = bbl.add_as_follower(t,api)
    if not status:
        return False
    ca.add(t.user_screen_name)
    next_entry = ca.get_next_entry()
    if next_entry:
        print next_entry
        bbl.remove_follow(next_entry, api)
    ca.increase_count()
    bbl.ca_save_state(ca, "follows")
    return True    


class tweet_buffer(object):
    def __init__(self, ca, api):
        self.buffer = []
        self.ca = ca
        self.api = api
        self.time = bba.minutes_of_day()
        print self.time, "time"
        print "initiate tweet buffer"
        logr.info("initiate tweet buffer")
    def add_to_buffer(self, t, score):
        print "added_to_buffer"
        if bba.minutes_of_day() - self.time > 0:
            self.time = bba.minutes_of_day()
            self.flush_buffer()            
            self.buffer = []
        self.buffer.append((score,t))
        
    def flush_buffer(self):
        print "Flush Buffer!"
        self.buffer.sort(reverse = True)
        for i in xrange(3):
            tweet = self.buffer[i][1]
            print self.time, self.buffer[i][0], tweet.text
            follow_management(tweet, ca = self.ca, api = self.api)
        return True

class FavListener(bbl.tweepy.StreamListener):
    def __init__(self, api):
        self.api = api
        #ca is a cyclic array that contains the tweet ID's there were favorited. Once the number_active_favorites is reached, 
        #the oldest favorite is automatically removeedd.
        self.ca = bbl.ca_initialize("favorites")
        self.ca_r = bbl.ca_initialize("retweets")
        self.ca_f = bbl.ca_initialize("follows")
        
        self.ca_recent_r = bbl.CyclicArray(100)
        self.ca_recent_f =  bbl.CyclicArray(100)
        
        self.ca.release_add_lock_if_necessary()
        self.ca_r.release_add_lock_if_necessary()
        self.ca_f.release_add_lock_if_necessary()
        
        self.CSim = bba.CosineStringSimilarity()
        self.tbuffer = tweet_buffer(api = self.api, ca = self.ca_f)
        
    def on_data(self, data):
        t = bbl.tweet2obj(data)
        #in case tweet cannot be put in object format just skip this tweet
        if not t:
            return True
        if t.user_screen_name == cfg.own_twittername:
            return True
        #Filter Tweets for language and location as in configuration
        if not bba.filter_tweets(t):
            return True
        #add score if tweet is relevant
        score = bba.score_tweets(t.text)
        if score >= 16:
            print t.text
        if score > cfg.favorite_score:
            if self.CSim.tweets_similar_list(t.text, self.ca_recent_f.get_list()):
                logr.info("favoriteprevented2similar;%s"%(t.id))
                return True
            success = favorite_management(t.id, self.ca, self.api)
            if success:
                self.ca_recent_f.add(t.text, auto_increase = True)
                self.ca_recent_f.cprint()
        if score >= cfg.retweet_score:
            print "enter retweet I"
            if self.CSim.tweets_similar_list(t.text, self.ca_recent_r.get_list()):
                logr.info("retweetprevented2similar;%s"%(t.id))
                return True
            print "enter retweet II"
            lp("score is,")
            lp(score)
            success = retweet_management(t.id, self.ca_r, self.api)
            print "enter retweet III"
            if success:
                self.ca_recent_r.add(t.text, auto_increase = True)
        if score >= cfg.follow_score:
            print "entering followers ares"
            self.tbuffer.add_to_buffer(t, score)         
        if cfg.dump_score > 0 and score > cfg.dump_score:
            print "Retweet Count", t.retweet_count
            if not t.retweet_count > 5:
                return True
            print "written to dump"
            logr_2.info("%s;%s;%s"%(t.user_screen_name, t.user_description, t.text))
        return True
            
            
    def on_error(self, status):
        print "error: ",
        print status
        

if __name__ == "__main__":
    auth, api = bbl.connect_app_to_twitter()
    l = FavListener(api)
    stream = bbl.tweepy.Stream(auth, l)
    logr.info("EngineStarted")
    while True:
        try:
            stream.filter(track=bba.manage_keywords(cfg.keywords).keys())
        except KeyboardInterrupt:
            logr.info("EngineEnded")
            logging.shutdown()
            sys.exit()
        except Exception,e:
            logr.error(e)          
            pass
#==============================================================================
#     except httplib.IncompleteRead,e:
#         print "Read Error detected <- Manual Messsage"
#         print e
#         logr.error(e)
#         sys.exit(0)
#==============================================================================
   # except Exception, e:
   #     logr.error(e)