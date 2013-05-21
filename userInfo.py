from google.appengine.ext import db
from google.appengine.api import memcache
import json
import logging
import random

class UserInfo(db.Model):#user info object.  stores what game they are in and what game state has been rendered to their screen
    name = db.StringProperty() #username taken from google account nickname
    ready = db.BooleanProperty(default = False) #not used
    choice = db.StringProperty(default = '') #image they clicked on last
    score = db.IntegerProperty(default = 0) #not used
    text = db.TextProperty(default = '') # text they typed in clue box
    game = db.StringProperty(default = '') # game they are in
    stage1 = db.IntegerProperty(default = -2) #header state (if the number doesn't match the game stage, then they need to re-draw) 
    stage2 = db.IntegerProperty(default = -2) #hand state (if the number doesn't match the game stage, then they need to re-draw)
    ind = db.IntegerProperty(default = 0) #index of the user in the game object (for quick access of their stats in the game)
    chatver = db.IntegerProperty(default = -1) #version of chat that they have rendered (on mis-match, fetches latest render)
    
    def mput(self):
        if not memcache.Client().set("%user%"+self.name,self,3600):
            if not memcache.Client().add("%user%"+self.name,self,3600):
                logging.error('mput fail')
            # if not memcache.Client().add("%user%"+self.name,self,3600):
            #     logging.error('also couldnt add to memcache')
            
    def safemod(self,command):
        if command not in "":
            client = memcache.Client()
            errcount = 1000
            while True and (errcount>0): # Retry loop
                errcount -=1
                s = client.gets("%user%"+self.name)
                exec command
                if client.cas("%user%"+self.name,s,3600):
                    break
            if (errcount==0):
                print "USERSAFEMOD FUCKK!"
                s = client.get("%user%"+self.name)
                print s.stage1
                print s.stage2
                exec command
                print command
                print s.stage1
                print s.stage2
                print random.randint(0,500)
                logging.error('user safemod')
            return s
        else:
            return self 

def getUserInfo(uid):
    try:
        user = memcache.Client().get("%user%"+uid)
        test = user.score
        return user
    except:
        try:
            user = UserInfo.get_by_key_name(uid)
            if not memcache.Client().add("%user%"+user.name,user,3600):
                logging.error('getUser fail')
        except:
            user = ""
            logging.error('user not found: '+uid)
    return user