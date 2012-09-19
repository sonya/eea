#!/bin/bash

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

stat_dir="${CACHE_DIR}/wsupp"
[ -d "$stat_dir" ] || mkdir -p "$stat_dir"

cd "$stat_dir"

if [ ! -f "IDB_DataSet.zip" ]; then
    wget http://www.census.gov/population/international/data/idb/include/IDB_DataSet.zip
    unzip IDB_DataSet.zip
fi

files="NY.GDP.DEFL.ZS_Indicator_MetaData_en_EXCEL.xls PA.NUS.ATLS_Indicator_MetaData_en_EXCEL.xls PA.NUS.PPPC.RF_Indicator_MetaData_en_EXCEL.xls NY.GDP.PCAP.PP.KD_Indicator_MetaData_en_EXCEL.xls NY.GDP.PCAP.CD_Indicator_MetaData_en_EXCEL.xls NY.GNP.PCAP.PP.CD_Indicator_MetaData_en_EXCEL.xls"
for afile in $files; do
    if [ ! -f "$afile" ]; then
        wget "http://api.worldbank.org/datafiles/$afile"
    fi
done

#TODO this needs to be updated everytime IMF releases new data
[ -f "WEOApr2012all.xls" ] || wget "http://www.imf.org/external/pubs/ft/weo/2012/01/weodata/WEOApr2012all.xls"

cd "$SCRIPTDIR"
