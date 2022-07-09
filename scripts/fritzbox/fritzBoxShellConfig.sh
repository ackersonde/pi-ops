#!/bin/bash

#******************************************************#
#*********************** CONFIG ***********************#
#******************************************************#

# Fritz!Box Config
[[ -z "$BoxIP" ]] && BoxIP="{{FRITZ_BOX_HOST}}"
[[ -z "$BoxUSER" ]] && BoxUSER="{{FRITZ_BOX_USER}}"
[[ -z "$BoxPW" ]] && BoxPW="{{FRITZ_BOX_PASS}}"

# Fritz!Repeater Config
[[ -z "$RepeaterIP" ]] && RepeaterIP="fritz.repeater"
[[ -z "$RepeaterUSER" ]] && RepeaterUSER="" #Usually on Fritz!Repeater no User is existing. Can be left empty.
[[ -z "$RepeaterPW" ]] && RepeaterPW="YourPassword"
