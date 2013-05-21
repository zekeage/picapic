#import cgi
#import datetime
import logging
import webapp2
import urllib
import jinja2
import os
import sys
import random
import urlparse
import json
import pickle
import re
from imageM import *
from userInfo import *
from Game import *
from util import *
from render import *

#import subprocess
jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.api import urlfetch
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.datastore import entity_pb

import datetime
    
class updateImages(webapp2.RequestHandler):#background task to check 4 images for updating
    def get(self):
        moreImagesPlease(4,1000)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Done!') 
        
class initialUpdate(webapp2.RequestHandler):#background task to check 20 images for updating (run this manually a couple times to restore an emptied image bank)
    def get(self):
        moreImagesPlease(20,1000)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Done!')
                      
class renderImage(webapp2.RequestHandler): #getimage and return it
    def get(self):
        imkey = self.request.get('imkey')
        if imkey[0]!='o':
            im = getImage(imkey)
            try:
                isize = sys.getsizeof(im.picture)
                self.response.headers['Content-Type'] = 'image/jpeg'
                self.response.out.write(im.picture)
            except:
                self.response.headers['Content-Type'] = 'image/jpeg'
                self.redirect('/gameOptions/onothing.jpg')
        else:
            self.response.headers['Content-Type'] = 'image/jpeg'
            self.redirect('/gameOptions/'+imkey)
    
class GameUpdate(webapp2.RequestHandler):    #parse status info from the client and call render functions, and return the results to the client
    def post(self):
        ukey = self.request.get('ukey')
        tbox = self.request.get('tbox')
        bpress = self.request.get('bpress')
        imchoice = self.request.get('imchoice')
        uchat = self.request.get('uchat')
        cuser = getUserInfo(ukey)
        if str(type(cuser))=="<type 'str'>":
            logging.error("no user...")
            self.redirect('/')
        cgame = getGame(cuser.game)
        woos = '';url =self.request.host_url
        (cuser,cgame,header,woo) = renderHeader(cuser,cgame,tbox,bpress,imchoice,url)
        woos+=woo; #render = '<div id="header">'+header+'</div>'
        render = header
        (cuser,cgame,game,woo) = renderHand(cuser,cgame,tbox,bpress,imchoice)
        woos+=woo; #render = render+'<div id="hand">'+game+'</div>'
        render = render+game
        (cuser,cgame,stats,woo) = renderStats(cuser,cgame,tbox,bpress,imchoice)
        render = render+stats
        woos+=woo; #render = render+'<div id="stats">'+stats+'</div>'
        (cuser,cgame,chats,woo) = renderChats(cuser,cgame,tbox,bpress,uchat)
        render = render+chats
        woos+=woo; #render = render+'<div id="stats">'+stats+'</div>'
        self.response.out.write(woos+render) #first 4 characters are 1s and 0s in woo which tell client if updates occurrd in header,hand,stats, and chat
        
class GamePage(webapp2.RequestHandler):  #on first access, set user stage to -2 to refresh their game session (if not logged in, promptthem)
    def get(self):
        user = users.get_current_user()
        if user:
            logging.error('NAME IS' + user.nickname())
            uiname = user.nickname();#uiname=uiname[0:(uiname.find('@'))]
            ui = getUserInfo(uiname)
            if not ui:
                ui = UserInfo(key_name=uiname) #user info
                ui.name =uiname
                ui.mput()  
                ui.put()
            else:
                ui.mput()
                ui=ui.safemod("s.stage1=-2;s.stage2=-2;s.ready=False;s.chatver=-1;")
                ui.put()
            template_values = {
            'logoutUrl': '/logout',
            'ukey': uiname,
            'gkey': ui.game,
            'imlist': [],
            }
            template = jinja_environment.get_template('game.html')
            #self.response.headers["Pragma"]="no-cache"
            #self.response.headers["Cache-Control"]="no-cache, no-store, must-revalidate, pre-check=0, post-check=0"
            self.response.out.write(template.render(template_values))
        else:
            self.redirect(users.create_login_url(self.request.uri))

class logout(webapp2.RequestHandler):
    def get(self):
        try:
            user = users.get_current_user()
            uiname=user.nickname();#uiname=uiname[0:(uiname.find('@'))]
            ui = getUserInfo(uiname)
            ui.put()
        except:
            whatever = 0
        self.redirect(users.create_logout_url('/'))


class kick(webapp2.RequestHandler):
    def get(self):
        memname = self.request.get('m')
        cuser = getUserInfo(memname)
        cgame = getGame(cuser.game)
        if cuser != "":
            if cgame != "":
                readys = json.loads(cgame.readys)
                if (datetime.datetime.now()-cgame.time)>datetime.timedelta(seconds=cgame.kicktime):
                    if not readys[cuser.ind]: #kick that mofo
                        cgame.removeUser(cuser.name)
                        cuser.stage1 = -2
                        cuser.stage2 = -2
                        cuser.ready = False   
                        cuser.choice = ''
                        cuser.text = ''
                        cuser.game = ""
                        cuser.put()
                        cuser.mput()
                        #self.redirect('/')
        

class leave(webapp2.RequestHandler):        #when a user leaves a game,they are just marked as inactive
    def get(self):
        user = users.get_current_user()
        if user:
            uiname=user.nickname();#uiname=uiname[0:(uiname.find('@'))]
            ui = getUserInfo(uiname)
            if ui.game not in "":
                cgame = getGame(ui.game)
                cgame.removeUser(ui.name)
                gchat = getGchats(cgame.name)
                gchat.put()
            ui.stage1 = -2
            ui.stage2 = -2
            ui.ready = False   
            ui.choice = ''
            ui.text = ''
            ui.game = ""
            ui.put()
            ui.mput()
            ui.mput()
        self.redirect('/')
            
app = webapp2.WSGIApplication([('/im',renderImage),
                               ('/kick',kick),
                               ('/update',updateImages),
                               ('/update0',initialUpdate),
                               ('/gupdate',GameUpdate),
                               ('/logout',logout),
                               ('/',GamePage),
                               ('/leave',leave)],
                              debug=True)









