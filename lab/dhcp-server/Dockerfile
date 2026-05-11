FROM alpine:3.20

RUN apk add --no-cache dnsmasq iproute2 tcpdump

COPY dnsmasq.conf /etc/dnsmasq.conf

# --log-dhcp prints DORA exchanges to stdout for easy observation
CMD ["dnsmasq", "--keep-in-foreground", "--log-dhcp", \
     "--log-facility=-", "--conf-file=/etc/dnsmasq.conf"]
