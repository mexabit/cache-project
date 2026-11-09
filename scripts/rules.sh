#!/bin/bash

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
	echo "This script must be run as root. Use 'sudo ./$0'"
	exit 1
fi

nft add table inet cache_project
nft 'add chain inet cache_project input { type filter hook input priority 0; policy accept; }'

nft flush chain inet cache_project input

nft add rule inet cache_project input ip saddr 192.168.97.114 ip daddr 192.168.96.249 tcp dport 8080 accept
nft add rule inet cache_project input ip daddr 192.168.96.249 tcp dport 8080 drop
