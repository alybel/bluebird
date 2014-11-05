#! /usr/bin/python -u

import bbanalytics as bba
import bblib as bbl
import config as cfg
import logging
import logging.handlers
import httplib
import sys
import pickle
import config as cfg
import os.path
import time
import traceback
import random

appendix = ''

if os.path.isfile(".production"):
    appendix = "prod_"

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

# first file logger
logr = logging.getLogger('logger')
hdlr_1 = logging.handlers.RotatingFileHandler("bluebird.log", maxBytes=20000000, backupCount=1)
hdlr_1.setFormatter(formatter)
logr.setLevel(logging.INFO)
logr.addHandler(hdlr_1)

verbose = cfg.verbose

TextBuilder = bbl.BuildText(cfg.preambles, cfg.hashtags)

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

def favorite_management(t, ca, api):
    if random.random() > 0.3: return False
    #check if ID is already favorited. If yes, interrupt.
    if ca.isin(t.id):
        return True
    status = bbl.add_favorite(t.id, api)
    if not status:
        return False
    ca.add(t.id)
    next_entry = ca.get_next_entry()
    if next_entry:
        #try except needed becasue users may not exist anymore in the future. removing them would then throw an error
        try:bbl.remove_favorite(next_entry, api)
        except:pass
    ca.increase_count()
    bbl.ca_save_state(ca, "favorites")
    return True

def retweet_management(t, ca, api):
    if random.random() > 0.3: return False
    lp("Entering Retweet Management")
    if ca.isin(t.id):
        return False
    rt_id = bbl.retweet(t.id, api)
    if not rt_id:
        return False
    ca.add(rt_id)
    next_entry = ca.get_next_entry()
    if next_entry:
        #try except needed becasue retweets may not exist anymore in the future. removing them would then throw an error
        try: bbl.remove_retweet(next_entry, api)
        except: pass
    ca.increase_count()
    bbl.ca_save_state(ca, "retweets")
    return True

def follow_management(t, ca, api):
    bbl.cleanup_followers(api)
    lp("entering follow management")
    if ca.isin(t.user_id):
        return False
    status = bbl.add_as_follower(t,api, verbose = verbose)
    if not status:
        return False
    ca.add(t.user_screen_name)
    next_entry = ca.get_next_entry()
    if next_entry:
        try: bbl.remove_follow(next_entry, api)
        except: pass
    ca.increase_count()
    bbl.ca_save_state(ca, "follows")
    return True    


class tweet_buffer(object):
    def __init__(self, ca, api, management_fct, delta_time):
        self.buffer = []
        self.ca = ca
        self.api = api
        self.management_fct = management_fct
        self.delta_time = delta_time
        lp("initiate tweet buffer")
        logr.info("initiate tweet buffer")

    def add_to_buffer(self, t, score):
        if bba.minutes_of_day() % self.delta_time == 0:
            self.flush_buffer()            
            self.buffer = []
        else:
            self.buffer.append((score,t))
        
    def flush_buffer(self):
        lp("Flush Buffer!%s"%str(bba.minutes_of_day()))
        self.buffer.sort(reverse = True)
        for i in xrange(min(3,len(self.buffer))):
            try:
                tweet = self.buffer[i][1]
            except IndexError:
                print self.buffer
                raise
            args = (tweet, self.ca, self.api)
            #Introduce some randomness such that not everything is retweeted favorited and statused
            self.management_fct(*args)
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

        #Buffers for all 4 Types of Interaction
        self.tbuffer = tweet_buffer(api = self.api, ca = self.ca_f, management_fct=follow_management, delta_time=cfg.activity_frequency)
        self.tbuffer_rt = tweet_buffer(api = self.api, ca = self.ca_r, management_fct=retweet_management, delta_time = cfg.activity_frequency)
        self.tbuffer_fav = tweet_buffer(api = self.api, ca = self.ca, management_fct=favorite_management, delta_time = cfg.activity_frequency)
        #self.tbuffer_status = tweet_buffer(api = self.api, ca = self.ca_st, management_fct=follow_management)

    def on_data(self, data):
        t = bbl.tweet2obj(data)
        #in case tweet cannot be put in object format just skip this tweet
        if not t:
            return True
        if t.user_screen_name == cfg.own_twittername:
            return True
        #Filter Tweets for url in tweet, number hashtags, language and location as in configuration
        if not bba.filter_tweets(t):
            return True
        #add score if tweet is relevant
        score = bba.score_tweets(t.text, verbose = verbose)
        #Manage Favorites
        if score >= cfg.favorite_score:
            if self.CSim.tweets_similar_list(t.text, self.ca_recent_f.get_list()):
                logr.info("favoriteprevented2similar;%s"%(t.id))
                return True
            self.tbuffer_fav.add_to_buffer(t, score)
            self.ca_recent_f.add(t.text, auto_increase = True)
        #Manage Status Updates
        if score >= cfg.status_update_score:
            url = bba.extract_url_from_tweet(t.text)
            if url:
                text = TextBuilder.build_text(url)
                #Introduce some randomness such that not everything is automatically posted
                if text and random.random() > 0.5:
                    bbl.update_status(text = text, api = self.api)
        #Manage Retweets
        if score >= cfg.retweet_score:
            if self.CSim.tweets_similar_list(t.text, self.ca_recent_r.get_list()):
                logr.info("retweetprevented2similar;%s"%(t.id))
                return True
            self.tbuffer_rt.add_to_buffer(t, score)
            self.ca_recent_r.add(t.text, auto_increase = True)
        #Manage Follows
        if score >= cfg.follow_score:
            self.tbuffer.add_to_buffer(t, score)         
        if cfg.dump_score > 0 and score > cfg.dump_score:
            if not t.retweet_count > 5:
                return True
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
            logr.error("in main function; %s"%e)
            print "Exception in user code:"
            print '-'*60
            traceback.print_exc(file=sys.stdout)
            print '-'*60
            time.sleep(2)
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
