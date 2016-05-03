import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import time
import json

def get_api(cfg):
  auth = tweepy.OAuthHandler(cfg['consumer_key'], cfg['consumer_secret'])
  auth.set_access_token(cfg['access_token'], cfg['access_token_secret'])
  return tweepy.API(auth)

def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            time.sleep(15*62)
            
        
#please fill in your credentials below
def main():
  cfg = { 
    "consumer_key"        : "",
    "consumer_secret"     : "",
    "access_token"        : "",
    "access_token_secret" : "" 
    }

  api = get_api(cfg)
  
  user_name = 'latimes'

  user = api.get_user(user_name)
  
  print user.screen_name

  #print user.friends_count
  
  #for friend in limit_handled(tweepy.Cursor(api.friends_ids,user_name).items()):
      #print friend
  #for friend in user.friends():
      #print friend.screen_name

  #print '---------'
  print user.followers_count
  for follower in limit_handled(tweepy.Cursor(api.followers_ids,user_name).items()):
      print follower
  #for follower in user.followers():
      #print follower.screen_name
      #print follower.id

if __name__ == "__main__":
  main()









