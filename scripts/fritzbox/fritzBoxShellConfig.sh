#!/bin/bash

#******************************************************#
#*********************** CONFIG ***********************#
#******************************************************#

# Fritz!Box Config
[[ -z "$BoxIP" ]] && BoxIP="{{CTX_FRITZ_BOX_HOST}}"
[[ -z "$BoxUSER" ]] && BoxUSER="{{CTX_FRITZ_BOX_USER}}"
[[ -z "$BoxPW" ]] && BoxPW="{{CTX_FRITZ_BOX_PASS}}"

# Fritz!Repeater Config
[[ -z "$RepeaterIP" ]] && RepeaterIP="fritz.repeater"
[[ -z "$RepeaterUSER" ]] && RepeaterUSER="" #Usually on Fritz!Repeater no User is existing. Can be left empty.
[[ -z "$RepeaterPW" ]] && RepeaterPW="YourPassword"
