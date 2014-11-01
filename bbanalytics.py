import config as cfg
import re, math
from collections import Counter
import datetime
import logging
logr = logging.getLogger("logger")
import sys


languages = cfg.languages if cfg.languages != [] else None
locations = cfg.locations if cfg.locations != [] else None

#pre-process keywords
#can be deleted
#keywords = [str(x).lower().rstrip("s").replace("-","") for x in cfg.keywords]
#negative_keywords = [str(x).lower().rstrip("s").replace("-","") for x in cfg.negative_keywords]

def manage_keywords(d = {}):
    keylist = d.keys()    
    for key in keylist: 
        if " " in key: 
            kv = key.split(" ")
            for k in kv:
                d[k] = d[key]/2.
            d["".join(kv)] = d[key]
    return d

keywords = manage_keywords(cfg.keywords)
negative_keywords = cfg.negative_keywords
forbidden_keywords = cfg.forbidden_keywords

def generic_filter(entity, compare_list):
    if not compare_list: return True
    if not entity in compare_list: return False
    return True

def lan_filter(lan):
    return generic_filter(lan, languages)

def loc_filter(loc):
    return generic_filter(loc, locations)

def filter_tweets(t):
    if cfg.only_with_url and not is_url_in_tweet(t.text):
        return False
    if cfg.number_hashtags >= 0 and number_hashtags(t.text) > cfg.number_hashtags:
        return False
    return lan_filter(t.lan) and loc_filter(t.loc)

def split_and_clean_text(t = ""):
    t = t.lower()
    for p in [",","!","?",".","]","["]:
        t = t.replace(p," ")
    t = t.replace("-","")  
    #split t into pieces
    t = t.split(" ")
    #remove hashtags
    t = [x.lstrip("#") for x in t]
    #remove plural s
    t = [x.rstrip("s") for x in t if len(x) > 2]
    #Uniquifiy the list of words
    #buld tuples of 2 words
    tstar = [t[i] + " " + t[i+1] for i,x in enumerate(t) if i < len(t)-1]    
    t.extend(tstar)
    return list(set(t))

def number_hashtags(t):
    count = 0
    for character in t:
        if character == "#":
            count +=1
    return count

def score_tweets(t="", verbose = False):
    """
    input cleaned_text
    scan description for list of keywords as set in the config file. If any keyword matches, return True.
    The function will not return True on "data science" and "datascience"
    """
    q = t
    t = split_and_clean_text(t)
    score = 0
    for word in t:
        if word in keywords:
            score += keywords[word]
        if word in negative_keywords:
            score -= 10
        if word in forbidden_keywords:
            score -= 1000
    if score >=0 and verbose:
        logr.info("TestTweet;%d;%s:%s"%(score,q,t))
        print score
        print q
        print t
    return score

def is_url_in_tweet(t = ""):
    if "http" in t: 
        return True
    return False

def extract_url_from_tweet(t = ""):
    "extract url from a string. Check if url is more than 18 characters, as for example: http://bit.ly/fi23uhf"
    q = t.split(" ")
    for word in q:
        if "http" in word and len(word) > 18:
            return word

class CosineStringSimilarity(object):
    def __init__(self):
        filling_words = ["in", "to", "a", "http", "as", "of", "and", "or", "it", "is", "on", "the"]
        filling_words.extend(cfg.keywords)
        self.filling_words = [x.lower() for x in filling_words]
        self.WORD = re.compile(r'\w+')
        
    def get_cosine(self, vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        else:
            return float(numerator) / denominator
        
    def text_to_vector(self,text):
        words = self.WORD.findall(text)
        words = [x.lower() for x in words]
        words = list(set(words) - set(self.filling_words))
        return Counter(words)
    
    def tweets_similar(self, t1, t2):
        vector1 = self.text_to_vector(t1)
        vector2 = self.text_to_vector(t2)
        similarity = self.get_cosine(vector1, vector2)
        return similarity > 0.6
    
    def tweets_similar_list(self, t, tl = []):
        for t2 in tl:
            if not t2:
                continue
            if self.tweets_similar(t, t2):
                return True
        return False
            
            
def minutes_of_day():
    """

    :rtype : datetime
    """
    return  datetime.datetime.now().time().minute + datetime.datetime.now().time().hour * 60
 
if __name__ == "__main__":
    assert(lan_filter("fr") == False)
    assert(loc_filter("usa") == True)
