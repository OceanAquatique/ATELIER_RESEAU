FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        iproute2 \
        iputils-ping \
        tcpdump \
        isc-dhcp-client \
        curl \
        dnsutils \
        traceroute \
        netcat-openbsd \
        tshark \
        less \
        nano \
    && rm -rf /var/lib/apt/lists/*
