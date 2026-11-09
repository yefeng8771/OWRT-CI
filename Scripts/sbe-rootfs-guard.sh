#!/bin/sh
# The generated eMMC rootfs payload, including image padding, must fit 122 MiB.
set -eu
[ "$#" -eq 1 ] && [ -f "$1" ] || { echo 'Missing rootfs image' >&2; exit 1; }
size=$(stat -c %s -- "$1")
limit=$((122 * 1024 * 1024))
if [ "$size" -gt "$limit" ]; then
    echo "ERROR: SBE1V1K padded rootfs $size bytes exceeds $limit bytes (122 MiB)" >&2
    exit 1
fi
printf 'SBE1V1K padded rootfs: %s bytes; remaining: %s bytes of 122 MiB\n' "$size" "$((limit-size))"
