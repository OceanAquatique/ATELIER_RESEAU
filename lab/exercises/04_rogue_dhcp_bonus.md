# Exercice 4 (Bonus) — Détection d'un serveur DHCP malveillant

**Durée estimée :** 1 h 30
**Niveau :** M2 — recherche et expérimentation
**Objectif :** simuler l'attaque dite **« rogue DHCP »** (un faux serveur
DHCP injecté sur le LAN qui sert une passerelle malveillante), observer la
**course aux Offers**, et écrire un script de détection côté défense.

> ⚠️ Cet exercice se déroule **uniquement dans le lab Docker**. N'exécutez
> jamais d'attaque DHCP sur un réseau dont vous n'avez pas l'autorisation
> écrite.

## Partie A — Mise en place de l'attaquant

Ajoutez un second serveur DHCP dans le LAN. Créez `lab/rogue/Dockerfile`&nbsp;:

```dockerfile
FROM alpine:3.20
RUN apk add --no-cache dnsmasq iproute2 tcpdump
COPY dnsmasq.conf /etc/dnsmasq.conf
CMD ["dnsmasq", "--keep-in-foreground", "--log-dhcp", \
     "--log-facility=-", "--conf-file=/etc/dnsmasq.conf"]
```

Et `lab/rogue/dnsmasq.conf`&nbsp;:

```
port=0
interface=eth0
bind-interfaces
dhcp-range=172.20.1.150,172.20.1.160,1h
# Passerelle MALVEILLANTE : l'attaquant
dhcp-option=option:router,172.20.1.99
dhcp-option=option:dns-server,172.20.1.99
```

Ajoutez le service à `docker-compose.yml`&nbsp;:

```yaml
  rogue-dhcp:
    build: ./rogue
    container_name: lab_rogue_dhcp
    hostname: rogue-dhcp
    cap_add: [NET_ADMIN, NET_BIND_SERVICE]
    networks:
      lan:
        ipv4_address: 172.20.1.99
```

Build et lancez&nbsp;: `docker compose up -d --build rogue-dhcp`.

## Partie B — La course aux Offers

Renouvelez plusieurs baux d'affilée depuis le client&nbsp;:

```bash
for i in 1 2 3 4 5; do
  docker exec lab_client bash -c "dhclient -r eth0 2>/dev/null; dhclient -v eth0 2>&1 | grep -E 'DHCPOFFER|bound to'"
  sleep 1
done
```

### À rendre

1. Combien d'**Offers** voyez-vous pour chaque Discover&nbsp;? De **quels
   serveurs** proviennent-elles (IP)&nbsp;?
2. Quel critère détermine **quelle Offer le client accepte**&nbsp;?
   (Indice&nbsp;: lisez la RFC 2131 §3.1.3 ou observez empiriquement plusieurs
   répétitions.)
3. Lorsque le rogue gagne, quelle est la **passerelle** assignée au
   client&nbsp;? Quelles conséquences concrètes pour le trafic
   sortant&nbsp;?

## Partie C — Outils de défense

Écrivez un script `detect_rogue_dhcp.sh` côté `dhcp-server` (le légitime)
qui&nbsp;:

1. Sniffe les Offers DHCP sur `eth0` (`tcpdump -nn 'udp and port 67'` ou
   via `scapy`).
2. Pour chaque Offer, extrait l'**IP du serveur émetteur**
   (champ `siaddr` ou option 54 `server-identifier`).
3. Compare à une **liste blanche** (`172.20.1.2` uniquement).
4. Émet une alerte sur stderr si une IP non autorisée est détectée.

Livrez le script et **une capture de console** montrant qu'il détecte
bien le rogue.

## Partie D — Contre-mesures réseau

En 5-10 phrases, comparez les trois contre-mesures suivantes en termes
de **niveau OSI, efficacité, déployabilité**&nbsp;:

1. **DHCP Snooping** (switchs L2 managés)
2. **802.1X + authentification du serveur**
3. **Détection passive** (l'approche de votre script en partie C)

Indiquez laquelle vous recommanderiez pour&nbsp;:
- un campus universitaire avec ~1000 postes,
- un datacenter cloud privé,
- un réseau Wi-Fi invité dans un café.

## Nettoyage

```bash
docker compose stop rogue-dhcp && docker compose rm -f rogue-dhcp
```
