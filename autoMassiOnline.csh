cd ~marlow/brilcalc
source ./setenv.csh
brilcalc lumi --begin "06/01/16 00:00:00" --output-style csv -b "STABLE BEAMS" | tail -4 > brilout.txt
python autoMassiOnline.py 

        
        
    
