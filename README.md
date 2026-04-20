[![xcore](https://img.shields.io/badge/xcore-2.0.0-blue)](https://www.github.com/traoreera/xcore)
[![version](https://img.shields.io/badge/version-0.1.0-green)]()

# Talion

**Talion** est un plugin API Gateway et Load Balancer hautement performant pour [xcore](https://www.github.com/traoreera/xcore). Il fournit une solution de routage et de répartition de charge **stateless**, conçue pour être compatible avec des déploiements multi-instances grâce à une synchronisation via le cache centralisé.

## 🚀 Fonctionnalités

- **🌐 Proxy HTTP Dynamique** - Redirection intelligente des requêtes vers les backends avec support du streaming.
- **⚖️ Load Balancing Avancé** - 3 algorithmes de répartition de charge :
  - `round_robin` - Distribution circulaire équitable.
  - `weighted` - Répartition basée sur des poids définis.
  - `least_connections` - Priorise les backends ayant le moins de connexions actives.
- **💚 Health Check & Auto-healing** - Surveillance continue de la santé des backends avec mise hors service automatique en cas d'échec.
- **🔄 Résilience (Retry)** - Mécanisme de retry automatique avec fallback sur un autre nœud en cas d'erreur réseau.
- **📊 Administration & Stats** - API complète pour gérer les services et monitorer les performances en temps réel.
- **💾 Architecture Stateless** - État stocké intégralement dans le cache xcore (Redis) pour une scalabilité horizontale parfaite.

## 📁 Structure du Projet

```text
talion/
├── plugin.yaml          # Configuration et métadonnées du plugin
├── plugin.sig           # Signature de sécurité
├── GEMINI.md            # Documentation contextuelle pour l'IA
├── src/
│   ├── main.py          # Point d'entrée du plugin
│   ├── section.py       # Modèles de configuration (EnvClass)
│   ├── dependencies.py  # Injection de dépendances FastAPI (LB, HTTP client)
│   ├── Balancer/
│   │   ├── balencer.py  # Orchestrateur du load balancer (stateless)
│   │   ├── algorithms.py # Mixin des algorithmes de sélection
│   │   ├── cache_io.py  # Mixin d'interaction avec le cache xcore
│   │   ├── section.py   # Modèles de données des nœuds (BackendNode)
│   └── gateway/
│       ├── proxy.py     # Logique de proxying et retry
│       ├── health.py    # Endpoint de santé public/interne
│       └── adminsitration.py # API d'administration (RBAC sécurisé)
```

## ⚙️ Configuration (`plugin.yaml`)

Le comportement de Talion est piloté par la section `env` du fichier `plugin.yaml` :

```yaml
env:
  urls:
    auth:
      - http://auth-service-1:8000/
    user:
      - http://user-service-1:8000/
      - http://user-service-2:8000/
  
  algorithm: round_robin # Options: round_robin, weighted, least_connections
  proxy_timeout: 30.0    # Timeout des requêtes vers les backends
  proxy_max_retries: 2   # Nombre de tentatives max avant 502
```

## 🛠️ API Endpoints

### 1. Proxy Gateway
Redirige les requêtes vers le backend approprié. Requiert une authentification xcore.
- **Route** : `/{service}/{path:path}`
- **Méthodes** : `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`

### 2. Administration (Sécurisé par RBAC)
Tous les endpoints d'administration requièrent des rôles spécifiques (`talion:add`, `talion:delete`, `talion:list`).

- **Stats** : `GET /admin/stats` - État détaillé de tous les pools.
- **Health** : `GET /health` - Résumé simplifié de l'état des services.
- **Gestion des Services** :
    - `POST /admin/services` : Ajouter un nouveau service dynamiquement.
    - `DELETE /admin/services/{name}` : Supprimer un service.
    - `POST /admin/setup` : Réinitialisation complète de la configuration.
- **Maintenance Manuelle** :
    - `POST /admin/services/{service}/nodes/unhealthy` : Forcer un nœud en mode hors-service.
    - `POST /admin/services/{service}/nodes/healthy` : Remettre un nœud en service.

## 🏗️ Architecture Technique

### Load Balancing Stateless
Talion n'utilise pas de mémoire locale pour stocker l'état des compteurs ou des index. Il utilise deux clés principales dans le cache :
- `Talion:lb:services` : Contient la liste des nœuds, leur état de santé, leur poids et le nombre de connexions actives.
- `Talion:lb:rr` : Stocke l'index actuel pour l'algorithme Round Robin par service.

Cette approche garantit que si vous avez 10 instances de Talion, elles se partagent exactement la même vision de l'infrastructure.

### Gestion des Erreurs
- **503 Service Unavailable** : Aucun backend n'est enregistré ou aucun n'est sain.
- **502 Bad Gateway** : Les tentatives vers les backends ont toutes échoué (Timeout/Connection Error).

## 🛠️ Développement

### Prérequis
- Python 3.10+
- xcore framework v2.0.0

### Tests & Qualité
Le plugin utilise les standards de `xcore`. Assurez-vous que votre environnement dispose de `httpx` installé.

```bash
pip install httpx
```

## 📄 License

Projet interne développé par la **xcore team**.
