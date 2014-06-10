import bbanalytics as bba
import bblib as bbl
import sys
import pickle

def load_cyclicarray(name = ""):
    with open("%s.sav"%(name)) as f:
        return pickle.load(f)
        

def load_vector(name = ""):
    ca = load_cyclicarray(name)
    return ca.get_list()

def vec_stats(l = [], name = ""):
    print "vector Name:", name
    print "Length of array:", len(l)
    print "Number of non-None items", sum([1 for x in l if x])
    print "First five elements", l[:5]
    print "Last five elememts", l[-5:]

def stat(name = ""):
    l = load_vector(name)
    vec_stats(l, name)

if __name__ == "__main__":

    if len(sys.argv) == 1: 
        print "usage:"
        print "bb_tools.py fav_stat to show list of current favorites"
        sys.exit()
    arg = sys.argv[1]
    if arg == "fav_stat":
        stat("favorites")
    if arg == "ret_stat":
        stat("retweets")
    if arg == "fol_stat":
        stat("follows")  