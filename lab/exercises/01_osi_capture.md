# Exercice 1 — OSI à travers une vraie capture de paquets

**Durée estimée :** 45 min
**Objectif :** relier chaque couche du modèle OSI à un champ concret observable
dans une capture réseau effectuée sur le lab.

## Préparation

Configurez le client (s'il ne l'a pas déjà été par DHCP — voir exercice 2)&nbsp;:

```bash
docker exec lab_client bash -c "ip route del default 2>/dev/null; ip route add default via 172.20.1.254"
```

Vérifiez l'accès au site « public »&nbsp;:

```bash
docker exec lab_client curl -s http://172.20.0.10/whoami
```

## Manipulation

Dans un terminal, lancez la capture côté client&nbsp;:

```bash
docker exec lab_client tcpdump -i eth0 -w /tmp/http.pcap -nn host 172.20.0.10
```

Dans un second terminal, déclenchez du trafic&nbsp;:

```bash
docker exec lab_client curl -v http://172.20.0.10/
docker exec lab_client curl -v http://172.20.0.10/whoami
```

Arrêtez la capture (Ctrl+C), puis analysez-la&nbsp;:

```bash
docker exec lab_client tshark -r /tmp/http.pcap -V | less
```

> `-V` produit la décomposition complète couche par couche (Frame → Ethernet
> → IP → TCP → HTTP).

## À rendre dans le README de votre fork

Pour **chaque couche OSI**, donnez **un exemple concret extrait de votre
capture** (champ, valeur observée). Justifiez en 1-2 phrases.

| Couche OSI         | Élément observé dans la capture | Valeur exemple |
| ------------------ | ------------------------------- | -------------- |
| 7 — Application    | _ex. méthode HTTP_              | `GET /whoami HTTP/1.1` |
| 6 — Présentation   | _ex. encodage / Content-Type_   | …              |
| 5 — Session        | _ex. Keep-Alive, cookies_       | …              |
| 4 — Transport      | _ex. port TCP, flags_           | …              |
| 3 — Réseau         | _ex. IP source / destination_   | …              |
| 2 — Liaison        | _ex. adresses MAC_              | …              |
| 1 — Physique       | _non visible — pourquoi&nbsp;?_ | …              |

## Questions de réflexion (à répondre dans le fork)

1. Pourquoi l'**adresse MAC source** observée n'est-elle **pas** celle du
   serveur `internet` mais celle du `nat-router`&nbsp;? Que vous apprend
   cette observation sur la portée de chaque couche&nbsp;?
2. Lancez `curl -v https://...` vers un site HTTPS public (depuis l'hôte,
   pas le lab). Quelle couche change visiblement par rapport au HTTP du
   lab&nbsp;? Quelles couches **disparaissent** de votre visibilité&nbsp;?
3. La couche 5 (Session) est très peu visible dans une capture HTTP/1.1.
   Donnez **deux mécanismes applicatifs** qui jouent le rôle de la
   couche session, et expliquez pourquoi ils sont implémentés
   « plus haut »&nbsp;dans la pile.
