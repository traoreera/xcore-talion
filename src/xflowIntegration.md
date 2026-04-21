# Intégration XFlow — Plugin Talion

API Gateway et Load Balancer hautement performant.

## ⚡ Actions IPC

| Action | Qualified Name | Entrée (Payload) | Sortie |
| :--- | :--- | :--- | :--- |
| **Health** | `talion.health` | - | `HealthResponse` |
| **Services** | `talion.services` | - | `ServicesResponse` |

---

## 📦 Détail des Objets (Schemas)

### `HealthResponse`
- `status`: (string) `ok` ou `degraded`.
- `degraded_services`: (array[string]) Liste des services ayant 0 nœud sain.
- `services`: (dict) État détaillé par service :
  - `{ "total": int, "healthy": int }`.

### `ServicesResponse`
- `algorithm`: (string) Algorithme utilisé (`round_robin`, `weighted`, `least_connections`).
- `proxy_timeout`: (float) Temps d'attente max vers les backends.
- `services`: (dict) Liste des URLs configurées par service.

## 📡 Événements (Event Bus)

Pas d'événements métier globaux pour le moment.
