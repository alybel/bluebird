#!/usr/bin/python -u

__author__ = 'alex'

import bblib as bbl
import bbanalytics as bba

auth, api = bbl.connect_app_to_twitter()

def get_friends_ids():
    """
    returns a vector or ids of users who follow me.
    :return: list
    """
    return api.followers()

def remove_people_who_dont_follow_back():
    users = get_friends_ids()
    print api.lookup_friendships(users), user


def test_tweet_scores():
    print "testing historic tweets saved in logfile"
    f = open("bluebird.log", 'r')
    for line in f:
        lv = line.split(';')
        if "TestTweet" in lv[0]:
            if "job" in line:
                print lv[2].split(':')[0]


if __name__ == '__main__':
    test_tweet_scores()

