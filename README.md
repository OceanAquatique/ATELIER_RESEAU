------------------------------------------------------------------------------------------------------
🎯 Comprendre les bases du réseau (OSI, DHCP, NAT) — Atelier Master 2
------------------------------------------------------------------------------------------------------
Cet atelier propose une exploration **pratique** des fondamentaux des réseaux à travers trois mécanismes essentiels — le modèle **OSI**, le protocole **DHCP** et la traduction d'adresses **NAT/PAT** — au niveau Master 2.

Deux supports complémentaires sont mis à disposition :

1. **Une application Flask de référence** (`flask_app.py`), à héberger sur PythonAnywhere, qui sert de fiche théorique structurée (JSON) sur chacun des trois mécanismes, et qui expose une route `/metrics` de QoS observable (latence p50/p90/p95/p99, débit, taux d'erreur, jitter, token-bucket).
2. **Un mini-réseau conteneurisé** (répertoire [`lab/`](lab/)), constitué de 4 services Docker (DHCP server, NAT router, client, "Internet" simulé) sur lequel les étudiant·e·s **capturent de vrais paquets** (tcpdump/tshark), **manipulent des règles iptables**, et observent **la table conntrack en direct**.

**Notre architecture cible**

![Screenshot Actions](Architecture_cible_Reseau.png)

-------------------------------------------------------------------------------------------------------
🧩 Séquence 1 : GitHub
-------------------------------------------------------------------------------------------------------
Objectif : créer un Repository GitHub pour travailler avec votre fork du projet.
Difficulté : Très facile (~10 minutes)
-------------------------------------------------------------------------------------------------------
**Faites un Fork de ce projet**. Si besoin, voici une vidéo d'accompagnement : [Forker ce projet](https://youtu.be/p33-7XQ29zQ)

---------------------------------------------------
🧩 Séquence 2 : Hébergement sur PythonAnywhere
---------------------------------------------------
Objectif : héberger l'application Flask de référence.
Difficulté : Faible (~10 minutes)
---------------------------------------------------

Rendez-vous sur **https://www.pythonanywhere.com/**, créez un compte, puis un serveur Web **Flask 3.13**.

---------------------------------------------------------------------------------------------
🧩 Séquence 3 : GitHub Actions (Industrialisation Continue)
---------------------------------------------------------------------------------------------
Objectif : automatiser la mise à jour de votre hébergement PythonAnywhere.
Difficulté : Moyenne (~15 minutes)
---------------------------------------------------------------------------------------------
Le workflow `.github/workflows/deploy-pythonanywhere.yml` déploie automatiquement votre code à chaque push sur `main` via l'API PythonAnywhere.

**Vous avez 4 secrets à créer** dans **Settings → Secrets and variables → Actions → New repository secret**&nbsp;:

| Secret              | Valeur                                                   |
| ------------------- | -------------------------------------------------------- |
| `PA_USERNAME`       | votre username PythonAnywhere                            |
| `PA_TOKEN`          | API token (Account → API Token)                          |
| `PA_TARGET_DIR`     | Web → Source code (ex&nbsp;: `/home/monuser/myapp`)      |
| `PA_WEBAPP_DOMAIN`  | votre site (ex&nbsp;: `monuser.pythonanywhere.com`)      |

**Dernière étape :** activez les workflows depuis l'onglet [Actions] du repo (« I understand my workflows, go ahead and enable them »).

---------------------------------------------------
🗺️ Séquence 4 : OSI (Open Systems Interconnection)
---------------------------------------------------
Difficulté : Moyenne (~1 h)
---------------------------------------------------

**Côté théorie** — consultez la fiche structurée sur **`{site}.pythonanywhere.com/osi`**.

**Côté pratique** — réalisez l'**[exercice 1](lab/exercises/01_osi_capture.md)** dans le lab Docker&nbsp;: capture HTTP au tcpdump, décodage couche par couche au `tshark`, et identification d'un champ concret pour chaque couche OSI.

**Exercice 1.1 — Définitions (réponse directement dans ce README)**

* Un **protocole** :
* Une **entité protocolaire** :
* Un **service** :
* Une **primitive de service** :
* Une **Service Data Unit (SDU)** par rapport à une PDU :
* Un **point d'accès à un service (SAP)** :

**Exercice 1.2 — Capture OSI (sortie du lab Docker)**

Collez votre tableau « Couche / élément observé / valeur exemple » issu de [`lab/exercises/01_osi_capture.md`](lab/exercises/01_osi_capture.md).

---------------------------------------------------
🗺️ Séquence 5 : Retour sur le protocole DHCP
---------------------------------------------------
Difficulté : Moyenne (~1 h)
---------------------------------------------------

**Côté théorie** — fiche sur **`{site}.pythonanywhere.com/dhcp`**.

**Côté pratique** — réalisez l'**[exercice 2](lab/exercises/02_dhcp_dora.md)**&nbsp;: capturez un DORA complet sur le lab, identifiez les options DHCP des 4 paquets, répondez aux questions sur le broadcast, le `xid`, et le renouvellement T1/T2.

**Exercice 2 — Capture DHCP (sortie du lab Docker)**

* Collez votre **tableau DORA** (4 lignes).
* Collez votre **configuration finale du client** (IP, masque, GW, DNS, bail).
* Collez votre **schéma d'encapsulation** (Ethernet → IP → UDP → BOOTP/DHCP).

---------------------------------------------------
🗺️ Séquence 6 : NAT / PAT
---------------------------------------------------
Difficulté : Élevée (~1 h)
---------------------------------------------------

**Côté théorie** — fiche sur **`{site}.pythonanywhere.com/nat`**.

**Côté pratique** — réalisez l'**[exercice 3](lab/exercises/03_nat_pat.md)**&nbsp;: observation de la table `conntrack`, suppression / restauration de la règle MASQUERADE, mise en place d'un DNAT entrant.

**Exercice 3 — Sortie du lab Docker**

* Collez **deux lignes de `conntrack -L`** annotées.
* Répondez aux questions de synthèse (NAT vs PAT, NAT et sécurité, NAT en IPv6).

---------------------------------------------------
🗺️ Séquence 7 (Bonus) : Détection d'un rogue DHCP
---------------------------------------------------
Difficulté : Élevée (~1 h 30)
---------------------------------------------------

**Optionnel mais recommandé pour le M2** — réalisez l'**[exercice 4 (bonus)](lab/exercises/04_rogue_dhcp_bonus.md)**&nbsp;: ajoutez un faux serveur DHCP dans le lab, observez la course aux Offers, écrivez un script de détection passive, et comparez 3 contre-mesures (DHCP Snooping, 802.1X, détection passive).

---------------------------------------------------
🗺️ Séquence 8 : Métriques de QoS observées
---------------------------------------------------

L'app Flask expose `/metrics` qui calcule sur les requêtes récentes&nbsp;:
* latence p50 / p90 / p95 / p99,
* débit (req/s sur 60&nbsp;s),
* taux d'erreur,
* jitter (somme absolue des diffs entre latences consécutives),
* politique QoS appliquée (token bucket).

**Exercice 4 — Charge & QoS**

Depuis votre poste, injectez une rafale et observez `/metrics`&nbsp;:

```bash
for i in $(seq 1 30); do curl -s -o /dev/null https://{site}.pythonanywhere.com/osi; done
curl -s https://{site}.pythonanywhere.com/metrics | python -m json.tool
```

Commentez en 5-6 lignes&nbsp;:
* Quelle est la **différence sémantique** entre p50 et p99&nbsp;? Pour quel type de SLO chacune est-elle pertinente&nbsp;?
* À partir de combien de requêtes/seconde le token bucket commence-t-il à **rejeter** (HTTP 429)&nbsp;? Recoupez avec les paramètres `TOKENS_PER_SEC` et `BURST`.

--------------------------------------------------------------------
🧠 Troubleshooting
---------------------------------------------------
Objectif : visualiser vos logs et identifier vos erreurs.
---------------------------------------------------

**Côté PythonAnywhere** — accédez aux trois journaux suivants&nbsp;:
* Access log&nbsp;: `{site}.pythonanywhere.com.access.log`
* Error log&nbsp;: `{site}.pythonanywhere.com.error.log`
* Server log&nbsp;: `{site}.pythonanywhere.com.server.log`

**Côté lab Docker** — commandes utiles&nbsp;:

```bash
docker compose ps                          # état des services
docker logs -f lab_dhcp_server             # journal DHCP en direct
docker logs -f lab_nat_router              # règles iptables au démarrage
docker exec lab_nat_router conntrack -L    # table de traduction NAT
docker exec lab_internet tail -f /var/log/nginx/access.log
```

Si le NAT ne fonctionne pas (`curl` timeout), relancez **`sudo ./lab/host-setup.sh`** — voir [`lab/README.md`](lab/README.md) pour l'explication détaillée du `br_netfilter`.
