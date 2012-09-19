#!/bin/bash
#
# script to download energy price stats from eurostat.
#
# main page:
# http://epp.eurostat.ec.europa.eu/statistics_explained/index.php/Energy_price_statistics
#
# data page:
# http://epp.eurostat.ec.europa.eu/portal/page/portal/energy/data/main_tables
#

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

stat_dir="${CACHE_DIR}/eu"
[ -d "$stat_dir" ] || mkdir -p "$stat_dir"

cd "$stat_dir"

BASE_URL="http://epp.eurostat.ec.europa.eu/tgm/web/_download"

# in order: gas prices for hh consumers, gas prices for industrial consumers,
# electricity for hh, electricity for insutry
tables="00113 00112 00115 00114"

for atable in $tables; do
    filename="Eurostat_Table_ten${atable}FlagDesc.xls"
    [ -f "$filename" ] || wget "${BASE_URL}/${filename}"
done

# not EU dataset but put here for now

filename="eia_world_intensities.xls"
[ -f "$filename" ] || wget -O "$filename" "http://www.eia.gov/cfapps/ipdbproject/XMLinclude_3.cfm?tid=91&pid=46&pdid=&aid=31&cid=regions&titleStr=Carbon%20Intensity%20using%20Market%20Exchange%20Rates%20(Metric%20Tons%20of%20Carbon%20Dioxide%20per%20Thousand%20Year%202005%20U.S.%20Dollars)&syid=1995&eyid=2009&form=&defaultid=3&typeOfUnit=STDUNIT&unit=MTCDPUSD&products="

cd "$SCRIPTDIR"

