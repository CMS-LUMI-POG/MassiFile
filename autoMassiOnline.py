import os

# get last fill from brilcalc 
lastFillLine = open('brilout.txt','r').readlines()[0]
vals = lastFillLine.split(',')
lastFill = int(vals[0].split(':')[1])
print ("lastFill from brilout = {0:d}".format(lastFill))

lastFillProcessed = int(open('LASTFILLONLINE','r').read())

if lastFill > lastFillProcessed :
    print ("Updating Massi files for fill {0:d}".format(lastFill))
    open('LASTFILLONLINE','w').write("{0:d}".format(lastFill))
    os.system("source ./runMassiOnline.csh {0:d}".format(lastFill))
else :
    print ("Massi files up to date")

    
        
        
    
