#!/usr/bin/env bash
# OpenNEM script to mirror AEMO MMS archives for a year and month
# locally. See usage for more info.ç
set -eo pipefail

usage() { echo "Usage: $0 [-y <year>] [-m <month>]" 1>&2; exit 1; }

unset wgetpath
unset desinationdir
unset year
unset month
unset ignore
unset ignore_files

wgetpath=`which wget`
desinationdir=data/mms

if ! [ -x "$(command -v $wgetpath)" ]; then
  echo "Require wget"
  exit -1
fi

if ! [ -d $desinationdir ]; then
  echo "Creating destination $desinationdir"
  mkdir -p $desinationdir
fi

while getopts ":y:m:i" flag
do
  case "${flag}" in
    y ) year=${OPTARG};;
    m ) printf -v month "%02d" ${OPTARG};;
    i ) ignore=1;;
    : ) usage;;
  esac
done

shift "$(( OPTIND - 1 ))"

if [ -z "$year" ] || [ -z "$month" ]; then
  echo 'Missing -y or -m' >&2
  usage
fi

echo "Downloading for year $year and month $month"

dist_url="http://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/$year/MMSDM_${year}_${month}/"

# test if distribution is available

echo -n "Checking $dist_url .. "

status=$(curl -s --head -w %{http_code} $dist_url -o /dev/null)
echo -n " ($status) "

if ! [ "$status" = "200" ]; then
  echo " FAILED"
  echo "Invalid year and month specified."
  exit -1
else
  echo " OK "
fi

# Ignore files - larger bidoffer and p5min files
ignore_files="index.htm*"

if [ "$ignore" = 1 ]; then
  ignore_files="${ignore_files}, PUBLIC_DVD_BIDPEROFFER*, PUBLIC_DVD_P5MIN_*"
fi

$wgetpath \
  -r `# recursive` \
  -c `# continue broken` \
  -x \
  -nH \
  -np \
  -nv \
  --timestamping \
  -R ${ignore_files} \
  --retry-connrefused \
  -t20 \
  --retry-on-http-error=403,501,503 \
  --random-wait \
  --cut-dirs 3 \
  --limit-size 100M \
  -P ${desinationdir} \
  -U "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0" \
  $dist_url

