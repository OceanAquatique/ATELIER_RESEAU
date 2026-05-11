# Lab Réseau — Mini-infrastructure conteneurisée

Ce lab fournit un **vrai réseau** isolé constitué de 4 conteneurs Docker, sur
lequel les étudiant·e·s manipulent **DHCP**, **NAT/PAT** et observent les
couches OSI à travers des **captures de paquets réelles** (tcpdump / tshark).

## Topologie

```
                  ┌──────────────────┐
                  │   internet       │  172.20.0.10
                  │   (nginx)        │
                  └────────┬─────────┘
                           │  wan : 172.20.0.0/24
                  ┌────────┴─────────┐
                  │   nat-router     │  .254 (wan) / .254 (lan)
                  │  iptables NAT    │  MASQUERADE → wan
                  └────────┬─────────┘
                           │  lan : 172.20.1.0/24
        ┌──────────────────┼───────────────────┐
        │                                      │
┌───────┴────────┐                    ┌────────┴─────────┐
│  dhcp-server   │  172.20.1.2        │      client      │  172.20.1.50
│  (dnsmasq)     │                    │ (dhclient/tcpdump│
└────────────────┘                    │  curl/tshark)    │
                                      └──────────────────┘
```

| Conteneur     | Rôle                                                  | Outils principaux |
| ------------- | ----------------------------------------------------- | ----------------- |
| `internet`    | Site public simulé, journalise l'IP source perçue     | nginx             |
| `nat-router`  | Passerelle, fait du PAT vers le WAN                   | iptables, conntrack, tcpdump |
| `dhcp-server` | Distribue les baux DHCP sur le LAN                    | dnsmasq, tcpdump  |
| `client`      | Poste utilisateur côté LAN                            | dhclient, tcpdump, tshark, curl, dig, traceroute |

## Pré-requis hôte (une seule fois)

Le kernel Linux fait passer les trames bridge par les chaînes `iptables` du
host (`br_netfilter`). En politique `FORWARD DROP` par défaut, cela bloque la
traversée NAT entre nos deux bridges. On désactive ce hook pour le lab&nbsp;:

```bash
sudo ./host-setup.sh
```

> Modification **non persistante** : à relancer après un redémarrage de
> l'hôte. Pour restaurer : `sudo sysctl -w net.bridge.bridge-nf-call-iptables=1`.

## Démarrage

```bash
cd lab
sudo ./host-setup.sh        # pré-requis hôte (une fois par boot)
docker compose build        # ~2-3 min la première fois
docker compose up -d
docker compose ps           # vérifier que les 4 services sont Up
```

Pour ouvrir une session interactive sur un conteneur&nbsp;:

```bash
docker exec -it lab_client bash         # poste utilisateur (Debian)
docker exec -it lab_nat_router sh       # routeur (Alpine)
docker exec -it lab_dhcp_server sh      # serveur DHCP (Alpine)
```

Pour observer les journaux DHCP en direct&nbsp;:

```bash
docker logs -f lab_dhcp_server
```

## Exercices

| #  | Fichier                                              | Sujet                                          |
| -- | ---------------------------------------------------- | ---------------------------------------------- |
| 1  | [exercises/01_osi_capture.md](exercises/01_osi_capture.md)         | OSI — capture HTTP et identification des couches |
| 2  | [exercises/02_dhcp_dora.md](exercises/02_dhcp_dora.md)             | DHCP — observer DORA paquet par paquet         |
| 3  | [exercises/03_nat_pat.md](exercises/03_nat_pat.md)                 | NAT/PAT — table conntrack et règles iptables   |
| 4  | [exercises/04_rogue_dhcp_bonus.md](exercises/04_rogue_dhcp_bonus.md) | **Bonus** — détection de serveur DHCP malveillant |

## Nettoyage

```bash
docker compose down              # arrête les conteneurs, garde les images
docker compose down --rmi all    # supprime aussi les images du lab
```
