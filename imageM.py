from google.appengine.ext import db
from google.appengine.api import memcache
import json
import logging
import random
from google.appengine.api import images
import urllib
from google.appengine.api import urlfetch
import sys
import datetime

#image models in the datastore and accompanying im info

class ImInfo(db.Model):#stores info about an image in parallel so that it can be accessed WITHOUT loading the full image itself
    state = db.IntegerProperty(default = 0) #0,1,2, fresh, drawn, played
    atime = db.DateTimeProperty(auto_now_add=True) #INDICATES WHEN STATE LAST CHANGED ACCIDENTAL CAPS
    name = db.StringProperty() #name of image (same as corresponding image model object)
    def mput(self):
        if not memcache.Client().set("%iminfo%"+self.name,self,3600):
            if not memcache.Client().add("%iminfo%"+self.name,self,3600):
                logging.error('iminfo mput fail')
    def safemod(self,command):
        client = memcache.Client()
        errcount = 1000
        while True and (errcount>0): # Retry loop
            errcount -=1
            s = client.gets("%iminfo%"+self.name)
            exec command
            if client.cas("%iminfo%"+self.name,s,3600):
                break
        return s

def getImInfo(bid): #fast iminfo access via memcache
    try:
        iminfo = memcache.Client().get("%iminfo%"+bid)
        test = iminfo.state
        return iminfo
    except:
        try:
            iminfo = ImInfo.get_by_key_name(bid)
            test = iminfo.state
            if not memcache.Client().add("%iminfo%"+bid,iminfo,3600):
                logging.error('getiminfo fail')
        except:
            iminfo = ""
    return iminfo

class ImageM(db.Model):#images pulled from imgur
    name = db.StringProperty()#same name as iminfo object.  string representation of integer 0 to 999
    url = db.StringProperty() #where it came from on imgur. not used
    picture = db.BlobProperty(default=None) #picture data
    ctime = db.DateTimeProperty(auto_now_add=True) # created
    atime = db.DateTimeProperty(auto_now_add=True) # accessed
    drawn = db.BooleanProperty() # not used
    played = db.BooleanProperty() # not used
    def mput(self):
        if not memcache.Client().set("%im%"+self.name,self,3600):
            if not memcache.Client().add("%im%"+self.name,self,3600):
                logging.error('im mput fail')

def makeThumb(im,x0,y0):#makes a thumbnail.  not used currently. trys to balance cropping with scaling so that image fill is decent in 100px by 1--px square
    im2 = images.Image(im)
    w = im2.width
    h = im2.height
    ratio = (y0*1.0)/x0
    iratio = (h*1.0)/w
    rratio = iratio/ratio
    if rratio > 2:
        nh = w*ratio*2; d = ((h-nh)*.5)/h
        im = images.crop(im,0.0,d,1.0,1.-d)
    elif rratio <.5:
        nw = h/ratio*2; d = ((w-nw)*.5)/w
        im = images.crop(im,d,0.0,1.0-d,1.0)
    return images.resize(im,x0,y0,1)             

def sizeCheck(im): #checks that image is not ridiculously long or wide (extreme aspect ratio) before saving it into the bank
    im2 = images.Image(im)
    w = im2.width
    h = im2.height
    if (w*1.0)/h >2.7:
        return False
    if (h*1.0)/w >2.7:
        return False
    return True

def smartResize(im,w,h):#only resize if it isnt a gif.  broken tho, animation is still getting lost...whatevs
    gif = images.Image(im)
    try:
        gif.seek(1)
    except:
        im = images.resize(im,w,h,1)
    return im

def playImage(iname): #may not be necessary, but marks an image as played so that it can be deleted and replaced soon in an image update call
    try:
        im = getImage(iname)
        iminfo = getImInfo(iname)
        if not str(type(im))=="<type 'str'>":
            if not str(type(iminfo))=="<type 'str'>":
                iminfo=iminfo.safemod('s.state= 2;s.atime=datetime.datetime.now()')
                iminfo.put()
                timage=im.picture
                timage = makeThumb(timage,100,100)
                sim = ImageM(key_name=im.name+'s') #makes a small thumbnail (not used)
                sim.picture = db.Blob(timage)
                memcache.Client().set("%im%"+im.name+'s',sim,3600)
            else:
                logging.error(iname+' iminfo is a string: ')
        else:
            logging.error(iname+' image is a string: '+im)
    except:
        logging.error('couldn play'+iname)
        
def getRand(): #get an image from the bank
    N =1000
    drawn=True
    safety = 1000
    while drawn and safety >0: #while image is not already drawn by someone
        safety -= 1
        j = str(random.randint(0,N-1))
        drawn = False
        try:
            rimage = getImInfo(j)
            s = rimage.state
            if s>0:
                drawn = True
        except:
            logging.error("couldnt find imstate of: "+j)
            drawn = True

    if drawn == False:
        rimage.state = 1 #mark image as drawn at this time
        rimage.atime = datetime.datetime.now();
        rimage.mput()
        rimage.put() #put changes
        return j
    else:
        return False
    
def makehand(N): #get N random images
    hand = []
    for i in range(0,N):
        hand.append(getRand())
    return hand

def getImage(imkey): #get image from memcache (first access pulls from datastore, subsequent aceesses from memory)
    try:
        im = memcache.Client().get("%im%"+imkey)
        test = im.played
    except:
        try:
            im = ImageM.get_by_key_name(imkey)
            if not memcache.Client().add("%im%"+imkey,im,3600):
                if not memcache.Client().set("%im%"+imkey,im,3600):
                    logging.error('getImage fail')
        except:
            im = ""
    return im

def newImage(name): #steal an image from imgur/random
    nbytes = 10000000; goodAspect = False
    maxSize = 800000
    while nbytes>maxSize or nbytes < 1000 or not goodAspect:
        #url = "http://i.imgur.com/1Qz3K.jpg"
        randurl = "http://imgur.com/random"
        try:
            response = urllib.urlopen(randurl)
            msg = response.read()
            startPos = msg.find('<img src=\"')+10
            endPos = msg.find('\" alt=',startPos)
            url = msg[startPos:endPos]
            timage = urlfetch.Fetch(url).content
            nbytes= sys.getsizeof(timage)
            goodAspect = sizeCheck(timage)
        except:
            nbytes = 10000000
    rimage = ImageM(key_name=name)
    rimage.url = url
    timage = smartResize(timage,400,400); #resize and re-encode as jpg
    rimage.name = name
    rimage.picture = db.Blob(timage)
    rimage.drawn = False
    rimage.played = False
    rimage.put()
    rimage.mput()
    return url  

def moreImagesPlease(n,N): #N is image bank size, n is number of tiems to pick a random image key and check if it needs to be replaced with a call to newImage
    for i in range(0,n):
        j = str(random.randint(0,N-1)); 
        iminfo = getImInfo(j)
        if iminfo=="":
            newImage(j); iminfo = ImInfo(key_name=j);iminfo.name = j; iminfo.state=0; iminfo.atime = (datetime.datetime.now()); iminfo.put();iminfo.mput()
            logging.error('replaced empty')  
        else:
            if iminfo.state==2:
                if ((datetime.datetime.now()-iminfo.atime)>datetime.timedelta(minutes=15)):
                    newImage(j);iminfo.state=0; iminfo.atime = datetime.datetime.now(); iminfo.put();iminfo.mput()
                    logging.error('replaced played')   
            elif iminfo.state==1:
                if ((datetime.datetime.now()-iminfo.atime)>datetime.timedelta(hours=72)):
                    newImage(j);iminfo.state=0; iminfo.atime = datetime.datetime.now(); iminfo.put();iminfo.mput()
                    logging.error('replaced stale')   
                    
                      