[![xcore](https://img.shields.io/badge/xcore-2.0.0-blue)](https://www.github.com/traoreera/xcore)
[![version](https://img.shields.io/badge/version-0.1.0-green)]()

**Talion** est un plugin API Gateway et Load Balancer pour [xcore](https://www.github.com/traoreera/xcore). Il fournit une solution de routage et de répartition de charge stateless, compatible multi-instance.

## 🚀 Fonctionnalités

- **🌐 Proxy HTTP** - Redirection des requêtes vers les backends avec support du streaming
- **⚖️ Load Balancing** - 3 algorithmes de répartition de charge :
  - `round_robin` - Rotation circulaire
  - `weighted` - Répartition pondérée aléatoire
  - `least_connections` - Moindres connexions actives
- **💚 Health Check** - Surveillance de la santé des backends
- **🔄 Retry** - Mécanisme de retry automatique avec fallback
- **📊 Statistiques** - Endpoint de monitoring des services
- **💾 Stateless** - Stockage dans le cache pour compatibilité multi-instance

## 📁 Structure du projet

```
talion/
├── plugin.yaml          # Configuration du plugin xcore
├── plugin.sig           # Signature du plugin
├── src/
│   ├── main.py          # Point d'entrée du plugin
│   ├── section.py       # Configuration (EnvClass)
│   ├── dependencies.py  # Dépendances FastAPI (LoadBalancer, HTTP client)
│   ├── Balancer/
│   │   ├── balencer.py  # Logique principale du load balancer
│   │   ├── algorithms.py # Algorithmes de sélection
│   │   ├── cache_io.py  # Interactions avec le cache
│   │   └── section.py   # Modèles de données (BackendNode)
│   └── gateway/
│       ├── proxy.py     # Routeur de proxy HTTP
│       ├── health.py    # Endpoint de santé
│       └── administration.py  # Administration
```

## ⚙️ Configuration

### plugin.yaml

```yaml
name: talion
version: 0.1.0
author: xcore team's
description: >
  talion est un api gateway plus un systeme de balence 
  de serveur 

execution_mode: trusted
entry_point: src/main.py
framework_version: "==2.0.0"

requires:
  - name: auth
    version: ">=0.1.0,<0.3.0"

permissions: []

resources:
  timeout_seconds: 15
  max_memory_mb: 256
  max_disk_mb: 100
  rate_limit:
    calls: 10000
    period_seconds: 60

  runtime:
    health_check:
      enabled: true
      interval_seconds: 60
      timeout_seconds: 3
    
    retry:
      max_attempts: 3
      backoff_seconds: 3.0

env:
  urls:
    auth:
      - http://localhost:8000/app/auth/
    user:
      - http://localhost:8000/user
      - http://localhost:9000/user
  
  algorithm: round_robin  # round_robin | weighted | least_connections
  proxy_timeout: 30.0
  proxy_max_retries: 2
```

## 🔧 Utilisation

### Démarrage

Le plugin s'intègre automatiquement à xcore et expose les routes suivantes :

### Endpoints

#### 1. Proxy

Redirige les requêtes vers le backend sélectionné par le load balancer.

```
/{service}/{path:path}
```

**Méthodes supportées** : GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS

**Exemple** :
```bash
curl http://localhost:8000/talion/user/profile
# → Proxy vers un des backends "user"
```

#### 2. Health Check

```
/health
```

Retourne l'état de santé de tous les services :
```json
{
  "status": "ok",
  "degraded_services": [],
  "services": {
    "auth": {"total": 1, "healthy": 1},
    "user": {"total": 2, "healthy": 2}
  }
}
```

## 🏗️ Architecture

### LoadBalancer

Le `LoadBalancer` est stateless - toutes les données sont stockées dans le cache xcore :

- `Talion:lb:services` - Pool de backends par service
- `Talion:lb:rr` - Index round-robin

Cela permet de faire tourner plusieurs instances de Talion sans partage de mémoire.

### Algorithmes

| Algorithme | Description |
|------------|-------------|
| `round_robin` | Distribution circulaire équitable |
| `weighted` | Sélection basée sur les poids définis |
| `least_connections` | Route vers le backend avec le moins de connexions actives |

### Gestion des erreurs

- **Retry** : En cas d'échec (timeout, connexion refusée), le plugin réessaie avec un autre backend
- **Mark unhealthy** : Un backend en échec est marqué comme unhealthy
- **503** : Retourné si aucun backend n'est disponible
- **502** : Retourné si tous les backends ont échoué

## 🛠️ Développement

### Prérequis

- Python 3.10+
- xcore 2.0.0

### Dépendances

```python
from xcore.sdk import TrustedBase, AutoDispatchMixin
from xcore.services.cache.service import CacheService
```

### Tests

À implémenter selon les besoins du projet xcore.

## 📄 License

Projet interne xcore team.

---

**Note** : Ce plugin nécessite l'installation de [xcore](https://www.github.com/traoreera/xcore) pour fonctionner.
