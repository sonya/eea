#!/bin/bash

base_url="http://www.wiod.org/protected3/data/"

getfiles()
{
    while [ ! -z "$1" ]; do
        #for afile in "$1"; do
        afile="$1"
        filename=${afile#*/}
        [ -f "$filename" ] || wget "${base_url}${afile}"

        if [ "${afile##*.}" = "zip" ]; then
            dirname=${afile%/*}
            [ -d "$dirname" ] || unzip -d "$dirname" "$filename"
        fi

        shift
    done
}

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

stat_dir="${CACHE_DIR}/wiod"
[ -d "$stat_dir" ] || mkdir -p "$stat_dir"

cd "$stat_dir"

# environment accounts:
# http://www.wiod.org/database/ea.htm
getfiles EU/EU_may12.zip EM/EM_may12.zip CO2/CO2_may12.zip AIR/AIR_may12.zip land/lan_may12.zip materials/mat_may12.zip water/wat_may12.zip

# national supply and use
# pyp = previous year prices
# default is current prices
# http://www.wiod.org/database/nat_suts.htm
getfiles suts/sut_feb12.zip niot/NIOT_row_apr12.zip niot/NIOT_row_pyp_apr12.zip

# national tables based on trade (skipping):
# http://www.wiod.org/database/nat_suts_bas.htm

# international input output
# http://www.wiod.org/database/iot.htm
getfiles intsuts_analytic/intsut_row_apr12.zip wiot_analytic/wiot_row_apr12.zip

# international trade:
# http://www.wiod.org/database/iot_trade_bas.htm
getfiles intsuts_basic/intsut_apr12.zip wiot_basic/wiot_apr12.zip exr_wiod.xls

# socioeconomic tables
# http://www.wiod.org/database/sea.htm
getfiles sea/sea_feb12.zip

cd "$SCRIPTDIR"

