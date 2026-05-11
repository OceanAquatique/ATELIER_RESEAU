#!/usr/bin/env bash
# Host prerequisite for the network lab.
#
# Why: Docker bridges enable br_netfilter, which routes bridge frames through
# the host's iptables FORWARD chain. The default DROP policy then prevents
# our nat-router container from forwarding traffic between the lan and wan
# bridges. Disabling bridge-nf for IPv4 keeps frames at L2 and lets the
# in-container netfilter handle routing/NAT — which is exactly what we
# want students to observe.
#
# Run once before `docker compose up`. The change is non-persistent
# (reverts on reboot); re-run if needed.
#
# Requires: sudo
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    exec sudo -E "$0" "$@"
fi

echo "[host-setup] Disabling br_netfilter IPv4 hook (was: $(sysctl -n net.bridge.bridge-nf-call-iptables 2>/dev/null || echo 'n/a'))"
sysctl -w net.bridge.bridge-nf-call-iptables=0 > /dev/null

echo "[host-setup] Done. The lab should now be able to route via nat-router."
echo "[host-setup] Tip: 'sudo sysctl -w net.bridge.bridge-nf-call-iptables=1' to restore."
