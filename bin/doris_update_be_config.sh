#!/bin/bash

set -eu
set -o pipefail

if [ "$#" -ne 5 ]; then
  echo "Usage: $0 FE_HOST FE_PORT KEY VALUE PERSIST"
  exit 1
fi

fe_host="$1"
fe_port="$2"
key="$3"
value="$4"

be_hosts=(`mycli -uroot -h$fe_host -P$fe_port -e "show backends\G" | grep Host | awk '{print $3}'`)

for be_host in "${be_hosts[@]}"; do
  set -x
  curl -X POST "http://${be_host}:8040/api/update_config?${key}=${value}&persist=$5"
  set +x
done
