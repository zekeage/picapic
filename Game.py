from google.appengine.ext import db
from google.appengine.api import memcache
import json
import logging
import random
from imageM import *
from userInfo import *
import datetime
import jinja2
import os
import util

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

#google app engine database model that stores chats for a game. model name is same as the game name.
class Gchats(db.Model):
    name = db.StringProperty(default = '') #model name
    chats= db.TextProperty(default = '##br####br####br####br####br####br####br##')#chat text
    rendered =db.TextProperty(default = '')#rendered version of chats (rendered by frirst player session)
    ver = db.IntegerProperty(default = 0)#version flag so users can check if they need to re-render
    newchats = db.BooleanProperty(default = False)#queue for chats before they are added
    shownames = db.IntegerProperty(default = 1)#0 or 1 for anon or names shown
    ucolors = db.TextProperty(default = '{}')#list of color for each user
    lastuser = db.StringProperty(default = '')#last person to type (no need to rewrite the user name)
    
    def safemod(self,command): #way to modify chat in memory without race condition
        if command not in "":
            client = memcache.Client()
            errcount = 1000
            while True and (errcount>0): # Retry loop
                errcount -=1
                s = client.gets("%gchat%"+self.name) #get the chats
                exec command #do the operation
                if client.cas("%gchat%"+self.name,s,3600): #write back the chat only if the access time is still current
                    break
            if (errcount==0):
                logging.error('gchat safemod fail')
            return s
        else:
            return self
        
    def mput(self): #put chat in memory (original entity is in datastore)
        if not memcache.Client().set("%gchat%"+self.name,self,3600):
            if not memcache.Client().add("%gchat%"+self.name,self,3600):
                logging.error('gchat mput fail')
                
    def uflare(self,uname): #add fake html for color to username
        if uname != '##GOD##':
            colors = ['00CC00','00CC99','006699','0000FF','6600FF','6600FF','FF0066','CC0000','FF6600','FFCC00','E6E600','669900']
            ucolors = json.loads(self.ucolors)
            color = colors[ucolors[uname]%len(colors)]
            return '#n0##s0#'+color+'#s1#'+uname+'#se#:#n1# '
        else:
            return '##GOD##'
    
    def addChat(self,uname,uchat):  #append a chat to the chat text
        command = """
uname = \'"""+self.uflare(uname)+"""\'
uchat = \'"""+uchat+"""\'
if uname not in "":
    if (s.lastuser != uname) and (uname!='##GOD##'):
        s.chats += ('##p1####p0##'+uname+uchat)
    elif uname=='##GOD##':
        s.chats += ('##p0####i0##'+uchat+'##i1####p1##')
    else:
        s.chats += ('##br##'+uchat)
s.newchats=True
s.lastuser = uname"""
        s=self.safemod(command)
        return s
    
    def addRender(self,render): #put the rendered chat
        command = """
render = \"\"\""""+render+"""\"\"\"
s.rendered = render
s.newchats=False
s.ver+=1"""
        s=self.safemod(command)
        return s
    
    def addUser(self,uname): #give the user a color assignment if they dont have one
        command = """
uname = \'"""+uname+"""\'
ucolors = json.loads(s.ucolors)
try:
    nc=ucolors[uname]
except:
    ucolors[uname]=len(ucolors)
    s.ucolors = json.dumps(ucolors)"""
        s=self.safemod(command)
        return s
    
    def newRender(self,shownames): #increment version and render the chats
        command = """
s.shownames = """+str(shownames)+"""
chatstream = s.chats
template_values = {
'chatstream': chatstream,
}
template = jinja_environment.get_template('chat.html')
s.rendered=template.render(template_values)
s.newchats=False
s.ver+=1"""
        s=self.safemod(command)
        #util.unescape(chatstream),
        return s
                
def getGchats(gid): #fast way to access chats.  checks memory first. miss falls to datastore
    try:
        gchat = memcache.Client().get("%gchat%"+gid)
        test = gchat.name
        return gchat
    except:
        try:
            gchat = Gchats.get_by_key_name(gid)
            if not memcache.Client().add("%gchat%"+gid,gchat,3600):
                logging.error('getGchats fail')
        except:
            gchat = ""
    return gchat
            
#google app engine database model that stores a game. includes everything about the game, state, user status, scores, etc.         
class Game(db.Model):
    members = db.TextProperty(default = '[]')
    memhands = db.TextProperty(default = '[]')
    memims = db.StringProperty(default = '[]')
    oldmemims = db.StringProperty(default = '[]')
    readys = db.StringProperty(default = '[]')
    active = db.StringProperty(default = '[]')
    stage = db.IntegerProperty(default = 0)
    turn = db.IntegerProperty(default = 0)
    handsize = db.IntegerProperty(default = 7)
    maxturn =db.IntegerProperty(default = 50)
    whosturn = db.StringProperty(default = '')
    scores = db.StringProperty(default = '[]')
    dscores = db.StringProperty(default = '[]')
    clue = db.TextProperty(default = '')
    stats = db.TextProperty(default = '')
    name = db.StringProperty(default = '')
    kicktime = db.IntegerProperty(default = 100)
    time = db.DateTimeProperty(auto_now_add=True)
    wasfirst = db.StringProperty(default = '')
    chats = db.TextProperty(default = """""")
    autoclue = db.IntegerProperty(default = 0)
    picpope = db.BooleanProperty(default = False)
    imchosenby = db.StringProperty(default = '[]')
    isrand = db.StringProperty(default = '[]')
    #0=default,1=nofirstplayer,2=picturepope
    
    def safemod(self,command): #way to modify game in memory without race condition
        if command not in "":
            client = memcache.Client()
            errcount = 1000
            while True and (errcount>0): # Retry loop
                errcount -=1
                s = client.gets("%game%"+self.name)
                exec command
                if client.cas("%game%"+self.name,s,3600):
                    break
            if (errcount==0):
                print "FUCKK, GAMESAFEMOD FAILED, FUCKKKK!OH SHIT OH SHIT!"
                s = client.get("%game%"+self.name)
                print s.stage
                print s.scores
                exec command
                print command
                print s.stage
                print s.scores
                print random.randint(0,500)
                logging.error('game safemod fail')
            return s
        else:
            return self
    
    def putUser(self,uname): #put the user in a game
        #if self.stage==0 or self.stage==1 or self.stage==2: #in hand or lobby
        hand = json.dumps(makehand(self.handsize))
        command = """
uname = \'"""+uname+"""\'
members = json.loads(s.members)
active = json.loads(s.active)
try: #in the game
    ind = members.index(uname)
    if not (s.stage==3):
        active[ind] = 2
    else:
        active[ind] = 1
    s.active = json.dumps(active)
except: #not in list
    scores = json.loads(s.scores)
    memims = json.loads(s.memims)
    memhands = json.loads(s.memhands)
    readys = json.loads(s.readys)
    dscores = json.loads(s.dscores)
    dscores.append([0,0])
    members.append(uname)
    scores.append(0)
    memims.append(-1)
    readys.append(False)
    memhands.append(\'"""+hand+"""\')
    if s.stage==0 or s.stage==1 or s.stage==2:
        active.append(2)
    else:
        active.append(1)
    s.members = json.dumps(members)
    s.scores = json.dumps(scores)
    s.memims = json.dumps(memims)
    s.memhands = json.dumps(memhands)
    s.readys = json.dumps(readys)
    s.dscores = json.dumps(dscores)
    s.active = json.dumps(active)
s.time = datetime.datetime.now()"""
        s = self.safemod(command)
        s.mput()
        s.put()
        members = json.loads(s.members)
        try:
            gchats = getGchats(self.name)
            nc=gchats.name
        except:
            gchats = Gchats(key_name=self.name)
            gchats.name = self.name
            gchats.put()
            gchats.mput()
        gchats=gchats.addUser(uname)
        gchats=gchats.addChat('##GOD##',uname+' has joined the game!')
        gchats.put()
        return members.index(uname)
        #else: #voting, wait till next turn
            #return False
        
    def removeUser(self,uname): #marks user as inactive and figures out who is new first player if player was first
        command = """
uname = \'"""+uname+"""\'
members = json.loads(s.members)
active = json.loads(s.active)
ind = members.index(uname)
active[ind] = 0
s.active = json.dumps(active)
if uname==s.whosturn:
    if s.stage <700:
        #new first player
        s.wasfirst=uname
        newInd = ind+1
        while newInd < (len(members)):
            if active[newInd]==2:
                break
            newInd +=1
        if newInd==len(members):
            newInd = 0
            while newInd < (len(members)):
                if active[newInd]==2:
                    break
                newInd +=1    
        try:
            s.whosturn = members[newInd]
        except:
            nc=1; #dont care, there was only one member in game
"""
        s=self.safemod(command)
        if s.wasfirst==uname:
            if s.stage<2:
                mem = getUserInfo(s.whosturn)
                mem.safemod("""s.stage1=-2;s.stage2=-2;""")
        gchats = getGchats(self.name)
        gchats.addChat('##GOD##',uname+' has ditched you fuckers.')
        gchats.put()
        return True


    def mput(self):#put game in memory
        if not memcache.Client().set("%game%"+self.name,self,3600):
            if not memcache.Client().add("%game%"+self.name,self,3600):
                logging.error('g mput fail')
        
    def advance(self,options): #game state machine shenanigans.  moves to next state
        if self.stage == 0: #in lobby.  on transition, apply options and fill hands of users
            command = """
s.stage = s.stage+1;s.time = datetime.datetime.now();"""
            if not (options==''):
                if 'op1.jpg' in options:
                    self.handsize=9
                    memhands = json.loads(self.memhands)
                    imcount = 0
                    for i in range(0,len(memhands)):
                        imcount+=(self.handsize-len(json.loads(memhands[i])))
                    randi = []
                    for i in range(0,imcount):
                        randi.append(getRand())
                    command = command+"""
randi = json.loads(\'"""+json.dumps(randi)+"""\')
numhands = """+str(self.handsize)+"""
memhands = json.loads(s.memhands)
count = 0
for i in range(0,len(memhands)):
    hand = json.loads(memhands[i])
    while len(hand)<numhands:
        hand.append(randi[count])
        count += 1
    memhands[i]=(json.dumps(hand))
s.memhands = json.dumps(memhands)
s.handsize = numhands"""
                if 'op2.jpg' in options:
                    command = command+"""
s.autoclue = random.randint(0,1083)+1
"""
                if 'op3.jpg' in options:
                    command = command+"""
s.kicktime = 20
"""
                if 'op4.jpg' in options:
                    command = command+"""
s.picpope = True
"""
        elif self.stage == 1: #in hand but no clue.  on transition, take first players clue and discard the cards selected by others
            randi = [];
            active = json.loads(self.active)
            for i in range(0,len(active)):
                if active[i] == 2:
                    randi.append(getRand())

            command = """
randi = json.loads(\'"""+json.dumps(randi)+"""\')
s.clue = getUserInfo(s.whosturn).text #get clue
s.stage = s.stage+1
readys = json.loads(s.readys)
active = json.loads(s.active)
members = json.loads(s.members)
memhands = json.loads(s.memhands)
memims = json.loads(s.memims)
s.time = datetime.datetime.now()
count = 0
for i in range(0,len(readys)):
    readys[i] = False
    if active[i]==2:
        if (not members[i]==s.whosturn) or s.autoclue:
            memi = getUserInfo(members[i]).choice
            if memi not in 'oskip.jpg oproceed.jpg':
                memhand = json.loads(memhands[i])
                j = memhand.index(memi)
                playImage(memi)
                memhand[j] = randi[count]
                memhands[i]= json.dumps(memhand)
            else:
                playImage(randi[count])
            count += 1
        else:
            memi= getUserInfo(members[i]).choice
            if memi not in 'oskip.jpg oproceed.jpg':
                memims[i] = memi
                playImage(memi)
                memhand = json.loads(memhands[i])
                j = memhand.index(memi)
                memhand[j] = randi[count]
                memhands[i]= json.dumps(memhand)
                count+=1
s.memhands = json.dumps(memhands)
s.memims = json.dumps(memims)
s.readys = json.dumps(readys)"""
        elif self.stage == 2: #get image choices and discard or submit accordingly (first player is discarding, others are submittingto match clue)
            randi = []
            active = json.loads(self.active)
            acount = 5;
            if self.autoclue:
                acount-=1
            for i in range(0,len(active)):
                if active[i] == 2:
                    randi.append(getRand())
                    acount -=1
            while acount >0:
                acount -=1
                randi.append(getRand())
                
            command = """
randi = json.loads(\'"""+json.dumps(randi)+"""\')
memhands = json.loads(s.memhands)
members = json.loads(s.members)
memims = json.loads(s.memims)
active = json.loads(s.active)
s.time = datetime.datetime.now()
isrand = []
count = 0
for i in range(0,len(members)):
    isrand.append(1)
    if active[i] == 2:
        member = members[i]
        memi= getUserInfo(member).choice
        if (not members[i]==s.whosturn) or (s.autoclue and not s.picpope):
            memims[i] = memi
            isrand[i]=0
            playImage(memi)
            memhand = json.loads(memhands[i])
            j = memhand.index(memi)
            memhand[j] = randi[count]
            memhands[i]= json.dumps(memhand)
            count += 1
        elif memi not in "":
            if memi not in 'oskip.jpg oproceed.jpg':
                memhand = json.loads(memhands[i])
                j = memhand.index(memi)
                playImage(memi)
                memhand[j] = randi[count]
                memhands[i]= json.dumps(memhand)
            else:
                playImage(randi[count])
            count += 1

while count < 4:
    memims.append(randi[count])
    isrand.append(1)
    playImage(randi[count])
    count += 1
readys = json.loads(s.readys)
for i in range(0,len(readys)):
    readys[i] = False
s.readys = json.dumps(readys)
s.memims = json.dumps(memims)
s.memhands = json.dumps(memhands)
s.isrand = json.dumps(isrand)
s.stage = s.stage+1"""
            
        elif self.stage == 3: #get voting selections and award points.  choose new first player and return game to first stage.
            # score points
            command = """
members = json.loads(s.members)
memims = json.loads(s.memims)
active = json.loads(s.active)
scores = json.loads(s.scores)
isrand = json.loads(s.isrand)
s.time = datetime.datetime.now()
firstPlayerInd = members.index(s.whosturn)
correctVotes = 0; 
tempScores = [0]*len(members)
whoTheyChose = []
activeCount=0;dscores = [];imchosenby=[]
for i in range(0,len(members)):
    imchosenby.append(json.dumps([]))
for i in range(0,len(members)): #mark choice of each member
    dscores.append([0,0])
    if active[i]==2:
        member = members[i]
        whoTheyChose.append(memims.index(getUserInfo(member).choice))
    else:
        whoTheyChose.append(-1)
s.imchosenby = json.dumps(imchosenby); count = -1;
for i in range(0,len(members)):  #give points for choices
    if active[i]==2:
        activeCount+=1
        member = members[i]
        if whoTheyChose[i]>=0:
            try:
                temp = json.loads(imchosenby[whoTheyChose[i]])
                temp.append(members[i])
                imchosenby[whoTheyChose[i]]=json.dumps(temp)
            except:
                whatever =1
            if (whoTheyChose[i]==firstPlayerInd) and not (s.autoclue and not s.picpope):
                if (not s.picpope) and (not s.autoclue):
                    correctVotes += 1
                    tempScores[i]+=2
                    dscores[i][0]+=2
            else:
                if s.picpope and (member==s.whosturn):
                    if not isrand[whoTheyChose[i]]:
                        tempScores[whoTheyChose[i]] += 5
                        dscores[whoTheyChose[i]][0] += 5
                    else:
                        tempScores[i] -= 4
                        dscores[i][0] -= 4
                elif s.picpope:
                    if not isrand[whoTheyChose[i]]:
                        dscores[whoTheyChose[i]][1] +=1
                    else:
                        dscores[i][1] -=1
                else:
                    if not isrand[whoTheyChose[i]]:
                        tempScores[whoTheyChose[i]] += 1   
                        dscores[whoTheyChose[i]][1] +=1
                    else:
                        tempScores[i] -= 1
                        dscores[i][0] -=1
        elif s.autoclue:
            if not s.picpope:
                tempScores[i]-=1
                dscores[i][0]-=1
    elif active[i]==1:
        active[i]=2
s.active = json.dumps(active)
s.imchosenby = json.dumps(imchosenby)
if correctVotes > 0 and correctVotes <(activeCount-1): #bonus for clue writer
    tempScores[firstPlayerInd] += 3
    dscores[firstPlayerInd][0] +=3
s.dscores = json.dumps(dscores)
for i in range(0,len(members)): #update scores
    scores[i] += tempScores[i]
s.scores = json.dumps(scores)
#new first player
s.wasfirst = s.whosturn
newInd = firstPlayerInd+1
while newInd < (len(members)):
    if active[newInd]==2:
        break
    newInd +=1
if newInd==len(members):
    newInd = 0
    while newInd < (len(members)):
        if active[newInd]==2:
            break
        newInd +=1    
s.whosturn = members[newInd]
                   
#clear things
readys = json.loads(s.readys)
for i in range(0,len(readys)):
    readys[i] = False
s.readys = json.dumps(readys)
s.oldmemims = s.memims
s.memims = json.dumps([-1]*len(members))
s.clue = ""
s.turn += 1
if s.autoclue!=0:
    s.autoclue=random.randint(0,1083)+1
#back to hand
s.stage = 1"""

        gchat = getGchats(self.name)
        gchat.safemod('s.newchats = True;')
        return self.safemod(command)  
        
        
    def readyCheck(self): #first player session checks that all players are ready before advancing
        readys = json.loads(self.readys)
        active = json.loads(self.active)
        members = json.loads(self.members)
        for i in range(0,len(readys)):
            if active[i]==2:
                if not readys[i]:
                    if not (self.picpope and (self.whosturn==members[i]) and self.autoclue and (self.stage==2)):
                        return False
        return True                

def getGame(gid):  #fast way to access game in memory.  a miss falls to the datastore entitiy
    try:
        game = memcache.Client().get("%game%"+gid)
        test = game.stage
        return game
    except:
        try:
            game = Game.get_by_key_name(gid)
            if not memcache.Client().add("%game%"+gid,game,3600):
                logging.error('getGame fail')
        except:
            game = ""
    return game