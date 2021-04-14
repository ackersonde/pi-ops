#!/bin/bash
DOMAIN=ackerson.de
IPV4_RECORD_ID=23738257
IPV6_RECORD_ID=23738236

# Environment sane?
CREDS_FILE=~/.ssh/do_token
if [ -s "$CREDS_FILE" ]; then
    source $CREDS_FILE
else
    echo "$DO_TOKEN required in $CREDS_FILE. Cowardly refusing to act..."
    exit
fi
if [ ! -f "/usr/bin/jq" ]; then
    echo "jq required to parse data from DNS API. Please install..."
    exit
fi

CURRENT_TIMESTAMP="$(date +%F) $(date +%T) -"

# IPv6
ipv6_current=`curl --silent https://ipv6.icanhazip.com/ | xargs echo -n`
ipv6_dns=`curl --silent -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $DO_TOKEN" \
"https://api.digitalocean.com/v2/domains/$DOMAIN/records/$IPV6_RECORD_ID" | jq -r '.[] | .data'`

if [ "$ipv6_current" != "$ipv6_dns" ]; then
    echo -e "\n$CURRENT_TIMESTAMP IPv6 would update from $ipv6_dns TO $ipv6_current"
#    curl --silent -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $DO_TOKEN" \
#    -d "{\"data\":\"$ipv6_current\"}" "https://api.digitalocean.com/v2/domains/$DOMAIN/records/$IPV6_RECORD_ID"
fi

# IPv4
ipv4_current=`curl --silent https://ipv4.icanhazip.com/ | xargs echo -n`
ipv4_dns=`curl --silent -X GET -H "Content-Type: application/json" -H "Authorization: Bearer $DO_TOKEN" \
"https://api.digitalocean.com/v2/domains/$DOMAIN/records/$IPV4_RECORD_ID" | jq -r '.[] | .data'`
if [ "$ipv4_current" != "$ipv4_dns" ]; then
    echo -e "\n$CURRENT_TIMESTAMP IPv4 would update from $ipv4_dns TO $ipv4_current"
#    curl --silent -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $DO_TOKEN" \
#    -d "{\"data\":\"$ipv4_current\"}" "https://api.digitalocean.com/v2/domains/$DOMAIN/records/$IPV4_RECORD_ID"
fi
