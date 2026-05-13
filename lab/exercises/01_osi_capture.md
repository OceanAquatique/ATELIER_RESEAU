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

**Étape 1 — supprimez une éventuelle capture précédente** (sinon échec en
*Permission denied* car tcpdump abandonne ses privilèges vers l'utilisateur
`tcpdump` après ouverture du fichier) :

```bash
docker exec lab_client rm -f /tmp/http.pcap
```

**Étape 2 — lancez la capture côté client.** Les flags importants&nbsp;:
`-U` (écriture non bufferisée, indispensable si la capture est interrompue),
`-c 30` (s'arrête automatiquement après 30 paquets, ≈ 2 à 3 requêtes HTTP) :

```bash
docker exec lab_client tcpdump -i eth0 -U -w /tmp/http.pcap -nn -c 30 host 172.20.0.10
```

> ⚠️ Cette commande **bloque** le terminal tant que les 30 paquets ne sont
> pas capturés. Ouvrez un **second terminal** pour l'étape 3.

**Étape 3 — dans un second terminal, déclenchez du trafic** *pendant* que
tcpdump tourne&nbsp;:

```bash
docker exec lab_client curl -v http://172.20.0.10/
docker exec lab_client curl -v http://172.20.0.10/whoami
docker exec lab_client curl -s http://172.20.0.10/        # complément pour atteindre 30 paquets
```

tcpdump s'arrête seul dès le 30e paquet et affiche un résumé du type
`30 packets captured / 0 packets dropped by kernel`.

**Étape 4 — vérifiez que la capture est exploitable** :

```bash
docker exec lab_client capinfos /tmp/http.pcap
```

`Number of packets` doit être > 0. Si la capture est vide, voir la section
*Pièges fréquents* en bas de cet énoncé.

**Étape 5 — analysez la capture**. Trois vues utiles&nbsp;:

```bash
# Vue compacte : une ligne par paquet (utile pour repérer les n° de frames)
docker exec lab_client tshark -r /tmp/http.pcap

# Vue détaillée d'un paquet précis (ex. la requête GET = frame n°4)
docker exec lab_client tshark -r /tmp/http.pcap -V -Y 'frame.number == 4'

# Vue détaillée complète (pager : utilisez 'q' pour quitter)
docker exec -it lab_client sh -c "tshark -r /tmp/http.pcap -V | less"
```

> `-V` produit la décomposition complète couche par couche
> (Frame → Ethernet → IP → TCP → HTTP). Le filtre `-Y` cible un paquet
> par son numéro pour éviter d'avoir à scroller dans toute la trace.

## Visualisation assistée : `osi_inspect.py`

La sortie brute de `tshark -V` est dense (plusieurs centaines de lignes par
paquet). Un script Python est fourni dans ce dossier pour vous présenter,
pour chaque trame, un **tableau structuré par couche OSI** avec en plus
une **colonne d'explication pédagogique** pour chaque champ.

### Lister les trames

Depuis la racine du dépôt (l'hôte, pas l'intérieur du conteneur) :

```bash
./lab/exercises/osi_inspect.py
```

Vous obtenez la même vue compacte que `tshark` mais sans avoir à taper la
commande complète. Repérez la trame qui vous intéresse — typiquement la
trame portant `GET /` (ligne marquée `HTTP 141 GET / HTTP/1.1`).

### Détailler une trame

```bash
./lab/exercises/osi_inspect.py 4         # trame n°4 — la requête HTTP
./lab/exercises/osi_inspect.py 1         # trame n°1 — le SYN du handshake
./lab/exercises/osi_inspect.py 8         # trame n°8 — la réponse 200 OK
```

Le script affiche, pour chaque couche OSI **présente** dans la trame, les
champs clés avec **3 informations** :

| Colonne       | Contenu                                       |
| ------------- | --------------------------------------------- |
| `Champ`       | Nom du champ tel qu'extrait par tshark        |
| `Valeur`      | Valeur réelle observée dans **votre** capture |
| `Explication` | À quoi sert ce champ, comment l'interpréter   |

C'est exactement la matière dont vous avez besoin pour remplir le tableau
*« Couche / Élément observé / Valeur exemple »* demandé dans la section
suivante.

### Réutilisation pour les exercices suivants

Le script est générique. Pour disséquer une capture DHCP (exercice 2) ou
NAT (exercice 3), pointez-le vers le bon conteneur et le bon fichier :

```bash
./lab/exercises/osi_inspect.py 1 --pcap /tmp/dhcp.pcap --container lab_dhcp_server
./lab/exercises/osi_inspect.py 3 --pcap /tmp/nat.pcap  --container lab_nat_router
```

### Travail demandé avec ce script

1. Lancez `./lab/exercises/osi_inspect.py` pour obtenir la liste des trames.
2. Identifiez **une trame contenant du HTTP** (typiquement la requête `GET /`)
   et **une trame de contrôle TCP** (SYN, ACK seul, ou FIN).
3. Lancez le script avec le n° de chaque trame et **copiez la sortie**
   dans le README de votre fork (bloc de code).
4. Pour chacune des deux trames, **comptez et nommez** les couches OSI
   visibles (utilisez la ligne `Pile présente : …` en en-tête). Expliquez
   en 1 phrase pourquoi la couche 7 est absente sur la trame de contrôle TCP.

> 💬 **Votre réponse (sorties du script + analyse) :**


```====================================================================================================================================
@OceanAquatique ➜ /workspaces/ATELIER_RESEAU (main) $ ./lab/exercises/osi_inspect.py 4
  Trame 4  |  141 octets  |  May 13, 2026 10:07:46.607592000 UTC
  Pile présente : eth > ip > tcp > http
====================================================================================================================================
  OSI   | Protocole                | Champ              = Valeur                 | Explication
------------------------------------------------------------------------------------------------------------------------------------
  L2    | Liaison — Ethernet       |
        |                          |   MAC source         = 16:ad:53:90:7c:bb      | Carte réseau émettrice sur le segment local
        |                          |   MAC destination    = 16:34:3a:cd:f9:ff      | Récepteur sur le LAN = prochain saut (souvent le routeur, pas la dest. finale)
        |                          |   EtherType          = 0x0800                 | Protocole L3 encapsulé : 0x0800=IPv4, 0x86DD=IPv6, 0x0806=ARP
------------------------------------------------------------------------------------------------------------------------------------
  L3    | Réseau — IPv4            |
        |                          |   IP source          = 172.20.1.50            | Adresse logique de l'émetteur (couche 3)
        |                          |   IP destination     = 172.20.0.10            | Destinataire final — peut traverser plusieurs routeurs
        |                          |   TTL                = 64                     | Time To Live, décrémenté à chaque saut. Évite les boucles infinies
        |                          |   Protocole encapsulé = 6                      | Indique ce qu'IP transporte : 6=TCP, 17=UDP, 1=ICMP
        |                          |   Longueur totale    = 127                    | Taille en octets de l'en-tête IP + payload
------------------------------------------------------------------------------------------------------------------------------------
  L4    | Transport — TCP          |
        |                          |   Port source        = 55986                  | Port éphémère choisi par le client (généralement > 1024)
        |                          |   Port destination   = 80                     | Port du service : 80=HTTP, 443=HTTPS, 22=SSH, 25=SMTP...
        |                          |   Flags              = ·······AP···           | Bits de contrôle : S=SYN, A=ACK, F=FIN, R=RST, P=PUSH
        |                          |   Numéro de séquence = 1                      | Position du 1er octet de payload dans le flux TCP
        |                          |   Numéro d'ACK       = 1                      | Prochain octet attendu en retour (cumulatif)
        |                          |   Fenêtre            = 64256                  | Octets que je peux encore recevoir sans ACK (contrôle de flux)
------------------------------------------------------------------------------------------------------------------------------------
  L7    | Application — HTTP       |
        |                          |   Méthode            = GET                    | Verbe HTTP : GET (lire), POST (envoyer), PUT, DELETE...
        |                          |   URI                = /                      | Chemin de la ressource demandée côté serveur
        |                          |   Version            = HTTP/1.1               | Version du protocole HTTP utilisée
        |                          |   Host               = 172.20.0.10            | Hôte ciblé — permet le virtual hosting (plusieurs sites par IP)
        |                          |   User-Agent         = curl/7.88.1            | Identifiant logiciel du client (navigateur, curl, bot...)
------------------------------------------------------------------------------------------------------------------------------------
@OceanAquatique ➜ /workspaces/ATELIER_RESEAU (main) $ ./lab/exercises/osi_inspect.py 1

====================================================================================================================================
  Trame 1  |  74 octets  |  May 13, 2026 10:07:46.607447000 UTC
  Pile présente : eth > ip > tcp
====================================================================================================================================
  OSI   | Protocole                | Champ              = Valeur                 | Explication
------------------------------------------------------------------------------------------------------------------------------------
  L2    | Liaison — Ethernet       |
        |                          |   MAC source         = 16:ad:53:90:7c:bb      | Carte réseau émettrice sur le segment local
        |                          |   MAC destination    = 16:34:3a:cd:f9:ff      | Récepteur sur le LAN = prochain saut (souvent le routeur, pas la dest. finale)
        |                          |   EtherType          = 0x0800                 | Protocole L3 encapsulé : 0x0800=IPv4, 0x86DD=IPv6, 0x0806=ARP
------------------------------------------------------------------------------------------------------------------------------------
  L3    | Réseau — IPv4            |
        |                          |   IP source          = 172.20.1.50            | Adresse logique de l'émetteur (couche 3)
        |                          |   IP destination     = 172.20.0.10            | Destinataire final — peut traverser plusieurs routeurs
        |                          |   TTL                = 64                     | Time To Live, décrémenté à chaque saut. Évite les boucles infinies
        |                          |   Protocole encapsulé = 6                      | Indique ce qu'IP transporte : 6=TCP, 17=UDP, 1=ICMP
        |                          |   Longueur totale    = 60                     | Taille en octets de l'en-tête IP + payload
------------------------------------------------------------------------------------------------------------------------------------
  L4    | Transport — TCP          |
        |                          |   Port source        = 55986                  | Port éphémère choisi par le client (généralement > 1024)
        |                          |   Port destination   = 80                     | Port du service : 80=HTTP, 443=HTTPS, 22=SSH, 25=SMTP...
        |                          |   Flags              = ··········S·           | Bits de contrôle : S=SYN, A=ACK, F=FIN, R=RST, P=PUSH
        |                          |   Numéro de séquence = 0                      | Position du 1er octet de payload dans le flux TCP
        |                          |   Numéro d'ACK       = 0                      | Prochain octet attendu en retour (cumulatif)
        |                          |   Fenêtre            = 64240                  | Octets que je peux encore recevoir sans ACK (contrôle de flux)
------------------------------------------------------------------------------------------------------------------------------------
### Analyse des trames sélectionnées

J’ai sélectionné deux trames représentatives de la capture :

- la trame n°4, qui contient une requête HTTP `GET / HTTP/1.1` ;
- la trame n°1, qui correspond à un paquet TCP de contrôle `SYN`.

Pour la trame n°4, la pile présente est : `eth > ip > tcp > http`.

On observe donc 4 couches OSI visibles :

- couche 2 — Liaison de données : Ethernet ;
- couche 3 — Réseau : IPv4 ;
- couche 4 — Transport : TCP ;
- couche 7 — Application : HTTP.

Cette trame transporte une donnée applicative, car elle contient une requête HTTP envoyée par le client vers le serveur.

Pour la trame n°1, la pile présente est : `eth > ip > tcp`.

On observe donc 3 couches OSI visibles :

- couche 2 — Liaison de données : Ethernet ;
- couche 3 — Réseau : IPv4 ;
- couche 4 — Transport : TCP.

La couche 7 est absente sur cette trame de contrôle TCP, car le paquet `SYN` sert uniquement à initier la connexion TCP et ne transporte pas encore de donnée applicative comme une requête HTTP 
```

## À rendre — répondez directement dans ce fichier

Pour **chaque couche OSI**, donnez **un exemple concret extrait de votre
capture** (champ, valeur observée). Justifiez en 1-2 phrases.

| Couche OSI         | Élément observé dans la capture | Valeur exemple |
| ------------------ | ------------------------------- | -------------- |
| 7 — Application    | Méthode HTTP  | `GET / HTTP/1.1` |
| 6 — Présentation   | Type de contenu HTTP | `Content-Type: text/html` |
| 5 — Session        | Maintien de connexion HTTP  | `Connection: keep-alive` |
| 4 — Transport      | Port TCP source et destination  | `55986 → 80, flag SYN ou ACK` |
| 3 — Réseau         | IP source et destination | `172.20.1.50 → 172.20.0.10` |
| 2 — Liaison        | Adresses MAC Ethernet |  `16:ad:53:90:7c:bb → 16:34:3a:cd:f9:ff` |
| 1 — Physique       | Non visible dans une capture pcap classique | `La capture montre des trames numériques, pas le signal électrique/physique` |

## Questions de réflexion

**Question 1.** Pourquoi l'**adresse MAC source** observée n'est-elle
**pas** celle du serveur `internet` mais celle du `nat-router`&nbsp;? Que
vous apprend cette observation sur la portée de chaque couche&nbsp;?

> 💬 **Votre réponse :**
```
L’adresse MAC observée n’est pas celle du serveur `internet`, car une adresse MAC n’a de portée que sur le réseau local immédiat. Le serveur `internet` est situé derrière un routeur : lorsque le paquet revient vers le client, le `nat-router` recrée une nouvelle trame Ethernet sur le LAN, avec sa propre adresse MAC comme adresse source.

Cette observation montre que la couche 2, liaison de données, fonctionne uniquement saut par saut, entre deux équipements voisins. À l’inverse, la couche 3, réseau, permet d’identifier une communication IP entre deux machines situées sur des réseaux différents.
```
**Question 2.** Vous capturez sur `eth0` du client (côté LAN). Dans votre
trace, l'**IP source** sortante est `172.20.1.50`. Pourtant, `curl /whoami`
rapporte que le serveur perçoit `172.20.0.254`. Expliquez cette différence
et indiquez **où** il faudrait capturer pour voir l'IP réécrite.
*Astuce&nbsp;:* `docker exec lab_nat_router tcpdump -i any -nn -c 10 host 172.20.0.10`.

> 💬 **Votre réponse :**
```
La capture est faite sur `eth0` du client, donc avant le passage par le routeur NAT. À cet endroit, le paquet sort encore avec l’adresse IP source réelle du client : `172.20.1.50`.

Ensuite, lorsque le paquet traverse le `nat-router`, celui-ci applique une traduction d’adresse. Il remplace l’adresse IP source du client par son adresse côté WAN : `172.20.0.254`. C’est pour cela que le serveur `internet`, via `/whoami`, indique qu’il perçoit la source comme `172.20.0.254`.

Pour voir l’adresse IP réécrite, il faudrait capturer sur le `nat-router`, côté sortie vers le réseau WAN, par exemple avec une capture sur le conteneur `lab_nat_router`.
```

**Question 3.** Lancez `curl -v https://...` vers un site HTTPS public
(depuis l'hôte, pas le lab). Quelle couche change visiblement par
rapport au HTTP du lab&nbsp;? Quelles couches **disparaissent** de votre
visibilité&nbsp;?

> 💬 **Votre réponse :**
```
Avec HTTPS, la couche application n’est plus visible en clair comme dans le HTTP du lab. Dans la capture HTTP, on pouvait lire directement la méthode `GET`, l’URI `/`, les en-têtes HTTP et la réponse du serveur. En HTTPS, ces éléments sont protégés par TLS.

La couche qui change visiblement est donc la couche liée à la sécurisation et au chiffrement des échanges : on observe une négociation TLS avant les données applicatives. Les couches basses restent visibles, notamment Ethernet, IP et TCP, car elles sont nécessaires pour transporter le flux réseau.

En revanche, le contenu applicatif HTTP disparaît de la visibilité directe : on ne peut plus lire clairement la méthode HTTP, le chemin demandé, les en-têtes complets ou le corps de la réponse. On voit le transport chiffré, mais pas le contenu applicatif en clair.
```

**Question 4.** La couche 5 (Session) est très peu visible dans une
capture HTTP/1.1. Donnez **deux mécanismes applicatifs** qui jouent le
rôle de la couche session, et expliquez pourquoi ils sont implémentés
« plus haut »&nbsp;dans la pile.

> 💬 **Votre réponse :**
```
Deux mécanismes applicatifs qui jouent un rôle proche de la couche session sont les cookies de session et les jetons d’authentification, comme les tokens ou les identifiants de session.

Les cookies permettent à une application web de reconnaître un utilisateur entre plusieurs requêtes HTTP. Les tokens d’authentification permettent aussi de maintenir un état logique entre le client et le serveur, par exemple pour savoir qu’un utilisateur est connecté.

Ces mécanismes sont implémentés plus haut dans la pile, au niveau applicatif, car HTTP est un protocole essentiellement sans état. Ce sont donc les applications web qui doivent gérer la continuité de session, l’identité utilisateur, l’authentification et le contexte métier.
```

## Pièges fréquents

* **Capture vide (`Number of packets: 0`)** — vous avez lancé `curl` *avant*
  tcpdump, ou tcpdump a été tué avant d'écrire son buffer. Solution : utilisez
  bien `-U -c 30` (étape 2) et déclenchez le trafic *après* le message
  `listening on eth0…`.
* **`tcpdump: /tmp/http.pcap: Permission denied`** — un fichier appartenant à
  l'utilisateur `tcpdump` (créé par une capture précédente) bloque
  l'écriture. Solution : `docker exec lab_client rm -f /tmp/http.pcap`.
* **`tshark … | less` n'affiche rien** — vous êtes dans un environnement
  sans TTY (script, pipeline). Retirez `| less` ou utilisez
  `docker exec -it lab_client sh -c "… | less"`.
