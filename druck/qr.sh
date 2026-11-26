#!/bin/sh
# Erzeugt den QR-Code für das Flugblatt.
# Aufruf: ./qr.sh https://deine-adresse.example
set -e
[ -n "$1" ] || { echo "Aufruf: $0 <URL>" >&2; exit 1; }
cd "$(dirname "$0")"
qrencode -t SVG -l M -m 0 -o qr.svg "$1"
printf '%s\n' "$1" > url.txt
echo "qr.svg erzeugt für: $1"
