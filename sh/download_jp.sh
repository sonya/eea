#!/bin/bash
#
# download jp tables
# all pages available at http://www.stat.go.jp/english/data/io

year_files()
{
    case "$1" in
        "1990")
            files=
            for i in `seq 46 64`; do
                files="$files 0000007500${i}"
            done
            echo "$files"
            ;;
        "1995")
            files=
            for i in `seq 1 9`; do
                files="$files 00000075000${i}"
            done
            for i in `seq 10 31`; do
                files="$files 0000007500${i}"
            done
            echo "$files"
            ;;
        "2000")
            files=
            for i in `seq 52 60`; do
                files="$files 0000047127${i}"
            done
            for i in `seq 896 902`; do
                files="$files 000004712${i}"
            done
            files="$files 000004713035 000004713036"
            for i in `seq 40 48`; do
                files="$files 0000047130${i}"
            done
            echo "$files"
            ;;
        "2005")
            files="000002581741 000002589207"
            for i in `seq 19 87`; do
                files="$files 0000025685${i}"
            done
            echo $files
            ;;
    esac
}

SCRIPTDIR=`dirname $0`
. "$SCRIPTDIR/include.sh"

cd "${CACHE_DIR}"

stat_dir="${CACHE_DIR}/jp"
[ -d "$stat_dir" ] || mkdir -p "$stat_dir"

base_url="http://www.e-stat.go.jp/SG1/estat/Xlsdl.do?sinfid="

years="1990 1995 2000 2005"
for year in $years; do
    year_dir="$stat_dir/$year"
    [ -d "$year_dir" ] || mkdir -p "$year_dir"

    cd "$year_dir"

    files=`year_files $year`

    for aFile in $files; do
        # TODO: get mapping so we don't download files that exist
        wget --content-disposition "$base_url${aFile}"
    done
done

# manually make a copy of the file we parse twice
cp $stat_dir/1990/l00_21.xls $stat_dir/1995

# 1995 documentation
if [ ! -f "$stat_dir/1995/iosummar.pdf" ]; then
    wget http://www.stat.go.jp/english/data/io/pdf/iosummar.pdf
    mv iosummar.pdf "$stat_dir/1995"
fi

# 2005 documentation
files="ioe05001 ioe05002 ioe05003 ioe05004 ioe05005 ioe05006 ioe05007 ioe05008"
year=2005
year_dir="$stat_dir/$year"
for aFile in $files; do
    pdfFile="$aFile.pdf"
    [ -f "$year_dir/$pdfFile" ] || wget "$base_url/$year/pdf/$pdfFile"
done

# 2005 e-stat files
estat_query="http://www.e-stat.go.jp/SG1/estat/XlsdlE.do?sinfid="
[ -f "ioe05112.xls" ] || wget "${estat_query}00002568519" -O "ioe05112.xls"
[ -f "ioe05113.xls" ] || wget "${estat_query}00002568520" -O "ioe05113.xls"
[ -f "ioe05114.xls" ] || wget "${estat_query}00002568521" -O "ioe05114.xls"
[ -f "ioe05115.xls" ] || wget "${estat_query}00002568522" -O "ioe05115.xls"

# env satellite files at
# http://www.cger.nies.go.jp/publications/report/d031/jpn/datafile/index.htm
base_url="http://www.cger.nies.go.jp/publications/report/d031/jpn/datafile/download"

env_files()
{
    case "$1" in
        "1990")
            echo "ei90407p.zip ei90187p.zip ei90091p.zip ei90032p.zip"
            ;;
        "1995")
            echo "ei95399p.zip ei95186p.zip ei95093p.zip ei95032p.zip"
            ;;
        "2000")
            echo "ei2000p401v00j.xls ei2000p188v00j.xls "\
                 "ei2000p104v01j.xls ei2000p32v00j.xls"
            ;;
        "2005")
            echo "ei2005pc403jp_wt_bd.zip"
            ;;
    esac
}

years="1990 1995 2000 2005"
for year in $years; do
    year_dir="$stat_dir/$year"
    [ -d "$year_dir" ] || mkdir -p "$year_dir"

    cd "$year_dir"

    year_server="$base_url/$year/ei"
    files=`env_files $year`

    for aFile in $files; do
        [ -f "$aFile" ] || wget "$year_server/$aFile"
        extension=${aFile#*.}
        if [ "$extension" = "zip" ]; then
            sampleFile=`zipinfo -1 "$aFile" | head -1`
            [ -f "$year_dir/$sampleFile" ] || unzip "$aFile"
        fi
    done
done

cd "$SCRIPTDIR"

