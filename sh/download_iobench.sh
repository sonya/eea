#!/bin/bash

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

[ -d "1947" ] || mkdir 1947 # benchmark
if [ ! -f "1947/1947 sectoring plan.pdf" ]; then
    wget http://bea.gov/industry/zip/47IOtext.zip
    unzip -d 1947 47IOtext.zip && rm 47IOtext.zip
fi

[ -d "1958" ] || mkdir 1958 # benchmark
if [ ! -f "1958/1958 Sectoring Plan.pdf" ]; then
    wget http://bea.gov/industry/zip/58IOtext.zip
    unzip -d 1958 58IOtext.zip && rm 58IOtext.zip
fi

[ -d "1963" ] || mkdir 1963 # benchmark
if [ ! -f "1963/1963 Sectoring Plan.rtf" ]; then
    wget http://bea.gov/industry/zip/63IO367-leveltext.zip
    unzip -d 1963 63IO367-leveltext.zip && rm 63IO367-leveltext.zip
fi

[ -d "1967" ] || mkdir 1967 # benchmark
if [ ! -f "1967/1967 Sectoring Plan.rtf" ]; then
    wget http://bea.gov/industry/zip/67IO484-leveltext.zip
    unzip -d 1967 67IO484-leveltext.zip && rm 67IO484-leveltext.zip
fi
if [ ! -f "1967/1967_PCE_Commodity.xls" ]; then
    wget http://bea.gov/industry/zip/1967_PCE_Commodity.zip
    unzip -d 1967 1967_PCE_Commodity.zip && rm 1967_PCE_Commodity.zip
fi

[ -d "1972" ] || mkdir 1972 # benchmark
if [ ! -f "1972/1972 Sectoring Plan.rtf" ]; then
    wget http://bea.gov/industry/zip/72IO496-leveltext.zip
    unzip -d 1972 72IO496-leveltext.zip && rm 72IO496-leveltext.zip
fi
if [ ! -f "1972/1972_PCE_Commodity.xls" ]; then
    wget http://bea.gov/industry/zip/1972_PCE_Commodity.zip
    unzip -d 1972 1972_PCE_Commodity.zip && rm 1972_PCE_Commodity.zip
fi

[ -d "1977" ] || mkdir 1977 # benchmark
if [ ! -f "1977/1977 Sectoring Plan.rtf" ]; then
    wget http://bea.gov/industry/zip/77IO537-leveltext.zip
    unzip -d 1977 77IO537-leveltext.zip && rm 77IO537-leveltext.zip
fi
if [ ! -f "1977/1977_PCE_Commodity.xls" ]; then
    wget http://bea.gov/industry/zip/1977_PCE_Commodity.zip
    unzip -d 1977 1977_PCE_Commodity.zip && rm 1977_PCE_Commodity.zip
fi

[ -d "1982" ] || mkdir 1982 # benchmark
if [ ! -f "1982/Readme.doc" ]; then
    wget http://bea.gov/industry/zip/ndn0025.zip
    unzip -d 1982 ndn0025.zip && rm ndn0025.zip
    unzip -d 1982 1982/82-6dt.exe && rm 1982/82-6dt.exe
fi
if [ ! -f "1982/1982_PCE_Commodity.xls" ]; then
    wget http://bea.gov/industry/zip/1982_PCE_Commodity.zip
    unzip -d 1982 1982_PCE_Commodity.zip && rm 1982_PCE_Commodity.zip
fi

[ -d "1987" ] || mkdir 1987 # benchmark
if [ ! -f "1987/README.DOC" ]; then
    wget http://bea.gov/industry/zip/ndn0016.zip
    unzip -d 1987 ndn0016.zip && rm ndn0016.zip
    unzip -d 1987 1987/disk1.zip && rm 1987/disk1.zip
    unzip -d 1987 1987/disk2.zip TBL2-87.DAT && rm 1987/disk2.zip
    unzip -d 1987 1987/disk3.zip TBL3-87.DAT && rm 1987/disk3.zip
fi
if [ ! -f "1987/readme-ionipa.doc" ]; then
    wget http://bea.gov/industry/zip/ndn0021.zip
    unzip -d 1987 ndn0021.zip -x io-code.fmt mathio.doc readme.bat \
        sic-io.doc io-code.doc
    mv 1987/readme.doc 1987/readme-ionipa.doc
fi

[ -d "1992" ] || mkdir 1992 # benchmark
if [ ! -f "1992/ReadMe.txt" ]; then
    wget http://bea.gov/industry/zip/ndn0178.zip
    unzip -d 1992 ndn0178.zip && rm ndn0178.zip
    unzip -d 1992 1992/disk1.zip && rm 1992/disk1.zip
    unzip -d 1992 1992/disk2.zip && rm 1992/disk2.zip
    unzip -d 1992 1992/disk3.zip && rm 1992/disk3.zip
fi
if [ ! -f "1992/ReadMe-IONIPA.txt" ]; then
    wget http://bea.gov/industry/zip/ndn0186.zip
    mkdir extract
    unzip ndn0186.zip -d extract -x IO-Code.txt IOXtract.txt MathIO.txt \
        Sic-IO.txt IO-Code.fmt && rm ndn0186.zip
    mv extract/ReadMe.txt 1992/ReadMe-IONIPA.txt
    mv extract/* 1992 && rmdir extract
fi

[ -d "1996" ] || mkdir 1996 # annual
if [ ! -f "1996/ReadMe.txt" ]; then
    wget http://bea.gov/industry/zip/ndn0247.zip
    unzip -d 1996 ndn0247.zip && rm ndn0247.zip
fi

[ -d "1997" ] || mkdir 1997 # benchmark
if [ ! -f "1997/ReadMe.txt" ]; then
    wget http://bea.gov/industry/zip/ndn0306.zip # before redefs
    unzip -d 1997 ndn0306.zip && rm ndn0306.zip
fi
if [ ! -f "1997/ReadMe-HSConcord.txt" ]; then
    wget http://bea.gov/industry/zip/NDN0317.zip
    unzip NDN0317.zip && rm NDN0317.zip
    mv HSConcord.txt 1997
    mv ReadMe.txt 1997/ReadMe-HSConcord.txt
fi
if [ ! -f "1997/1997import_matrix.xls" ]; then
    wget http://bea.gov/industry/xls/1997import_matrix.xls
    mv 1997import_matrix.xls 1997
fi
if [ ! -f "1997/ReadMe-IONIPA.txt" ]; then
    wget http://bea.gov/industry/zip/ndn0311.zip
    unzip ndn0311.zip && rm ndn0311.zip
    mv ndn0311/ReadMe.txt 1997/ReadMe-IONIPA.txt
    mv ndn0311/*Appendix* 1997
    mv ndn0311/*IO-CodeSummary.txt 1997
    mv ndn0311/*NIPA* 1997
    rm -r ndn0311
fi

#wget http://bea.gov/industry/zip/ndn0271.zip # annual

[ -d "1998" ] || mkdir 1998 # annual
if [ ! -f "1998/ReadMe.txt" ]; then
    wget http://bea.gov/industry/zip/ndn0291.zip
    unzip -d 1998 ndn0291.zip && rm ndn0291.zip
fi

[ -d "1999" ] || mkdir 1999 # annual
if [ ! -f "1999/README.txt" ]; then
    wget http://bea.gov/industry/zip/NDN0313.zip
    unzip -d 1999 NDN0313.zip && rm NDN0313.zip
fi

[ -d "2002" ] || mkdir 2002 # benchmark
if [ ! -f "2002/ReadMe.txt" ]; then
    wget http://bea.gov/industry/zip/2002detail.zip # before redefs
    unzip -d 2002 2002detail.zip && rm 2002detail.zip
fi
if [ ! -f "2002/2002import_matrix.xls" ]; then
    wget http://bea.gov/industry/xls/2002import_matrix.xls
    mv 2002import_matrix.xls 2002
fi
if [ ! -f "2002/HSConcord.xls" ]; then
    wget http://bea.gov/industry/xls/HSConcord.xls
    mv HSConcord.xls 2002
fi
if [ ! -f "2002/2002_PCE_Bridge.xls" ]; then
    wget http://bea.gov/industry/zip/2002_PCE_PES_Bridge_Tables.zip
    unzip 2002_PCE_PES_Bridge_Tables.zip
    mv 2002_PCE_PES_Bridge_Tables/* 2002 && rmdir 2002_PCE_PES_Bridge_Tables
fi

# annual accounts

[ -d "io-annual" ] || unzip ../io-annual.zip

# travel and tourism accounts

satellite_dir="bea/satellite/tourism"
[ -d "$satellite_dir" ] || mkdir -p "$satellite_dir"
if [ ! -f "$satellite_dir/ReadMe.txt" ]; then
    wget http://www.bea.gov/industry/zip/TTSA_2011.zip
    unzip -d "$satellite_dir" TTSA_2011.zip
    rm TTSA_2011.zip
fi

cd $SCRIPTDIR
