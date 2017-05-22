#! /usr/bin/env python

# take fill lumi files as input and convert them to condensed run lumi files

import numpy
import time
import glob
import os
import copy

def getArgs() :
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--fill", type=int, help="Fill number")
    parser.add_argument("-c", "--currentThreshold", type=float, default = 5.e8, help="Single bunch current threshold in number of protons.")
    parser.add_argument("--currentProduct", type=float, default = 1.e20, help="Single bunch current product in number of protons**2.")
    parser.add_argument("-p","--printLevel", type=int, help="Print level")
    parser.add_argument("-d","--massiDir",default = '.',help="Directory where files are stored.")
    parser.add_argument("-n","--normalize",action='store_true',help="Normalize to separate byls file.") 
    return parser.parse_args()

def openOutputFiles(fill) :
    fError = open('{0:s}/logs/Fill{1:d}_errors.txt'.format(massiDir,fill),'w')     

    # make a directory for this fill
    dir = "{0:s}/filldata/{1:d}".format(massiDir,fill) 
    try:
        os.stat(dir)
    except:
        os.mkdir(dir)

    #open various output files 
    lumiAverageFileName = "{0:s}/{1:d}_lumi_CMS.txt".format(dir,fill)
    fAverage = open(lumiAverageFileName,'w')
    
    lumiSummaryFileName = "{0:s}/{1:d}_summary_CMS.txt".format(dir,fill)
    fSummary = open(lumiSummaryFileName,'w')
    
    if printLevel > 0 : print "Output files opened."

    return dir, fError, fAverage, fSummary

def makeBeamDictionary(fill) :
    beamDict = {}
    currentThreshold = args.currentThreshold
    masterPattern = numpy.zeros(3565,dtype=bool) 
    fName = '{0:s}/beam/Fill{1:d}_beam.csv'.format(args.massiDir,fill)
    #4006,251857,112,1436980763,[1 1.2046e+11 0.0000e+00 3 1.2612e+11 0.0000e+00 5 1.0991e+11 0.0000e+00 7 1.1117e+11 0.0000e+00
    nBX = 0
    for line in open(fName,'r').readlines()[2:] :
        vals = line.split(',')
        runLS = "{0:s}:{1:04d}".format(vals[1],int(vals[2]))
        BXvals = (vals[4].lstrip('[').rstrip(']')).split()
        i1i2BX = numpy.zeros(3565)
        for i in range(0,len(BXvals),3) :
            i1 = float(BXvals[i+1])
            i2 = float(BXvals[i+2].rstrip(']'))
            if i1*i2 > args.currentProduct :
                nBX += 1
                i1i2BX[int(BXvals[i])] = i1*i2
                masterPattern[int(BXvals[i])] = True 
            
        beamDict[runLS] = i1i2BX

    if nBX <= 0 :
        print("****\n****\n**** WARNING No active bunches found in beam current file.\n****\n****")
    else :
        nnBX = 0
        for i in range(len(masterPattern)) :
            if masterPattern[i] : nnBX += 1
        print ("nnBX={0:d} active bunches found.  N(BX x LS)={1:d} in beam current file.".format(nnBX,nBX))
        
    return beamDict, masterPattern

def getLumiByLS(fill) :
    fName = '{0:s}/lumi/Fill{1:d}_byls.csv'.format(args.massiDir,fill)
    #run:fill,ls,time,beamstatus,E(GeV),delivered(/ub),recorded(/ub),avgpu,source
    #262199:4638,59:59,11/20/15 12:04:26,FLAT TOP,2510,0.598,0.593,0.0,PLTZERO
    totalInstLumi = {}
    for line in open(fName,'r').readlines()[2:] :
        if len(line) < 10 : continue 
        vals = line.split(',')
        if len(vals) < 4 : continue 
        if vals[3] != 'STABLE BEAMS' : continue
        LS = "{0:04d}".format(int(vals[1].split(':')[0]))
        runLS = vals[0].split(':')[0] + ':' + LS 
        totalInstLumi[runLS] = float(vals[5])/LStime

    return totalInstLumi 

def normalizeLumiDictionary(fill,lumiDict, timeStampDict) :

    totalInstLumi = getLumiByLS(fill)

    for runLS in sorted(lumiDict.keys()) :
        if runLS in totalInstLumi.keys() :
            sumBX = numpy.sum(lumiDict[runLS])
            #print("runLS={0:s} lumiDict[runLS][160:180]={1:s}".format(runLS,str(lumiDict[runLS][160:180])))
            if sumBX > 0. :
                scaleFactor = totalInstLumi[runLS]/sumBX
                lumiDict[runLS] *= scaleFactor
                #print("runLS={0:s} timeStamp={1:f} sumBX={2:.1f} totalInstLumi={3:.1f} scaleFactor={4:.3f}".format(
                #    runLS, timeStampDict[runLS], sumBX, totalInstLumi[runLS], scaleFactor))

    return lumiDict 
                
def makeLumiDictionary(fill) :
    lumiDict, timeStampDict, LHCstatusDict = {}, {}, {}
    fName = '{0:s}/lumi/Fill{1:d}_xing.csv'.format(args.massiDir,fill)
    #260575:4562,1:1,1446413852,STABLE BEAMS,6500,96631.047,0.000,0.0,PLTZERO,[1 0.0105 0.0000 7 0.0105 0.0000 8 0.0105 0.0000 10 0.0105 . . .
    for line in open(fName,'r').readlines()[2:] :
        if len(line) < 70 : continue 
        vals = line.split(',')
        LS = "{0:04d}".format(int(vals[1].split(':')[0]))
        runLS = vals[0].split(':')[0] + ':' + LS 
        timeStampDict[runLS] = float(vals[2])
        LHCstatusDict[runLS] = vals[3] 
        BXvals = (vals[9].lstrip('[').rstrip(']')).split()
        lumiBX = numpy.zeros(3565)
        if len(BXvals) > 1:
            nnBX = 0 
            for i in range(0,len(BXvals),3) :
                lumiBX[int(BXvals[i])] = float(BXvals[i+1])/LStime
                if lumiBX[int(BXvals[i])] > 0.1 : nnBX += 1 

        lumiDict[runLS] = lumiBX

    if args.normalize :
        normalizedLumiDict = normalizeLumiDictionary(fill,lumiDict,timeStampDict) 
        return normalizedLumiDict, timeStampDict, LHCstatusDict
    else :
        return lumiDict, timeStampDict, LHCstatusDict

def getLumiThreshold(lumiBX) :
    if len(lumiBX.keys()) == 0 : return 0.
    maxLumi = 0. 
    for BX in lumiBX.keys() : maxLumi = max(lumiBX[BX],maxLumi)
    return 0.05*maxLumi

def fixBXlumiList(BXlumiList) :
    #unpack the dictionary into a standard array
    temp = numpy.zeros(3565)
    corr = numpy.zeros(3565)
    for key in BXlumiList.keys() : temp[key] = BXlumiList[key]
    shiftFraction = 0.5725 # fraction of lumi that is shifted by +1 BX
    for i in range(len(temp)) :
        if i==0 or temp[i-1] < 0.01 :   # Leading/solo bunch, leave this alone
            corr[i] = temp[i]
        elif temp[i+1] < 0.01 :       # Trailing bunch, shift this all into the previous BX
            corr[i-1] += temp[i]
            corr[i] = 0
        else :                          # Train bunch, shift a fraction of this into the previous BX
            corr[i-1] += temp[i]*shiftFraction
            corr[i] = temp[i]*(1.-shiftFraction)

    # load this back in to a dictionary
    correctedList = {}
    for i in range(len(corr)) :
        if corr[i] > 0.01 :
            correctedList[i] = corr[i]

    return correctedList

def printMasterPattern(masterPattern) :
    print "masterPattern="
    nBX = 0
    st1 = ""
    for i in range(3565) :
        if masterPattern[i] :
            nBX += 1
            st1 += "{0:5d}".format(i)
            if nBX % 20 == 0 :
                print st1
                st1 = ""
    print "{0:d} non-zero bunches total".format(nBX)
    return nBX
            
#####################################################################################################################
#
# begin execution here
#
#####################################################################################################################

#  General strategy
#    1) Make list of active BXes based on FBCT
#    2) Loop over these bunches
#         In each case find an order set of runLS values
#         Loop over the ordered list of runLS values
#            Find the luminosity for that [runLS][BX] entry

LStime = 23.31 
decimationFactor = 1    # report results for only every nth LS 
args = getArgs()
printLevel = args.printLevel
massiDir = args.massiDir
fill = int(args.fill) 

# open a directory for this fill

dir, fError, fAverage, fSummary = openOutputFiles(fill)
print ("dir={0:s} \nfError={1:s} \nfAverage={2:s} \nfSummary={3:s}".format(dir,fError.name,fAverage.name,fSummary.name))

beamDict, masterPattern = makeBeamDictionary(fill)
lumiDict, timeStampDict, LHCstatusDict = makeLumiDictionary(fill)

sortedRunLS = beamDict.keys()
sortedRunLS.sort()
if args.printLevel > 0 :
    print "sortedRunLS (from beam)={0:s}".format(str(sortedRunLS))
    print "lumiDict.keys() (from lumi)={0:s}".format(str(lumiDict.keys()))
    nnBX = printMasterPattern(masterPattern)

print("******* in main program **********")
for runLS in sortedRunLS :
    try :
        sumBX = numpy.sum(lumiDict[runLS])
        #print("runLS={0:s} timeStamp={1:.1f} {2:0.3f}".format(runLS, timeStampDict[runLS], sumBX))
    except KeyError :
        #print("KeyError in print loop runLS={0:s}".format(runLS))
        pass 

    
# start with summary file, which is based on byLS data only
# note that getLumiByLS() returns total instantaneous lumi
byLSLumi = getLumiByLS(fill)
startTime, endTime, totalLumi, peakLumi = 1.e12, 0., 0., 0.
for runLS in byLSLumi.keys() :
    try :
        startTime = min(startTime,timeStampDict[runLS])
        endTime = max(endTime,timeStampDict[runLS])
        totalLumi += LStime*byLSLumi[runLS]
        peakLumi = max(peakLumi,byLSLumi[runLS])
    except KeyError :
        print ("KeyError for runLS={0:s}".format(runLS))

fSummary.write("{0:f} {1:f} {2:f} {3:f}".format(startTime,endTime+LStime,peakLumi,totalLumi))
print("start={0:.1f} stop={1:.1f} peak={2:.3f}Hz/ub totalLumi={3:.3f} /pb".format(
        startTime,endTime+LStime,peakLumi,1.e-6*totalLumi))
fSummary.close()

# make the files for the individual bunches 
beamThreshold = args.currentThreshold*args.currentThreshold
nBX, nRunLSBeam, nRunLSLumi = 0, 0, 0
nAverage,lumiAverage, specificLumiAverage = {}, {}, {}

checkRunLS, checkSum, nBXFiles = '274157:0104', 0. , 0
for iBX in range(3564) :
    if masterPattern[iBX] :
        if args.printLevel > -1 : print "iBX={0:d}".format(iBX) 
        lines = []
        nBX += 1 
        for runLS in sortedRunLS :
            nRunLSBeam += 1
            if runLS in lumiDict.keys() :
                if LHCstatusDict[runLS] == 'STABLE BEAMS' :
                    nRunLSLumi += 1
                    specificLumi = 0.
                    i1i2 = beamDict[runLS][iBX]
                    #if i1i2 < beamThreshold and lumiDict[runLS][iBX] > 0.1 :
                    #    print("not active BX={0:d} runLS={1:s} lumiDict[runLS][iBX]={2:.3f}".format(iBX,runLS,lumiDict[runLS][iBX]))
                        
                    if i1i2 > beamThreshold :
                        lumi = lumiDict[runLS][iBX]
                        if runLS == checkRunLS : checkSum += lumi 
                        specificLumi = lumi/i1i2
                        lines.append("{0:.1f} 1.0 {1:f} {2:f} {3:e} {4:e}\n".format(timeStampDict[runLS],
                                    lumi,0.025*lumi,specificLumi,0.025*specificLumi))
                        if not runLS in nAverage.keys() :
                            nAverage[runLS] = 1
                            lumiAverage[runLS] = lumi
                            specificLumiAverage[runLS] = specificLumi
                        else :
                            nAverage[runLS] += 1
                            lumiAverage[runLS] += lumi
                            specificLumiAverage[runLS] += specificLumi
                            
            else :
                if args.printLevel > 1 :
                    print ("runLS {0:s} not in lumiDict.keys()".format(runLS)) 

        if args.printLevel > 0 : print "iBX={0:4d} len(lines)={1:4d}".format(iBX,len(lines))
        nBXFiles += 1
        with open("{0:s}/filldata/{1:d}/{1:d}_lumi_{2:d}_CMS.txt".format(massiDir,fill,10*(iBX-1)+1),'w') as f: 
            f.writelines(lines)
    
print ("nBX={0:4d} nRunLSBeam={1:5d} nRunLSLumi={2:5d}".format(nBX,nRunLSBeam,nRunLSLumi))

print("checkRunLS={0:s} checkSum={1:.3f} nBXFiles={2:d}".format(checkRunLS, checkSum, nBXFiles))

# compute and print average values
lines = []
if args.printLevel > 0 :
    print("nAverage.keys()={0:s}".format(str(nAverage.keys())))
for runLS in sortedRunLS :
    if runLS in nAverage.keys() :
        #lumiAverage[runLS] /= nAverage[runLS]
        specificLumiAverage[runLS] /= nAverage[runLS]
        line = "{0:.1f} 1.0 {1:f} {2:f} {3:e} {4:e}\n".format(timeStampDict[runLS],
            lumiAverage[runLS],0.025*lumiAverage[runLS],specificLumiAverage[runLS],0.025*specificLumiAverage[runLS])
        lines.append(line)
        
with open("{0:s}/filldata/{1:d}/{1:d}_lumi_CMS.txt".format(massiDir,fill),'w') as f: 
    f.writelines(lines)


    

        
    

        
        
    


    
    
    
    
