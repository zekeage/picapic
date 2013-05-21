from imageM import *
from userInfo import *
from Game import *
from util import *
import os
import jinja2

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

def renderHeader(cuser,cgame,tbox,bpress,imchoice,url):
    ukey = cuser.name
    if cgame == "": # not in game
        #debug = "ukey: " + ukey + "  tbox: " + tbox + "  bpress: " + str(bpress) + "  ustage: " + str(cuser.stage1)
        if cuser.stage1 < -1:
            rewrite = True
            #cuser.stage1 =-1
            command = """s.stage1=-1"""
            cuser = cuser.safemod(command)
        else:
            rewrite = False
        instructions = "Enter game to join or create:"
        message = ""
        errtext = ""
        hasbutton =True
        hasbox = True
        if bpress:
            tgame = getGame(tbox)
            try:
                nc = tgame.stage
                uind = tgame.putUser(ukey)
                rewrite = False
                message = "Loading..."
                command = """s.stage1 = """+str(tgame.stage-1)+"""\ns.stage2 = """+str(tgame.stage-1)+"""\ns.ready = False\ns.game = \'"""+tbox+"""\';s.ind="""+str(uind)+""""""
                cuser = cuser.safemod(command)
                cgame = getGame(cuser.game)
  
            except:
                rewrite = False
                message = "Loading..."
                cgame = Game(key_name=tbox)
                cgame.name = tbox; 
                cgame.whosturn = cuser.name
                cgame.mput()
                cgame.putUser(ukey)
                command = """s.game = \'"""+tbox+"""\';s.ind=0"""
                cuser = cuser.safemod(command)
                cgame = getGame(tbox)
                
    else:
        #debug = "ukey: " + ukey + "  tbox: " + tbox + "  bpress: " + str(bpress) + "  ustage: " + str(cuser.stage1) + "  gstage: " + str(cgame.stage) +" rand"+str(random.randint(0,499))+"mems:" + (cgame.members)+"ready:" + str(cuser.ready)
        if cuser.stage1 == cgame.stage: #at a stage
            rewrite = False
            if bpress or (cgame.picpope and cgame.autoclue and (cuser.name==cgame.whosturn)):
                if cuser.stage1==0: #entering game
                    if cuser.name==cgame.whosturn:
                        cgame=cgame.advance(imchoice)
                elif cuser.stage1 ==1:
                    if cuser.name==cgame.whosturn:
                        if cgame.autoclue !=0:
                            tbox = getQuote(url,cgame.autoclue)
                        command = """s.text = \'"""+tbox+"""\'"""
                        cuser = cuser.safemod(command)
                        if cgame.readyCheck():
                            cgame=cgame.advance('')
                elif cuser.stage1==2:
                    if cuser.name==cgame.whosturn:
                        if cgame.readyCheck():
                            cgame=cgame.advance('')
                elif cuser.stage1==3:
                    if cuser.name==cgame.whosturn:
                        if cgame.readyCheck():
                            cgame=cgame.advance('')

        else:
            errtext = ""
            message = ""
            rewrite = True
            hasbox = False
            hasbutton = False
            instructions = ""
            if cgame.stage==0:
                command = """s.stage1=0\ns.choice =\"\""""
                cuser = cuser.safemod(command)
                #cuser.mput()
                #if cgame.turn >1:
                    #message = cgame.getScoreSummary()
                if cuser.name==cgame.whosturn:
                    hasbutton = False
                    instructions = "<span style=\"font-weight: normal;\">You should probably select the options you want...</span>Then click START GAME!"
                    message = ""
                else:
                    instructions = "Waiting on "+cgame.whosturn+" to fucking choose some fucking options already."
            elif cgame.stage==1:
                command = """s.stage1=1\ns.choice =\"\""""
                cuser = cuser.safemod(command)
                cgame.put()
                if cuser.name==cgame.whosturn:
                    hasbutton = False
                    if cgame.autoclue:
                        hasbox = False
                        if cgame.picpope:
                            instructions = "You may banish an unworthy image."
                        else:
                            instructions ="If you'd like to discard a picture for a new one, NOW IS THE TIME TO SELECT IT." 
                    else:
                        hasbox = True
                        if cgame.picpope:
                            instructions = "Provide a clue."
                        else:
                            instructions = "Compose a fucking clue, then pick the picture that goes with it!"
                else:
                    instructions = "If you'd like to discard a picture for a new one, NOW IS THE TIME TO SELECT IT."
            elif cgame.stage==2:
                cuser.put()
                command = """s.stage1=2\ns.choice =\"\""""
                cuser = cuser.safemod(command)
                if cuser.name==cgame.whosturn:
                    if cgame.picpope and cgame.autoclue:
                        instructions = "The gods have spoken a clue, rest now while your clergy men try to interpret his will."    
                    else:
                        if cgame.picpope:
                            instructions = "You may banish an unworthy image from your hand while your followers try to interpret your words. They are so eager to please you."
                        else:
                            instructions = "Choose a picture to replace with a new random one."
                    message = "Clue: #s0#FFEE00#s1#" + cgame.clue +"#se#"
                else:
                    if cgame.picpope:
                        instructions = "Offer a selection that will please His holiness, "+cgame.whosturn+"."
                    else:
                        instructions = "Choose a picture to match " + cgame.whosturn + "\'s clue."
                    message = "Clue: #s0#FFEE00#s1#" + cgame.clue +"#se#"
                if cgame.autoclue and not cgame.picpope:
                    instructions ="Let this quote inspire you to CLICK ON A FUCKING PICTURE. DO IT."  
            elif cgame.stage==3:
                gchat = getGchats(cgame.name)
                gchat.put()
                command = """s.stage1=3\ns.choice =\"\""""
                cuser = cuser.safemod(command)             
                if cuser.name==cgame.whosturn:
                    if cgame.picpope:
                        instructions = "Choose the most worthy image."
                    else:
                        instructions = "Choose your favorite attempt to match your clue."
                    message = "Clue: #s0#FFEE00#s1#" + cgame.clue +"#se#"
                else:
                    if cgame.picpope:
                        instructions = "Pick your favorite (just for fun), while you wait patiently for " + cgame.whosturn + "\'s decision."
                    else:
                        instructions = "Choose " + cgame.whosturn + "\'s picture."
                    message = "Clue: #s0#FFEE00#s1#" + cgame.clue +"#se#"
                if cgame.autoclue and not cgame.picpope:
                    instructions ="PICK THE BEST FUCKING PICTURE. CLICK THAT SHIT!" 
                active = json.loads(cgame.active); active = active[cuser.ind];
                if (active==1):
                    instructions = "Chill for a moment, you are temporarily in observer mode"
        
    if rewrite:   
        template_values = {
            'debug': "",
           'errtext': errtext,
           'instructions': instructions,
           'message': message,
           'hasbox' : hasbox,
           'boxcontents' : "",
           'hasbutton' : hasbutton,
           }
        template = jinja_environment.get_template('header.html')
        output = template.render(template_values)
    else:
        output = ""
    return cuser,cgame,output,str(int(rewrite))

def renderHand(cuser,cgame,tbox,bpress,imchoice):
    notallowed = ""
    if cgame != "":
        if cuser.stage2==cgame.stage:
            rewrite = False
            if imchoice not in "":
                if imchoice not in cuser.choice:
                    command = """s.choice = \'"""+imchoice+"""\'"""
                    cuser=cuser.safemod(command)
                    command = """readys=json.loads(s.readys);readys["""+str(cuser.ind)+"""]=True;s.readys = json.dumps(readys)"""
                    cgame =cgame.safemod(command)
            else:
                command = """s.choice = \"\""""
                cuser=cuser.safemod(command)
                command = """readys=json.loads(s.readys);readys["""+str(cuser.ind)+"""]=False;s.readys = json.dumps(readys)"""
                cgame =cgame.safemod(command)
        else:    
            cuser=cuser.safemod('s.stage2='+str(cgame.stage))
            rewrite = True
        if rewrite:
            if cgame.stage == 0:
                imtype = 2;
                if cuser.name == cgame.whosturn:
                    imlist = ['op1.jpg','op2.jpg','op3.jpg','op4.jpg','opstart.gif']
                    clickFunc= "addBorderOp(this)"
                else:
                    imlist = ['op1.jpg','op2.jpg','op3.jpg','op4.jpg','opstart.gif']
                    clickFunc= ""
            elif cgame.stage ==1:
                imtype = 1;
                memhands = json.loads(cgame.memhands)
                imlist = json.loads(memhands[cuser.ind])
                clickFunc= "addBorder(this)"
                if (cuser.name != cgame.whosturn) or cgame.autoclue:
                    imlist.insert(0,'oskip.jpg')
                elif (cuser.name == cgame.whosturn) and cgame.picpope:
                    imlist = ['oproceed.jpg']
            elif cgame.stage ==2:
                imtype = 1;
                memhands = json.loads(cgame.memhands)
                imlist = json.loads(memhands[cuser.ind])
                clickFunc= "addBorder(this)"
                if (cuser.name == cgame.whosturn) and (not cgame.autoclue):
                    imlist.insert(0,'oskip.jpg')
                elif (cuser.name == cgame.whosturn) and cgame.picpope:
                    clickFunc= ""
            elif cgame.stage ==3:
                imtype = 1;
                clickFunc= "addBorder(this)"
                imlist = json.loads(cgame.memims)
                active = json.loads(cgame.active)
                if active[cuser.ind]==2:
                    notallowed = imlist[cuser.ind]
                elif active[cuser.ind]==1:
                    clickFunc =""
                imlist = randperm(imlist)
            else:
                rewrite = False
    else:
        if cuser.stage2==-2:
            imtype = 2;
            rewrite = True
            imlist = ['orules.png']
            clickFunc= ""; notallowed = ""
            cuser=cuser.safemod('s.stage2=-1')
        else:
            rewrite = False
            

    
    if rewrite:        
        template_values = {
            'imlist': imlist,
            'imtype': imtype,
            'notallowed':notallowed,
            'clickFunc':clickFunc
           }
        template = jinja_environment.get_template('hand.html')
        output = template.render(template_values)
    else:
        output = ""
    return cuser,cgame,output,str(int(rewrite))

def renderStats(cuser,cgame,tbox,bpress,imchoice):
    if cgame != "":
        if cuser.name==cgame.whosturn:
            members = json.loads(cgame.members)
            scores = json.loads(cgame.scores)
            dscores = json.loads(cgame.dscores)
            readys = json.loads(cgame.readys)
            active = json.loads(cgame.active)
            memims = json.loads(cgame.oldmemims)
            imchosenby = json.loads(cgame.imchosenby)
            idle = (datetime.datetime.now()-cgame.time)>datetime.timedelta(seconds=cgame.kicktime)
            whosturn=cgame.whosturn
            memout=[];scoreout=[];kick = [];showImages=0; imlist = [];N = 0;
            for i in range(len(members)):
                if active[i]==2:
                    im='osecret.jpg'; first = 0; N+=1;
                    if (cgame.stage==1):
                        try:
                            if (members[i]==cgame.wasfirst) and cgame.picpope:
                                im = 'opope.jpg'                            
                            elif int(memims[i])>0:
                                im = memims[i]; showImages=1
                            else:
                                im = 'onothing.jpg'
                            if (members[i]==cgame.wasfirst) and not cgame.autoclue:
                                first = 1
                            if (dscores[i][0]==5) and cgame.picpope:
                                first = 1
                        except:
                            whatever=0
                    temp=''
                    try:
                        temp2 = json.loads(imchosenby[i]) 
                        for j in range(len(temp2)):
                            temp+=(temp2[j]+', ')
                        if len(temp)>1:
                            temp = temp[0:-2]
                    except:
                        temp=''
                    imlist.append([im, first, temp])
                    kick = ''
                    if idle:
                        if not readys[i]:
                            if not (cgame.stage==0):
                                kick = '&nbsp<a onclick=\"catchLink(this)\" href="#" id="m='+members[i]+'">(kick)</a>'
                    memout.append([readys[i], members[i], kick])
                    delta = ''
                    if (abs(dscores[i][0])+abs(dscores[i][1]))>0:
                        p0 = '+'; p1 = '+';
                        if dscores[i][0]<0:
                            p0 = ''
                        if dscores[i][1]<0:
                            p1 = ''                        
                        if cgame.autoclue and not cgame.picpope:
                            if len(memout)<4:
                                delta = ' ('+p0+str(dscores[i][0])+","+p1+str(dscores[i][1])+')'
                            else:
                                delta = ' ('+p1+str(dscores[i][1])+')'
                        elif cgame.picpope:
                            if (abs(dscores[i][0])>0):
                                delta = ' ('+p0+str(dscores[i][0])+')'                     
                        else:
                            delta = ' ('+p0+str(dscores[i][0])+","+p1+str(dscores[i][1])+')'
                    else:
                        delta = ''
                    scoreout.append('<b>'+str(scores[i])+'</b> '+delta)
            width = 15; Fwidth = width*N;
            if Fwidth >100:
                width = 100.0/N; Fwidth = 100;
            if cgame.autoclue:
                whosturn = ""
            template_values = {
                'whosturn': whosturn,
                'members': memout,
               'scores': scoreout,
               'width' : width,
               'Fwidth' : Fwidth,
               'showImages': showImages,
               'imlist': imlist,
               }
            template = jinja_environment.get_template('stats.html')
            cgame.stats = template.render(template_values)
            cgame.mput()
        return cuser,cgame,cgame.stats,'1'
    else:
        return cuser,cgame,'','1'
    
def renderChats(cuser,cgame,tbox,bpress,uchat):
    if cgame != "":
        newchats = 0;
        gchat = getGchats(cgame.name)
        if uchat not in "":
            gchat=gchat.addChat(cuser.name,uchat)
        if cuser.name==cgame.whosturn:
            if cgame.stage==3:
                shownames='0'
            else:
                shownames='1'
            try:
                gchat = getGchats(cgame.name)
                if gchat.newchats:
                    newchats=1;
            except:
                whatevs = 1
            if newchats:
                gchat = gchat.newRender(shownames)
            else:
                gchat = gchat.safemod('s.shownames='+shownames)
        if cuser.chatver != gchat.ver:
            cuser=cuser.safemod('s.chatver='+str(gchat.ver))
            return cuser,cgame,gchat.rendered,'1'+str(gchat.shownames)
        else:
            return cuser,cgame,'','0'+str(gchat.shownames)
    else:   
        return cuser,cgame,'<div id = "chats"></div>','11'
    
    
    
    
    
    
    
    
    
           