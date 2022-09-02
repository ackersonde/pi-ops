#!/bin/bash

# parameters
USERNAME="{{FRITZ_BOX_USER}}"
PASSWORD="{{FRITZ_BOX_PASS}}"
CERTPATH="/etc/letsencrypt/live/ackerson.de"
HOST=https://fritz.ackerson.de
WGET="wget" # add `--no-check-certificate` if/when you've missed the expiration

# make and secure a temporary file
TMP="$(mktemp -t XXXXXX)"
chmod 600 $TMP

# login to the box and get a valid SID
CHALLENGE=`$WGET -q -O - $HOST/login_sid.lua | sed -e 's/^.*<Challenge>//' -e 's/<\/Challenge>.*$//'`
HASH="`echo -n $CHALLENGE-$PASSWORD | iconv -f ASCII -t UTF16LE |md5sum|awk '{print $1}'`"
SID=`$WGET -q -O - "$HOST/login_sid.lua?sid=0000000000000000&username=$USERNAME&response=$CHALLENGE-$HASH"| sed -e 's/^.*<SID>//' -e 's/<\/SID>.*$//'`

# generate our upload request
BOUNDARY="---------------------------"`date +%Y%m%d%H%M%S`
printf -- "--$BOUNDARY\r\n" >> $TMP
printf "Content-Disposition: form-data; name=\"sid\"\r\n\r\n$SID\r\n" >> $TMP
printf -- "--$BOUNDARY\r\n" >> $TMP
printf "Content-Disposition: form-data; name=\"BoxCertImportFile\"; filename=\"BoxCert.pem\"\r\n" >> $TMP
printf "Content-Type: application/octet-stream\r\n\r\n" >> $TMP
cat $CERTPATH/privkey.pem >> $TMP
cat $CERTPATH/fullchain.pem >> $TMP
printf "\r\n" >> $TMP
printf -- "--$BOUNDARY--" >> $TMP

# upload the certificate to the box
$WGET -O - $HOST/cgi-bin/firmwarecfg --header="Content-type: multipart/form-data boundary=$BOUNDARY" --post-file $TMP | grep SSL

# clean up
rm -f $TMP
