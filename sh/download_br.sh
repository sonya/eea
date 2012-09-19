#!/bin/bash
#
# brazilian input output tables in 12 and 55 sectors
# http://www.ibge.gov.br/home/estatistica/economia/matrizinsumo_produto/default.shtm
#

base_url="ftp://ftp.ibge.gov.br/Matriz_insumo-produto"
years="2000 2005"
sizes="12 55"

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

stat_dir="${CACHE_DIR}/br"
[ -d "$stat_dir" ] || mkdir -p "$stat_dir"

cd "$stat_dir"

for year in $years; do
    for size in $sizes; do
        dirname="${year}-s${size}"
        [ -d "$dirname" ] || mkdir "$dirname"

        zipFile="${dirname}.zip"
        url="${base_url}/MIPN${size}/${year}.zip"
        [ -f "$zipFile" ] || wget "$url" -O "$zipFile"

        cd "$dirname"
        if [ ! -f "tab01.xls" ]; then
            unzip "../$zipFile"
            mv $year/* . && rmdir "$year"
        fi
        cd ..
    done
done

cd "$SCRIPTDIR"
