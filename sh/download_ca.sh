#!/bin/bash
#
# download ca tables
# index at http://www.statcan.gc.ca/nea-cen/index-eng.htm

base_url="http://www20.statcan.gc.ca/tables-tableaux/cansim/csv"

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

stat_dir="${CACHE_DIR}/ca"
[ -d "$stat_dir" ] || mkdir -p "$stat_dir"

cd "$stat_dir"

http://www20.statcan.gc.ca/tables-tableaux/cansim/csv/03810010-eng.zip

files="01530031 01530032 01530033 01530034 01530046 03810009 03810010 03810011 03810012 03810013 03810014 03810019 03810020 03810021"

for file in $files; do
    zipFile="${file}-eng.zip"
    [ -f "$zipFile" ] || wget "$base_url/$zipFile"

    csvFile="${file}-eng.csv"
    # T here stands for terminated series, not tab-separated values
    tsvFile=${csvFile/038/T38}
    [ -f "$csvFile" ] || [ -f "$tsvFile" ] || unzip "$zipFile"
done

cd "$SCRIPTDIR"
