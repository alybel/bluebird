import mytwitter
from tweepy.streaming import StreamListener
from tweepy import Stream
import json
import sqlite3
import datetime
import sys

#TODO: Catch Error Code 161



approached_tablename = "people"
keywords = mytwitter.get_keywords()
today = datetime.date.today()
conn = sqlite3.connect("userman.db")
c = conn.cursor()
new_people_per_run = 500
current_number_friends = 0

languages = mytwitter.get_languages()
min_score_add = mytwitter.get_min_score_add()

def commit():
    print "Committed to database"
    conn.commit()

def add_user_to_db(user_name = "", user_id = "", d = ""):
    c.execute("INSERT INTO people VALUES(?,?,?,?,?,?,?,?)", ("null", user_name, user_id, 'null','null','null',"0", d))
    commit()
    
def check_number_friends_initialized():
    global current_number_friends
    if current_number_friends == 0:
        print "Current_number_friends not set. Run update first"
        sys.exit()
    
def ru(s = ""):
    """
    resolve unicode and return printable string
    """
    return s.encode('ascii', 'ignore')
       
class StdOutListener(StreamListener):
    def __init__(self, api, verbose = False):
        self.verbose = verbose
        self.count = 0
        self.api = api
    def on_data(self, data):
        if self.count >= new_people_per_run:
            return False
        q = json.loads(data)
        try:
            t = ru(q["text"])
            u = q["user"]
            d = ru(u["description"])
            lan = q["lang"]
        except:
            return True
        if not lan in languages: return True
        #if not mytwitter.demographics_to_follow_user(language = lan, location = loc, name = name):
        #    return True
        user, twitter_id = None, None
        score = mytwitter.filter_description_by_keywords("%s,%s"%(d,t), keywords)
        if d and t and score > min_score_add:
            twitter_id = u["id"]
            user = u["screen_name"] 
        if user and twitter_id:
            try:
                print d
                add_user_to_db(user, twitter_id, d)
                follow_new(user, twitter_id, self.api)
                self.count += 1
                if self.count > 1990:
                    print "maximum number adds reached"
                    sys.exit(0)
            except sqlite3.IntegrityError: 
                print "double entry prevented", twitter_id
                c.execute("UPDATE people SET description = ? where twitter_id = ?",(d, twitter_id))
                commit()
                print "updated description for", user
                return True
            except UnicodeEncodeError:
                print "pass due to encoding error"
            sys.stdout.write("Added User: %s Count: %d \n" % (user, self.count) )
            sys.stdout.flush()
        return True
    def on_error(self, status):
        print "error: ",
        print status

def follow_new(screen_name, twitter_id, api):
    """
    follow a twitter user. Store date of following.
    """
    try:
        api.create_friendship(screen_name)
        c.execute("UPDATE people SET date_added = '%s', i_follow = 1 where twitter_id = %s" % (str(today), twitter_id))
        print "Now following", screen_name
    except Exception,e:
        print e.message
        error_code = e.message[0]["code"] 
        if error_code == 34:
            c.execute("DELETE from people where screen_name = ?",(screen_name,))
            commit()
        elif error_code == 161: 
            print "rejected because of adding to many users"
            sys.exit()
    

def follow_new_people(api = None):
    global current_number_friends
    if current_number_friends == 0:
        print "Current_number_friends not set. Run update first"
        return
    cur = c.execute("select screen_name, twitter_id from people where i_follow != 1 and date_added = 'null' and is_follower != 1")
    l = []
    print "adding people..."
    try:
        for i in cur:
            screen_name = i[0]
            twitter_id = i[1]
            if current_number_friends >= 2500:
                print "number of friends limit 1990 reached. delete people before you run again."
                break
            try:
                api.create_friendship(screen_name)
            except Exception, e:
                print e
                if e.message[0]["code"]==34:
                    c.execute("DELETE from people where screen_name = ?",(screen_name,))
                    commit()
            l.append(twitter_id)
            current_number_friends += 1
            print current_number_friends
            print "now following...",screen_name
    except Exception, e:
        print e
    for twitter_id in l:
        c.execute("UPDATE people SET date_added = '%s', i_follow = 1 where twitter_id = %s" % (str(today), twitter_id))
        print "adding", twitter_id, "to database"
    commit()



def follow_people_again(api = None, days_go_back_in_past = 40):
    from_date = today - datetime.timedelta(days_go_back_in_past)
    cur = c.execute("select screen_name, twitter_id from people where i_follow != 1 and date_deleted <= '%s'  and is_follower != 1"%(str(from_date)))
    l = []
    print "re-adding people..."
    try:
        for i in cur:
            screen_name = i[0]
            twitter_id = i[1]
            print "now re-following...",screen_name
            api.create_friendship(screen_name)
            l.append(twitter_id)
    except:
        print sys.exc_info()[0]
    for twitter_id in l:
        c.execute("UPDATE people SET date_added = '%s', i_follow = 1, number_of_refollows = number_of_refollows + 1 where twitter_id = %s" % (str(today), twitter_id))
        print "re-adding", twitter_id, "to database"
    commit()
        
def parse_stream_for_new_people(auth = None, api = None, verbose = True):
    check_number_friends_initialized()
    l = StdOutListener(api, verbose)
    stream = Stream(auth, l)
    stream.filter(track=keywords)


def update_my_followers(api = None):
    global current_number_friends
    count = 0
    c.execute("UPDATE people SET is_follower = 0")
    c.execute("UPDATE people SET i_follow = 0")
    c.execute("UPDATE people SET date_deleted = '%s' where date_deleted = 'null' and is_follower = 0 and i_follow = 0"%(str(today)))
    for follower_id in api.followers_ids("AlexanderD_Beck"):
        try:
            c.execute("UPDATE people SET is_follower = 1 where twitter_id = %s"%(follower_id))
            count += 1
        except sqlite3.IntegrityError:
            print friends_id, "not found in database"
    print "detected", count, "followers"
    count = 0
    for friends_id in api.friends_ids("AlexanderD_Beck"):
        try:
            c.execute("UPDATE people SET i_follow = 1 where twitter_id = %s"%(friends_id))
            count += 1
        except sqlite3.IntegrityError:
            print friends_id, "not found in database"
    print "found", count, "people I follow"
    current_number_friends = count
    commit()

def cleanup_old_followers(api, days_go_back_in_past = 2):
    delete_before_date = today - datetime.timedelta(days_go_back_in_past)
    print "delete all non-followers prior to", delete_before_date
    cur = c.execute("SELECT screen_name, date_added FROM people where i_follow = 1 and is_follower != 1 and date_added <= '%s'"%delete_before_date)
    count = 0
    l = []
    for item in cur:
        tname = item[0]
        try:
            mytwitter.destroy_friendship(api, tname)
            l.append(tname)
        except Exception, e:
            print str(e)
            print "error when trying to destroy friendship"
        count += 1
    for sn in l:
        print sn
        c.execute("update people set date_deleted = '%s' where screen_name like '%s'"%(str(today), sn))
        c.execute("update people set i_follow = 0 where screen_name like '%s'"%(sn))
    print "deleted", count, "friends from account"
    commit()
    
def add_descriptions():
    print "adding descriptions"
    import time
    cur = c.execute("SELECT twitter_id, screen_name, description FROM people")
    l = cur.fetchall()
    #select entries with no description
    l = [(x[0], x[1]) for x in l if not x[2]]
    count = 0
    for x in l:
        time.sleep(2)
        try:
            friend = api.get_user(id = x[0])
            c.execute("UPDATE people SET description = ? where twitter_id = ?", (friend.description, x[0]))
            conn.commit()
            count += 1
            print count
        except Exception,e:
            #raise
            try:
                code = e.message[0]["code"]
            except:
                print "####",e,"####"
                raise
            if code == 34:
                #page does not exist
                print "page does not exist for", str(x[0])
                twitter_id = str(x[0])
                c.execute("DELETE from people where twitter_id = ?", (twitter_id,))
                commit()
            if code == 88:
                #rate exceeded
                print "\n rate limit exceeded, waiting for 5 minutes"
                count = 0
                time.sleep(300)
        
        

                    
if __name__ == '__main__':
    auth, api = mytwitter.connect_and_return_auth()
    #STEP 0 #update List of followers
    update_my_followers(api)
    cleanup_old_followers(api, days_go_back_in_past = 1)
    update_my_followers(api)
    #STEP 1 - Get New People to add
    #follow_new_people(api)
    #update_my_followers(api)
    parse_stream_for_new_people(auth, api, verbose = True)
    #STEP 2 - Add the new People
    #follow_new_people(api)
    #follow_people_again(api, days_go_back_in_past = 40)
    
    update_my_followers(api)
    add_descriptions()
    conn.close()
    
