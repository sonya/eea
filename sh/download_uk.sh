#!/bin/bash
#

# environmental accounts
# http://www.ons.gov.uk/ons/publications/re-reference-tables.html?edition=tcm%3A77-224120
#

base_url="http://www.ons.gov.uk/ons"
env_url="$base_url/rel/environmental/uk-environmental-accounts/2011---blue-book-update"

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

stat_dir="${CACHE_DIR}/uk"
[ -d "$stat_dir" ] || mkdir -p "$stat_dir"

cd "$stat_dir"

[ -f "rftsupplyuse.xls" ] || wget "$env_url/rftsupplyuse.xls"
[ -f "rftghgemissions.xls" ] || wget "$env_url/rftghgemissions.xls"
[ -f "rftghg-intensity.xls" ] || wget "$env_url/rftghg-intensity.xls"

#
# input output accounts
# http://www.ons.gov.uk/ons/search/index.html?newquery=input+output
# the urls here will probably go out of date in a year
#

base_url="http://www.ons.gov.uk/ons"
io_url="$base_url/rel/input-output/input-output-supply-and-use-tables"

# /ons/publications/re-reference-tables.html?edition=tcm%3A77-238342

[ -f "input-output-supply-and-use-tables--2004-2008.xls" ] || wget "$io_url/2010-edition/input-output-supply-and-use-tables--2004-2008.xls"
[ -f "2010-summary-tables.xls" ] || wget "$io_url/2010-edition/2010-summary-tables.xls"

# /ons/publications/re-reference-tables.html?edition=tcm%3A77-238333

[ -f "bb09-su-tables-1992-2003.xls" ] || wget "$io_url/2009/bb09-su-tables-1992-2003.xls"
[ -f "bb09-su-tables-2004-2007.xls" ] || wget "$io_url/2009/bb09-su-tables-2004-2007.xls"
[ -f "2009-summary-tables-a.xls" ] || wget "$io_url/2009/2009-summary-tables-a.xls"
[ -f "2009-summary-tables-b.xls" ] || wget "$io_url/2009/2009-summary-tables-b.xls"

cd "$SCRIPTDIR"
