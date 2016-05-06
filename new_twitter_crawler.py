import tweepy
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
import time
import json
import sys
import getopt
import cPickle as pickle


def get_api(cfg):
  auth = tweepy.OAuthHandler(cfg['consumer_key'], cfg['consumer_secret'])
  auth.set_access_token(cfg['access_token'], cfg['access_token_secret'])
  return tweepy.API(auth)


def limit_handled(cursor):
    while True:
      try:
        yield cursor.next()
      except tweepy.RateLimitError:
        logging_file.write('Waiting on cursor request \n')
        time.sleep(15*62)
      except tweepy.TweepError:
          logging_file.write("Failed to run the command on that user, Skipping... \n")


def limit_handled_user(user_name, api):
  while True:
    try:
      user = api.get_user(user_name)
      return user
    except tweepy.RateLimitError:
      logging_file.write('Waiting on user request for ' + user_name + '\n')
      time.sleep(15*62)
    except tweepy.TweepError:
      logging_file.write("Failed to run the command on that user, Skipping... \n")


def limit_handled_user_batch(user_ids, api):
  while True:
    try:
      users = api.lookup_users(user_ids)
      return users
    except tweepy.RateLimitError:
      logging_file.write('Waiting on user request for batch \n')
      time.sleep(15*62)
    except tweepy.TweepError:
      logging_file.write("Failed to run the command on that user, Skipping... \n")


logging_file = ""
  

# please fill in your credentials below
def main():
  try:
    opts, args = getopt.getopt(sys.argv[1:], 'i', ['User=', 'Degree='])

    user = ""
    degree = ""

    for o, a in opts:
      if o == '--User':
        user = a
      if o == '--Degree':
        degree = int(a)

  except getopt.GetoptError:
    print 'expected: twitter_crawler.py --User=berniesanders --Degree=2'
    sys.exit(2)

  if user == "":
    print "No user specified"
    sys.exit(1)

  logging_file = open(str(user) + ".log", 'w')
  logging_file.truncate()

  cfg = { 
    "consumer_key"        : "nWpbEeehwRkGCfCEMZOAMKuwY",
    "consumer_secret"     : "zKKaG2u4ZAmW0yRptl3eORd8C0ns5uZ40OQYi0MlPLKdrIP8sr",
    "access_token"        : "203359959-uByJ9E2oIbIrjh1i6NBt5AdZdZBiUaKnjrULOV3d",
    "access_token_secret" : "zxorRmLIxxxTj8oB4PqPB7WbEcfvxRs6xZ2QnYpvU06lB" 
    }

  api = get_api(cfg)

  user_name = user

  user = limit_handled_user(user_name, api)

  logging_file.write('Size of user object: ' + str(sys.getsizeof(user)) + '\n')

  logging_file.write(user.screen_name)
  logging_file.write('Number of followers: ' + str(user.followers_count) + '\n')

  createNetwork(user, degree, api)

def getUsernameListAsString(userList):
    listString = ""

    for user in userList:
        listString = listString + ", " + user.screen_name

    return listString[2:]

# Pretty print the network as user : list
def prettyPrintNetwork(network):
  for screen_name, followers in network.items():
    print screen_name , ':' , getUsernameListAsString(followers)

# Create a degreeth network for the given user
def createNetwork(user, degree, api):
  network = {}

  nextLayerOfFollowers = set()
  nextLayerOfFollowers.add(user)

  #For each degree of the network
  for i in range(0, degree):
    logging_file.write('Adding layer ' + str((i + 1)) + '\n')
    network, nextLayerOfFollowers = getLayer(network, nextLayerOfFollowers, api)
    logging_file.write('Layer added less following. Pretty printing layer: \n')
    prettyPrintNetwork(network)
    logging_file.write('----- \n')

    logging_file.write("Network created less following. Adding following. \n")

  # Iterate over user_name, get following and add
  for currentUserScreenName , setOfFollowers in network.items():

    count = 0
    currentBatch = []

    #Add this person to all of the people they're following's inward edges
    for currentFollowedUserId in limit_handled(tweepy.Cursor(api.friends_ids,currentUserScreenName).items()):
      currentBatch.append(currentFollowedUserId)
      count = count + 1

      if count == 100:
        network = getFollowingBatch(currentUserScreenName, currentBatch, network, api)

  network = getFollowingBatch(currentUserScreenName, currentBatch, network, api)

  prettyPrintNetwork(network)

  pickle.dump(network, open(user.screen_name + ".pickle", "wb"))


# get a batch of users that the given user is following
def getFollowingBatch(currentUserScreenName, currentBatch, network, api):
  currentBatchSet = limit_handled_user_batch(currentBatch, api)

  for u in currentBatchSet:
    screenName = u.screen_name

    # If they already exist, ensure this user has been added
    if screenName in network:
      network[screenName] |= set(currentUserScreenName)
      continue

    network[screenName] = set()
    network[screenName].add(currentUserScreenName)

  return network


def getLayer(network, layerOfUsers, api):
  nextLayerOfFollowers = set()

  for currentUser in layerOfUsers:

    #Skip them if we already added them to avoid cycles
    if currentUser.screen_name in network:
      continue

    network[currentUser.screen_name] = set()

    logging_file.write('Grabbing followers for user ' + currentUser.screen_name + '\n')

    currentUsersFollowers = addFollowersToSet(currentUser, api)

    #Add all of my followers to inward edges
    network[currentUser.screen_name] = currentUsersFollowers

    nextLayerOfFollowers |= currentUsersFollowers

  return network, nextLayerOfFollowers

#Given a user id, create a set of all of their followers
def addFollowersToSet(user, api):
  setOfFollowers = set()

  count = 0
  currentBatch = []

  for followerId in limit_handled(tweepy.Cursor(api.followers_ids,user.screen_name).items()):
    currentBatch.append(followerId)
    count = count + 1

    if count == 100:
      count = 0

      setOfFollowers |= set(limit_handled_user_batch(currentBatch, api))
      currentBatch = []

  setOfFollowers |= set(limit_handled_user_batch(currentBatch, api))

  return setOfFollowers


# VARIOUS TWITNET FUNCTIONS

# Merge two twitter social graphs
def mergeTwitNets(network1, network2):
  newNetwork = {}
  newNetwork.update(network1) #Add all of network1 to newNetwork

  for screen_name, followers in network2.items():
    if screen_name in newNetwork:
      newNetwork[screen_name] |= followers
    else:
      newNetwork[screen_name] = followers

  return newNetwork


# Load a network form a pickle file
def loadPickeledNetwork(username):
    return pickle.load(open(username + ".pickle", "rb"))

# Load a network from a text file
def loadTextNetwork(username):
    network = {}

    for line in open(username + '.txt'):
        line = line.strip(' ').split(':')
        username = line[0]

        follower_list = line[1]
        follower_list = follower_list.split(',')

        network[username] = []
        for follower in follower_list:
            network[username].append(follower)

    return network


if __name__ == "__main__":
  main()
