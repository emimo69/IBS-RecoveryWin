# shellcheck shell=bash
# Shared, read-only eligibility rules. No device operations on source.
ibs_disk_metadata_allowed() {
    local name=$1 type=$2 bytes=$3 transport=$4 removable=$5 readonly=$6
    [[ "$name" =~ ^/dev/(sd[a-z]+|hd[a-z]+|nvme[0-9]+n[0-9]+|mmcblk[0-9]+)$ ]] || return 1
    [[ "$type" == disk && "$bytes" =~ ^[0-9]+$ ]] || return 1
    (( bytes > 0 )) || return 1
    [[ "$transport" != usb && "$removable" == 0 && "$readonly" == 0 ]]
}
