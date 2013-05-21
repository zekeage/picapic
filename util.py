import random
import urllib

def randperm(x):
    n = len(x)-1
    y = []
    while n >=0:
        i = random.randint(0,n)
        y.append(x.pop(i))
        n -= 1
    return y


#===============================================================================
# def unescape(s):
#    s=s.replace("##sc##",";",9999)
#    s=s.replace("##sq##",'\'',9999)
#    s=s.replace("##dq##",'\"',9999)
#    return s
#===============================================================================

        
def getQuote(url,i):
    url = url+'/clues/'+str(i)+'.html'
    #logging.error('t'+url)
    response = urllib.urlopen(url)
    quote = response.read()
    quote = quote.rstrip()
    quote = quote.replace(';','##sc##',9999)
    quote = quote.replace('\"','##dq##',9999)
    quote = quote.replace('\'','##sq##',9999)
    return quote