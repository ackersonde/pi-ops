#!/bin/bash
source ~/.ssh/github_deploy_params

DOMAIN=ackerson.de
PREFIX=`./fritzBoxShell.sh IGDIP STATE | grep NewIPv6Prefix | awk '{print $2}'`

declare -A domains
domains["145482150"]="ubuntu@{{CTX_IPV6_MASTER_HOME}}"
domains["145483151"]="ubuntu@{{CTX_IPV6_SLAVE_HOME}}"
domains["145482932"]="ackersond@{{CTX_IPV6_BUILD_HOME}}"

for IPV6_RECORD_ID in "${!domains[@]}"
do
    local_ip=`ssh ${domains[$IPV6_RECORD_ID]} curl --silent https://ipv6.icanhazip.com/ | xargs echo -n`
    domain=`echo ${domains[$IPV6_RECORD_ID]} | awk -F '@' '{print $2}'`
    dns_look=`dig +short AAAA $domain`

    echo "$domain - iCAN: $local_ip  DIG: $dns_look"

    # first check if local IP matches DNS record
    if [[ "$local_ip" != "$dns_look" ]]; then
        # if not, check if IPv6 prefix has changed
        if [[ ! $local_ip =~ ^"${PREFIX::-1}".* ]]; then
            echo "UPDATE ${domains[$IPV6_RECORD_ID]} to $local_ip !"
            # curl --silent -X PUT -H "Content-Type: application/json" -H "Authorization: Bearer $DO_TOKEN" \
            #    -d "{\"data\":\"$local_ip\"}" "https://api.digitalocean.com/v2/domains/$DOMAIN/records/$IPV6_RECORD_ID"

            # send Slack update msg
            curl -s -o /dev/null -X POST -d token=$SLACK_API_TOKEN -d channel=C092UE0H4 \
             -d text="Please update $domain from $dns_look to $local_ip @ <https://cloud.digitalocean.com/networking/domains/$DOMAIN|DigitalOcean>" \
             https://slack.com/api/chat.postMessage
        fi
    fi
done
