# Exercice 2 — DHCP : observer DORA paquet par paquet

**Durée estimée :** 45 min
**Objectif :** capturer un échange DHCP complet (Discover / Offer / Request /
ACK), identifier les options portées par chaque message, et comprendre
pourquoi DHCP utilise un broadcast L2 alors qu'IP n'est pas encore
configuré.

## Manipulation

Côté `dhcp-server`, démarrez une capture filtrée sur les ports DHCP (67/68)&nbsp;:

```bash
docker exec -it lab_dhcp_server tcpdump -i eth0 -nn -e -v port 67 or port 68
```

> Note&nbsp;: `-e` affiche les adresses MAC, indispensables pour comprendre
> le broadcast L2.

Côté `client`, déclenchez une nouvelle demande de bail&nbsp;:

```bash
docker exec lab_client bash -c "dhclient -r eth0 2>/dev/null; dhclient -v eth0"
```

Observez les **4 paquets** DORA dans la capture, puis arrêtez tcpdump (Ctrl+c).

Affichez aussi les journaux applicatifs du serveur&nbsp;:

```bash
docker logs --tail 40 lab_dhcp_server
```

## À rendre — répondez directement dans ce fichier

### 1. Tableau DORA

Complétez en vous appuyant sur **votre propre capture**&nbsp;:

| Étape | Émetteur (IP src) | Destinataire (IP dst) | MAC src / dst | Options DHCP notables |
|---|---|---|---|---|
| 1. Discover | `0.0.0.0` | `255.255.255.255` | `16:ad:53:90:7c:bb → ff:ff:ff:ff:ff:ff` | Option 53 = `Discover`, option 55 = liste des paramètres demandés : masque, passerelle, DNS, domaine, hostname, routes statiques, NTP… |
| 2. Offer | `172.20.1.2` | `172.20.1.142` | `56:98:82:3b:02:cd → 16:ad:53:90:7c:bb` | Option 53 = `Offer`, option 54 = serveur DHCP `172.20.1.2`, option 51 = bail `43200s`, option 1 = masque `255.255.255.0`, option 3 = passerelle `172.20.1.254`, option 6 = DNS `1.1.1.1, 8.8.8.8` |
| 3. Request | `0.0.0.0` | `255.255.255.255` | `16:ad:53:90:7c:bb → ff:ff:ff:ff:ff:ff` | Option 53 = `Request`, option 54 = serveur DHCP choisi `172.20.1.2`, option 50 = IP demandée `172.20.1.142`, option 55 = paramètres demandés |
| 4. ACK | `172.20.1.2` | `172.20.1.142` | `56:98:82:3b:02:cd → 16:ad:53:90:7c:bb` | Option 53 = `ACK`, option 54 = serveur DHCP `172.20.1.2`, option 51 = bail `43200s`, option 58 = T1 `21600s`, option 59 = T2 `37800s`, option 1 = masque, option 3 = passerelle, option 6 = DNS |
### 2. Configuration finale du client


```Dans cette capture, l’identifiant de transaction `xid` est identique dans les quatre paquets : `0xc5b35b3f`. Cela permet d’associer le Discover, l’Offer, le Request et l’ACK au même échange DHCP.```

```bash
docker exec lab_client ip -4 addr show eth0
docker exec lab_client ip route
docker exec lab_client cat /etc/resolv.conf   # peut être vide si non géré par dhclient
```

Notez **l'IP attribuée, le masque, la passerelle, les DNS, la durée de bail**.

> 💬 **Votre réponse :**
>
```D’après la capture et les fichiers de bail, le serveur DHCP a attribué au client l’adresse dynamique suivante :

- Adresse IP DHCP attribuée : `172.20.1.142/24`
- Masque : `255.255.255.0`
- Passerelle : `172.20.1.254`
- DNS : `1.1.1.1` et `8.8.8.8`
- Domaine : `lab.local`
- Durée du bail : `43200` secondes, soit `12 h`
- T1 / renouvellement : `21600` secondes, soit `6 h`
- T2 / rebind : `37800` secondes, soit `10 h 30`
- Serveur DHCP : `172.20.1.2`

On remarque aussi que l’interface `eth0` possède encore une adresse statique `172.20.1.50/24`, configurée par le lab Docker, ainsi qu’une adresse secondaire dynamique `172.20.1.142/24` obtenue par DHCP. L’adresse attribuée par le serveur DHCP est donc bien `172.20.1.142`.
```

### 3. Questions de réflexion

**Question 1.** Pourquoi le client utilise-t-il **`0.0.0.0` comme IP
source** pour le Discover, alors que c'est une adresse non routable&nbsp;?
Que se passerait-il avec n'importe quelle autre adresse&nbsp;?

> 💬 **Votre réponse :**
>
```
Le client utilise `0.0.0.0` comme adresse IP source dans le DHCP Discover parce qu’il n’a pas encore reçu de configuration IP valide. Il ne peut donc pas utiliser une vraie adresse source.

S’il utilisait une adresse arbitraire, celle-ci pourrait être fausse, déjà utilisée par une autre machine, hors du réseau local, ou non autorisée. DHCP utilise donc `0.0.0.0` pour signaler clairement : “je n’ai pas encore d’adresse IP, je cherche un serveur DHCP”.
```

**Question 2.** Pourquoi le **Request** est-il **rediffusé en broadcast**
alors que le client connaît déjà l'IP du serveur après l'Offer&nbsp;?

> 💬 **Votre réponse :**
>
```
Le DHCP Request est rediffusé en broadcast même si le client connaît déjà le serveur DHCP après l’Offer, car cette étape sert aussi à informer tout le réseau du choix effectué par le client.

Dans un réseau où plusieurs serveurs DHCP auraient répondu avec plusieurs Offers, le broadcast permet d’indiquer publiquement quel serveur et quelle adresse IP le client accepte. Les autres serveurs peuvent alors abandonner leur proposition.
```

**Question 3.** À quoi sert le **transaction ID (xid)** présent dans les
4 paquets&nbsp;? Que se passerait-il s'il était omis dans un réseau avec
plusieurs serveurs DHCP&nbsp;?

> 💬 **Votre réponse :**
>
```
Le transaction ID, ou `xid`, sert à identifier un échange DHCP précis. Dans ma capture, les quatre paquets DORA partagent le même `xid` : `0xc5b35b3f`.

Cela permet au client et au serveur de rattacher le Discover, l’Offer, le Request et l’ACK à la même transaction. Sans cet identifiant, dans un réseau avec plusieurs clients et plusieurs serveurs DHCP, les réponses pourraient être mélangées et il serait difficile de savoir quelle Offer ou quel ACK correspond à quelle demande.
```

**Question 4.** Que renvoie le serveur si vous demandez explicitement une
adresse hors du pool (essayez `dhclient -v -s 172.20.1.99 eth0`)&nbsp;?
Justifiez.

> 💬 **Votre réponse :**
>
```
Si le client demande explicitement une adresse hors du pool DHCP, par exemple `172.20.1.99` alors que le pool autorisé est `172.20.1.100 -- 172.20.1.200`, le serveur ne doit pas attribuer cette adresse.

Comme l’adresse demandée ne fait pas partie de la plage d’allocation configurée, le serveur DHCP doit refuser cette demande. Dans un comportement DHCP autoritaire, cela se traduit par un refus de type DHCPNAK si le serveur reçoit une demande considérée comme invalide pour ce réseau.
```

**Question 5.** La directive `dhcp-authoritative` est active sur notre
serveur. Quel est son effet **comportemental** sur les NAK&nbsp;?

> 💬 **Votre réponse :**
```
> La directive `dhcp-authoritative` indique que ce serveur DHCP se considère comme l’autorité légitime sur ce réseau.

Son effet est important pour les NAK : si un client demande une adresse invalide, ancienne, hors pool ou incohérente avec le réseau, le serveur peut répondre rapidement par un DHCPNAK. Cela évite que le client conserve une mauvaise configuration et accélère le retour vers une demande DHCP propre.
```

### 4. Renouvellement de bail (T1/T2)

Le bail est de 12&nbsp;h, T1 (renouvellement) à 6&nbsp;h, T2 (rebind) à 10&nbsp;h30.
En **2-3 phrases**, décrivez la différence entre un renouvellement T1 et
un rebind T2 (destinataire du paquet, comportement attendu).

```
T1 correspond au renouvellement normal du bail. À ce moment-là, le client essaie de renouveler son adresse auprès du serveur DHCP qui lui a attribué le bail initial, ici `172.20.1.2`, généralement en unicast.

T2 correspond au rebind. Si le client n’a pas réussi à renouveler son bail pendant T1, il tente de contacter n’importe quel serveur DHCP disponible, généralement en broadcast. Le but est d’éviter l’expiration complète du bail et la perte de configuration réseau.
```

> 💬 **Votre réponse :**
>
> _Remplacez ce texte par votre réponse._
