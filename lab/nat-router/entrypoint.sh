#!/bin/sh
set -eu

# Detect WAN/LAN interfaces dynamically (Docker assigns ethN unpredictably)
WAN_IF=$(ip -o -4 addr show | awk '$4 ~ /^172\.20\.0\./ {print $2; exit}')
LAN_IF=$(ip -o -4 addr show | awk '$4 ~ /^172\.20\.1\./ {print $2; exit}')

echo "============================================================"
echo " NAT router starting"
echo "   WAN interface : ${WAN_IF}   (172.20.0.254)"
echo "   LAN interface : ${LAN_IF}   (172.20.1.254)"
echo "============================================================"

# IP forwarding is enabled by docker-compose sysctls; assert it.
echo "ip_forward = $(cat /proc/sys/net/ipv4/ip_forward)"

# Reset chains
iptables -F
iptables -t nat -F
iptables -t mangle -F

# PAT / NAT overload toward the WAN side
iptables -t nat -A POSTROUTING -o "${WAN_IF}" -j MASQUERADE

# Permissive forwarding for the lab (NOT for production)
iptables -P FORWARD ACCEPT

echo
echo "Active NAT rules:"
iptables -t nat -L -n -v --line-numbers
echo
echo "Router is up. Keeping container alive."
echo "Tip: 'docker exec -it lab_nat_router conntrack -L' shows the NAT translation table."
exec tail -f /dev/null
