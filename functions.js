//check for async html request to complete (for game updates)
htreq.onreadystatechange=function()
   		{
   		if (htreq.readyState==4 && htreq.status==200)
     		{
     		gameState = 2;
     		}
   		}

//check for async html request to complete (for background process management on server)
htreqS.onreadystatechange=function()
   		{
   		if (htreqS.readyState==4 && htreqS.status==200)
     		{
     		//document.write("<h1>This is a heading</h1>"); 
     		updateState = 2;
     		}
   		}	
   		
//make sure that there is text in the box when submitting a clue or entering a game	
function checkErrors(element)
{	
	try {if (document.getElementById("tbox").value.replace(/\s+/g,'') == '') 
			{txt = "No text! Try again, you sack of shit.";}
			else {txt="";}
	//else if (document.getElementById("b1").value=="")
		//{txt = "If you don't pick a picture, you're gonna have a bad time.";}
		}
	catch(err)
		{
		txt = "";	
		}
	if (txt=="")
		{document.getElementById("b1").value="1";
		return 1;}
	else
		{

		t = document.getElementById("err");
		t.innerHTML = txt;
		return 0;
		}
}

//unused?
function sleep(milliseconds) {
  var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
	if ((new Date().getTime() - start) > milliseconds){
	  break;
	}
  }
}

//catch return key in chat box and append the text to your queue to be sent back on next update
function chatSubmit(event)
{
   if(event && (event.keyCode == 13) && (!event.shiftKey))
   {  event.preventDefault();
   	  EE = document.getElementById("cbox");
   	  temp = EE.value;
   	  if (temp.replace(/\s+/g,'') != '')
   	  {
   	  		if (chatStream=="") {chatStream=temp;}
   	  		else {chatStream=chatStream+'##br##'+temp;}
	      	chatSending=1;
	      	EE.value="";
	      	//alert(chatStream);
			EE.selectionStart = 0;
			EE.selectionEnd = 0;
      }
   }
}

//catch return key in game name box and call checkerrors to check not empty and submit the name
function gnameSubmit(event)
{
   if(event && (event.keyCode == 13) && (!event.shiftKey))
   {
   event.preventDefault();
   checkErrors(document.getElementById("b1"));
   //document.getElementById("b1").value="1";
   }
}

//unused
function setCaret(ctrl)
{
	pos = ctrl.value.length;
	scrollPosy = document.body.scrollTop;
	scrollPosx = document.body.scrollLeft;
	//if (window.navigator.appName=="Netscape")
	//{
	//scrollPosy=scrollPosy;
	//scrollPosx=scrollPosx;
	//}
	if(ctrl.setSelectionRange)
	{
		ctrl.focus();
		ctrl.setSelectionRange(pos,pos);
	}
	else if (ctrl.createTextRange) {
		var range = ctrl.createTextRange();
		range.collapse(true);
		range.moveEnd('character', pos);
		range.moveStart('character', pos);
		range.select();
	}
	window.scrollTo(scrollPosx,scrollPosy);
}

//mark class of selected image as "selected" and deselect previously selected ones
function addBorder(element)
{   if (element.id.indexOf("hov") !== -1)
		{eid = element.id.substring(0,element.id.length-3);}
		else {eid = element.id;}
	try {if (document.getElementById('offlimits').value!=eid) {allowed=1;} else{allowed = 0;}}
	catch(err) {allowed =1;}
	if (allowed ==1)
	{	
		var images = new Array(); 
		images = document.getElementsByTagName('img');
		for (var i=0; i<images.length; i++)  {
			if (document.getElementById(images[i].id).className=="selectedIM")
			{document.getElementById(images[i].id).className = "unselectedIM";}
			}
		t = document.getElementById("err");
		t.innerHTML = "";
		if (eid==document.getElementById('b2').value)
			{
			document.getElementById('b2').value = "";
			document.getElementById('b1').value = "";
			}
		else
			{
			if (checkErrors(document.getElementById('b1')))
				{
				document.getElementById(eid).className = "selectedIM";  
				document.getElementById('b2').value = eid;
				}
			}

		}

	else
	{
			t = document.getElementById("err");
		t.innerHTML = "CANT VOTE FOR YOUR OWN PICTURE";
			
	}
}

//prevents th ekick link from redirecting you (it just sends an async request to kick the user)
function catchLink(element)
{
req = new XMLHttpRequest(); 
req.open( "GET", "kick?"+element.id, true );
req.send();
return false;
}

//same as addborder but allows multiple selections
function addBorderOp(element)
{	if (element.id.indexOf("hov") !== -1)
		{eid = element.id.substring(0,element.id.length-3);}
		else {eid = element.id;}
	var images = new Array(); 
	t = document.getElementById("err");
	t.innerHTML = "";
	currentOp = document.getElementById('b2').value;
	if (currentOp.indexOf(eid) !== -1)
		{
		document.getElementById(eid).className = "unselectedIM";
		currentOp=currentOp.replace(eid,'');
		document.getElementById('b2').value = currentOp;
		}
	else
		{
		document.getElementById(eid).className = "selectedIM";
		currentOp = currentOp+eid;
		document.getElementById('b2').value = currentOp;
		}
	if (eid=="opstart.gif")
	{
	document.getElementById('b1').value = "1";
	}
}

//if not waiting on a request, send the client status (button press, clues entered, chats entered, images selected) on timer trigger
//when the response comes, parse it and update html in various divs as necessary
function updateGame(req,timer)
{

if (gameState==0) //make a request
	{
	req.open( "POST", "gupdate", true );
	req.setRequestHeader("Content-type","application/x-www-form-urlencoded");
	
	try {tbox = document.getElementById('tbox');textval = tbox.value.replace(/;/g,"##sc##");
	textval=textval.replace(/'/g,"##sq##");textval=textval.replace(/"/g,"##dq##");textval=textval.replace(/\n/g,"##br##");}
	catch(err) {textval = "";}
	
	try {bpress = document.getElementById("b1").value;}
	catch(err) {bpress = "";}
	
	try {uname = document.getElementById("uname").value;}
	catch(err) {uname = "";}
	
	try {imchoice = document.getElementById('b2').value;}
	catch(err) {imchoice = ""}
	
	chatStream = chatStream.replace(/;/g,"##sc##");chatStream=chatStream.replace(/"/g,"##dq##");
	chatStream=chatStream.replace(/'/g,"##sq##");chatStream=chatStream.replace(/\n/g,"##br##");
	
	req.send("ukey="+uname+"&tbox="+textval+"&bpress="+bpress+"&imchoice="+imchoice+"&uchat="+chatStream);
	chatStream = "";
	gameState = 1;
	}
else if (gameState==2) //response received
	{
	var txt = req.responseText;
	doHeader = txt.substring(0,1);doHand = txt.substring(1,2);doStats = txt.substring(2,3);doChats = txt.substring(3,4);showNames = txt.substring(4,5);
	txt = txt.substring(5);txt=txt.replace(/src=/g,"data-src="); 
	htxt = $('<div>'+txt+'</div>');
	if (doHeader=='1') {header = htxt.find("#header").html();	renderHeader(header);}
	if (doHand=='1')   {hand =   htxt.find("#hand").html();	 	renderHand(hand);}
	if (doStats=='1')  {stats =  htxt.find("#stats").html();	  renderStats(stats);}
	if (doChats=='1')  {hastext=0;wasAtBottom=0;
						try {
						var temp = document.getElementById("ctext");
						wasAtBottom = (abs(temp.scrollTop-temp.scrollHeight)<20);//broken--temp.scrollHeight can be huge but scrollTop is just screen height
						t = document.getElementById("cbox").value; if (t != "") {hastext=1;}}
						catch(err) {;}
						if ((document.activeElement.id=="cbox")||(hastext==1)) {chats =  htxt.find("#ctext").html(); writing=1;}
						else {chats =  htxt.find("#chats").html();writing=0;}	  
						renderChats(chats,showNames,writing);doscroll=0;
						if (chatSending==1)
							{doscroll=1;chatSending=0;}
						else
							{try
							{
								var sidebar = document.getElementById('sidebar');
								var sprop = document.defaultView.getComputedStyle(sidebar,null).getPropertyValue("box-shadow");
								var shov = (sprop.indexOf('-')!=-1);
								if (shov)
									{doscroll = 1;}
							}
							catch(err) {doscroll=0;}}
						if (true)//doscroll
							{
							try {
							var temp = document.getElementById("ctext");
							temp.scrollTop = temp.scrollHeight;
							}
							catch(err){nocare=1;}
							}	
						}
	gameState = 0;
	}
}

function unescape(txt) //replace escaped quotes and semicolons that were removed to prevent python from losing it shits
{
txt=txt.replace(/##br##/g,'<br>');    
txt=txt.replace(/##sc##/g,';');
txt=txt.replace(/##sq##/g,'\'');
txt=txt.replace(/##dq##/g,'\"');
return txt;
}

function renderHeader(txt) //puts new html in header div
{
txt=txt.replace(/#s0#/g,'<span style=\"color: #');
txt=txt.replace(/#s1#/g,'\">');
txt=txt.replace(/#se#/g,'</span>');
txt = unescape(txt);
t = document.getElementById("header");
t.innerHTML = '<div>' + txt + '</div>';
document.getElementById('b2').value = "";
}

function renderHand(txt) //puts new hand in hand div
{
if (txt!=null){txt=txt.replace(/data-src=/g,"src="); }
t = document.getElementById("hand");
t.innerHTML = '<div>' + txt +'</div>'
document.getElementById('b2').value = "";
}

function renderStats(txt) //puts new stats in stat table
{
if (txt != document.getElementById('statstore').value)
{	
	imlistold = document.getElementById('imstore').value;
	imlist = ($('<div>'+txt+'</div>').find("#secret")).attr("value");
	if (imlist != imlistold) //if images haven changed, re-render the table
		{
		if (txt!=null){txt=txt.replace(/data-src=/g,"src="); }
		t = document.getElementById("stats");
		t.innerHTML = txt;
		document.getElementById('imstore').value=imlist;
	
		}
	else //if images haven't changed, only update the text
		{
		t1 = ($('<div>'+txt+'</div>').find("#t1")).html();
		t2 = ($('<div>'+txt+'</div>').find("#t2")).html();
		t = document.getElementById("t1");t.innerHTML = t1;
		t = document.getElementById("t2");t.innerHTML = t2;
		}
}
}

function renderChats(txt,showNames,writing)//render chat bar
{ 
	{//secret fake html so sanitized output from server can still do color and pgraphs
	txt=unescape(txt);
	txt=txt.replace(/##i0##/g,'<i>');
	txt=txt.replace(/##i1##/g,'</i>');
	if (showNames=='0') {
	txt=txt.replace(/##p0##/g,'<br>');
	txt=txt.replace(/##p1##/g,'');
	txt=txt.replace(/#n0#(.*?)#n1#/g,'');}
	else {
	txt=txt.replace(/##p0##/g,'<p>');
	txt=txt.replace(/##p1##/g,'</p>');
	txt=txt.replace(/#n.#/g,'');
	txt=txt.replace(/#s0#/g,'<span style=\"color: #');
	txt=txt.replace(/#s1#/g,'\">');
	txt=txt.replace(/#se#/g,'</span>');
	}
	if (writing==1)
		{//if you are writing something, don't clear the box
		t = document.getElementById("ctext");
		t.innerHTML = '<div>'+txt+'</div>';
		}
	else
		{
		t = document.getElementById("chats");
		t.innerHTML = '<div>'+txt+'</div>';
		}
	}
}
 	
function updateImagesBackground(req,timer) //make a request to the server which reminds it to update its image bank in the background (response does not matter)
{
	if (updateState==0)
	{
	req.open( "GET", "update", true );
	//req.setRequestHeader("Content-type","application/x-www-form-urlencoded");
	req.send();
	updateState = 1;
	}
	else if (updateState ==2)
	{
		txt = req.responseText;
		updateState = 0;
	}
}
