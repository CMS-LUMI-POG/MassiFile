cd ~marlow/brilcalc
source ./setenv.csh
cd ~marlow/brilcalc/massi
export MASSIDIR=~marlow/work/massi
export NORMTAG_XING=~marlow/brilcalc/Normtags/normtag_xing.json
export NORMTAG_BYLS=~marlow/brilcalc/Normtags/normtag_byls.json
export LUMIDIR=~marlow/work/massi/lumi
export BEAMDIR=~marlow/work/massi/beam
export MASSIDIR=~marlow/work/massi

export FILL=$1

#make input files using brilcalc
brilcalc lumi --tssec --byls --xing --xingMin 0.01 --normtag $NORMTAG_XING -f $FILL  -o $LUMIDIR/Fill${FILL}_xing.csv
brilcalc lumi --tssec --byls --normtag $NORMTAG_BYLS -f $FILL  -o $LUMIDIR/Fill${FILL}_byls.csv
brilcalc beam --tssec --xing -f $FILL -o $BEAMDIR/Fill${FILL}_beam.csv

#process them to make the Massi files
python makeMassiFile.py --normalize -f $FILL -d $MASSIDIR 

#move and compress the files
cd $MASSIDIR
mv ./filldata/$FILL ./dev/.
cd ./dev 
tar -cvzf $FILL.tgz $FILL 
cd ~marlow/brilcalc/massi



