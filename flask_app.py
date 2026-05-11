import os
import time
import random
from collections import deque
from flask import Flask, request, jsonify

app = Flask(__name__)

# ---- Simple in-memory "QoS" simulation state ----
WINDOW = deque(maxlen=2000)  # store (t, endpoint, duration_ms, status)
TOKENS_PER_SEC = 5           # rate limit (simulated QoS policy)
BURST = 10
tokens = BURST
last_refill = time.time()

def now_ms():
    return int(time.time() * 1000)

def refill_tokens():
    global tokens, last_refill
    t = time.time()
    elapsed = t - last_refill
    add = int(elapsed * TOKENS_PER_SEC)
    if add > 0:
        tokens = min(BURST, tokens + add)
        last_refill = t

def qos_admit():
    """Token bucket admission: return (allowed, retry_after_seconds)."""
    global tokens
    refill_tokens()
    if tokens > 0:
        tokens -= 1
        return True, 0
    return False, 1  # simplistic retry-after

def record(endpoint, duration_ms, status):
    WINDOW.append((time.time(), endpoint, duration_ms, status))

def compute_metrics():
    # Compute latency percentiles + error rate + throughput approximation over last N entries
    data = list(WINDOW)
    if not data:
        return {}
    durations = sorted([d[2] for d in data])
    errors = sum(1 for d in data if d[3] >= 400)
    total = len(data)
    error_rate = errors / total

    # Approx throughput over last 60 seconds
    cutoff = time.time() - 60
    last60 = [d for d in data if d[0] >= cutoff]
    rps = len(last60) / 60 if last60 else 0

    def pct(p):
        idx = int(round((p/100) * (len(durations)-1)))
        return durations[max(0, min(idx, len(durations)-1))]

    # jitter = stddev-ish approximation on consecutive diffs (simple)
    diffs = [abs(durations[i] - durations[i-1]) for i in range(1, len(durations))]
    jitter = sum(diffs)/len(diffs) if diffs else 0

    return {
        "count": total,
        "error_rate": round(error_rate, 4),
        "rps_last_60s": round(rps, 3),
        "latency_ms": {
            "p50": pct(50),
            "p90": pct(90),
            "p95": pct(95),
            "p99": pct(99),
            "max": durations[-1],
        },
        "jitter_ms_avg_absdiff": round(jitter, 2),
        "qos_policy": {
            "token_bucket": {"tokens_per_sec": TOKENS_PER_SEC, "burst": BURST}
        }
    }

@app.before_request
def start_timer():
    request._t0 = time.time()

@app.after_request
def end_timer(response):
    duration_ms = int((time.time() - getattr(request, "_t0", time.time())) * 1000)
    record(request.path, duration_ms, response.status_code)
    # Expose "service" metadata (contract-ish headers)
    response.headers["X-Service-Name"] = "network-lab"
    response.headers["X-Service-Version"] = "1.0"
    response.headers["X-Request-Id"] = str(now_ms()) + "-" + str(random.randint(1000,9999))
    return response

@app.get("/")
def index():
    return """
    <h1>Network Lab (Flask)</h1>
    <ul>
      <li><a href="/osi">/osi</a> — OSI mapping</li>
      <li><a href="/dhcp">/dhcp</a> — Protocole DHCP</li>
      <li><a href="/nat">/nat</a> — Protocole NAT</li>
      <li><a href="/metrics">/metrics</a> — Métriques QoS (latence, débit, taux d'erreur)</li>
    </ul>
    """

@app.get("/osi")
def osi():
    # Ce qu'une application web peut observer dans le modèle OSI
    # (principalement couche 7 et un peu couche 4)

    info = {
        "Couche_7_Application": {
            "description": "Interaction directe avec l'application web (HTTP).",
            "methode_http": request.method,
            "chemin_requete": request.path,
            "exemple_entetes_http": {
                k: request.headers.get(k)
                for k in ["Host", "User-Agent", "Accept", "Content-Type"]
            }
        },

        "Couche_6_Presentation": {
            "description": "Gestion du format des données et du chiffrement.",
            "exemple": "JSON (UTF-8), encodage des données, TLS/HTTPS.",
            "remarque": "Souvent gérée par les bibliothèques ou le serveur web."
        },

        "Couche_5_Session": {
            "description": "Gestion de la session entre client et serveur.",
            "exemple": "Cookies, sessions HTTP, maintien de connexion (keep-alive).",
            "remarque": "Généralement gérée par le framework ou l'application."
        },

        "Couche_4_Transport": {
            "description": "Communication entre machines via TCP ou UDP.",
            "adresse_client": request.remote_addr,
            "remarque": "HTTP utilise TCP. Les détails du handshake ou des ports ne sont pas visibles directement dans Flask."
        },

        "Couche_3_Reseau": {
            "description": "Routage des paquets IP entre réseaux.",
            "remarque": "L'application ne voit généralement que l'adresse IP du client (souvent via un proxy)."
        },

        "Couche_2_Liaison_de_donnees": {
            "description": "Transmission des trames sur le réseau local.",
            "exemple": "Ethernet ou Wi-Fi.",
            "remarque": "Les adresses MAC et les trames ne sont pas visibles dans une application web."
        },

        "Couche_1_Physique": {
            "description": "Transmission physique des bits.",
            "exemple": "Câble réseau, fibre optique, ondes radio Wi-Fi.",
            "remarque": "Totalement invisible pour une application."
        }
    }

    return jsonify(info)

@app.get("/dhcp")
def dhcp():
    info = {
        "protocole": "DHCP",
        "signification": "Dynamic Host Configuration Protocol",
        "role": "Attribuer automatiquement une configuration réseau à un équipement.",
        
        "a_quoi_sert_dhcp": {
            "adresse_ip": "Attribue une adresse IP au client.",
            "masque": "Fournit le masque de sous-réseau.",
            "passerelle": "Indique la passerelle par défaut.",
            "dns": "Fournit l'adresse des serveurs DNS.",
            "autres_parametres": "Peut aussi fournir d'autres options réseau."
        },

        "ports": {
            "client": 68,
            "serveur": 67,
            "transport": "UDP"
        },

        "fonctionnement": {
            "etape_1_discover": "Le client envoie un message DHCP Discover pour chercher un serveur DHCP.",
            "etape_2_offer": "Le serveur répond avec un DHCP Offer proposant une adresse IP.",
            "etape_3_request": "Le client répond avec un DHCP Request pour demander l'adresse proposée.",
            "etape_4_ack": "Le serveur confirme avec un DHCP ACK et attribue officiellement la configuration."
        },

        "mnemonique": "DORA = Discover, Offer, Request, Acknowledge",

        "bail": {
            "definition": "L'adresse IP est attribuée pour une durée limitée appelée bail.",
            "renouvellement": "Le client tente de renouveler son bail avant son expiration."
        },

        "avantages": [
            "Automatisation de la configuration réseau",
            "Réduction des erreurs de saisie manuelle",
            "Gestion centralisée des adresses IP",
            "Gain de temps pour les administrateurs"
        ],

        "risques_ou_points_de_vigilance": [
            "Un faux serveur DHCP peut distribuer de mauvaises configurations",
            "Une mauvaise plage d'adresses peut provoquer des conflits",
            "Le serveur DHCP est un point important de l'infrastructure"
        ],

        "couches_osi": {
            "couche_7": "Service réseau utilisé par les équipements",
            "couche_4": "Utilise UDP",
            "couche_3": "Fonctionne sur IP",
            "remarque": "DHCP est généralement associé à la couche application dans le modèle OSI."
        },

        "exemple_concret": "Quand un PC ou un smartphone se connecte à un réseau, il demande automatiquement une adresse IP via DHCP."
    }

    return jsonify(info)

@app.get("/nat")
def nat():
    info = {
        "protocole_ou_mecanisme": "NAT",
        "signification": "Network Address Translation",
        "role": "Traduire des adresses IP privées en adresse(s) IP publique(s) pour permettre la communication avec Internet.",

        "pourquoi_on_utilise_nat": {
            "economie_adresses_ipv4": "Permet à plusieurs machines privées de partager une même adresse IP publique.",
            "masquage_reseau_interne": "Les machines internes ne sont pas directement visibles depuis Internet.",
            "sortie_vers_internet": "Permet aux postes internes d'accéder au web même s'ils utilisent des adresses privées."
        },

        "adresses_privees_courantes": [
            "10.0.0.0/8",
            "172.16.0.0/12",
            "192.168.0.0/16"
        ],

        "types_de_nat": {
            "nat_statique": "Une adresse IP privée est associée en permanence à une adresse IP publique.",
            "nat_dynamique": "Une adresse privée reçoit temporairement une adresse publique d'un pool.",
            "pat_nat_overload": "Plusieurs machines privées partagent une même IP publique grâce à la traduction des ports."
        },

        "cas_le_plus_courant": {
            "nom": "PAT",
            "autre_nom": "NAT Overload",
            "explication": "Le routeur remplace l'IP source privée par son IP publique et modifie aussi le port source."
        },

        "exemple_simple": {
            "avant_nat": {
                "ip_source": "192.168.1.10",
                "port_source": 51514,
                "ip_destination": "142.250.179.14",
                "port_destination": 443,
                "protocole": "TCP"
            },
            "apres_nat": {
                "ip_source": "203.0.113.5",
                "port_source": 40001,
                "ip_destination": "142.250.179.14",
                "port_destination": 443,
                "protocole": "TCP"
            },
            "explication": "Le routeur NAT remplace l'adresse privée 192.168.1.10 par son IP publique 203.0.113.5 et change le port source 51514 en 40001."
        },

        "table_nat_exemple": [
            {
                "interne": "192.168.1.10:51514",
                "publique": "203.0.113.5:40001",
                "destination": "142.250.179.14:443",
                "protocole": "TCP"
            },
            {
                "interne": "192.168.1.11:51515",
                "publique": "203.0.113.5:40002",
                "destination": "1.1.1.1:53",
                "protocole": "UDP"
            }
        ],

        "fonctionnement_retour": {
            "principe": "Quand la réponse revient vers l'IP publique et le port traduits, le routeur consulte sa table NAT.",
            "exemple": "203.0.113.5:40001 est remappé vers 192.168.1.10:51514.",
            "resultat": "La réponse est renvoyée à la bonne machine interne."
        },

        "avantages": [
            "Partage d'une même IP publique",
            "Réduction de la consommation d'adresses IPv4",
            "Masquage partiel du réseau interne"
        ],

        "limites": [
            "Complexifie certains protocoles",
            "Peut gêner les connexions entrantes",
            "N'est pas un mécanisme de sécurité suffisant à lui seul"
        ],

        "couche_osi": {
            "principale": "Couche 3 - Réseau",
            "nuance": "Quand le NAT modifie aussi les ports (PAT), il touche également des informations liées à la couche 4."
        },

        "analogie": "Le NAT agit comme un standard téléphonique : plusieurs postes internes sortent avec un même numéro principal, mais le standard sait à qui renvoyer chaque appel retour."
    }

    return jsonify(info)

@app.get("/metrics")
def metrics():
    """Métriques QoS observées sur les requêtes récentes (latence, débit, taux d'erreur)."""
    allowed, retry_after = qos_admit()
    if not allowed:
        resp = jsonify({"error": "rate_limited", "retry_after_seconds": retry_after})
        resp.status_code = 429
        resp.headers["Retry-After"] = str(retry_after)
        return resp
    return jsonify(compute_metrics())

if __name__ == "__main__":
    # utile en local uniquement
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
