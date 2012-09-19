#!/bin/bash
#
# download nipa tables
#

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

nipa_dir="bea/nipa"
[ -d "$nipa_dir" ] || mkdir -p "$nipa_dir"

if [ ! -f "$nipa_dir/Section1All_csv.csv" ]; then
    wget "http://bea.gov//national/nipaweb/SS_Data/Section1All_csv.zip"
    unzip -d "$nipa_dir" Section1All_csv.zip
    rm Section1All_csv.zip
fi

if [ ! -f "$nipa_dir/Section2all_csv.csv" ]; then
    wget "http://www.bea.gov//national/nipaweb/SS_Data/Section2All_csv.zip"
    unzip -d "$nipa_dir" Section2All_csv.zip
    rm Section2All_csv.zip
fi

if [ ! -f "$nipa_dir/Section2All_underlying.csv" ]; then
    wget "http://www.bea.gov//national/nipaweb/nipa_underlying/SS_Data/Section2All_csv.zip"
    unzip Section2All_csv.zip
    mv Section2All_csv.csv "$nipa_dir/Section2All_underlying.csv"
    rm Section2All_csv.zip
fi

cd $SCRIPTDIR
