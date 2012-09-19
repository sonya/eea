#!/bin/bash

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

stat_dir="${CACHE_DIR}/eia"
[ -d "$stat_dir" ] || mkdir -p "$stat_dir"

cd "$stat_dir"

if [ ! -f "Data File Codes and Descriptions.xls" ]; then
    wget http://www.eia.gov/state/seds/CDF/Data%20File%20Codes%20and%20Descriptions.xls
fi

if [ ! -f "use_all_phy.csv" ]; then
    wget http://www.eia.gov/state/seds/sep_use/total/csv/use_all_phy.zip
    unzip use_all_phy.zip
    rm use_all_phy.zip
fi

if [ ! -f "use_all_btu.csv" ]; then
    wget http://www.eia.gov/state/seds/sep_use/total/csv/use_all_btu.zip
    unzip use_all_btu.zip
    rm use_all_btu.zip
fi

if [ ! -f "pr_all.csv" ]; then
    wget http://www.eia.gov/state/seds/sep_prices/total/csv/pr_all.zip
    unzip pr_all.zip
    rm pr_all.zip
fi

if [ ! -f "ex_all.csv" ]; then
    wget http://www.eia.gov/state/seds/sep_prices/total/csv/ex_all.zip
    unzip ex_all.zip
    rm ex_all.zip
fi

# TODO these files are from dynamic tables at
# http://www.eia.gov/cfapps/ipdbproject/IEDIndex3.cfm?tid=2&pid=2&aid=7
# the ending year parameter may need to be updated

aids="7:consumption 12:capacity"
pids="2:total 27:nuclear 28:thermal 29:renewable 35:geothermal 36:solar 37:wind 38:biomass"
urlbase="http://www.eia.gov/cfapps/ipdbproject/XMLinclude_3.cfm"

for aid_str in $aids; do
    aid=${aid_str%:*}
    aid_title=${aid_str#*:}
    for pid_str in $pids; do
        pid=${pid_str%:*}
        pid_title=${pid_str#*:}
        if [ ! -f "${pid_title}_${aid_title}.xls" ]; then
            titlestr="${pid_title}%20${aid_title}"
            if [ "$aid" = "12" ]; then
                endyear=2010
                unit="BKWH"
            else
                endyear=2009
                unit="MK"
            fi
            wget --content-disposition "${urlbase}?tid=2&pid=${pid}&aid=${aid}&pdid=&cid=regions&titleStr=${titlestr}&syid=1980&eyid=${endyear}&form=&defaultid=3&typeOfUnit=STDUNIT&unit=${unit}&products="
        fi
    done
done

cd "${SCRIPTDIR}"

