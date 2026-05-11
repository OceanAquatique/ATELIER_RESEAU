FROM alpine:3.20

RUN apk add --no-cache \
        iptables \
        ip6tables \
        iproute2 \
        tcpdump \
        conntrack-tools \
        bash \
        curl

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
