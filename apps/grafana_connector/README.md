# OpenFactory Grafana Connector

The OpenFactory Grafana Connector exposes the current state of OpenFactory assets through a REST API that can be consumed by Grafana using the Infinity datasource.

The connector is intentionally generic. It dynamically retrieves all attributes of an OpenFactory asset and exposes them as a JSON object.

To reduce the number of requests sent to the OpenFactory API, the connector maintains a short-lived in-memory cache. Multiple requests for the same asset within the cache time-to-live (TTL) are therefore served directly from memory.

## REST API

### Get the current state of an asset

```http
GET /assets/{asset_uuid}
```

Example:

```http
GET /assets/VIRTUAL-MTCONNECT-TEMP-SENS
```

Response:

```json
{
  "AssetType": "Device",
  "DockerService": "",
  "Temp": 216.92,
  "asset": "VIRTUAL-MTCONNECT-TEMP-SENS",
  "avail": "AVAILABLE",
  "inc": "Demofactory",
  "references_above": "",
  "references_below": "VIRTUAL-MTCONNECT-TEMP-SENS-PRODUCER, VIRTUAL-MTCONNECT-TEMP-SENS-AGENT",
  "uns_id": "Demofactory/VIRTUAL-MTCONNECT-TEMP-SENS"
}
```

## Deployment

Deploy the connector on an OpenFactory cluster using the following application configuration:

```yaml
apps:

  grafana-connector-app:
    uuid: OPENFACTORY-GRAFANA-CONNECTOR
    image: ghcr.io/openfactoryio/grafana-connector

    environment:
      - LOG_LEVEL=${OPENFACTORY_GRAFANA_CONNECTOR_LOG_LEVEL:-INFO}
      - LOG_HTTP_REQUESTS=${LOG_HTTP_REQUESTS:-False}

    routing:
      expose: true
      port: 4000
      hostname: openfactory-grafana-connector

    networks:
      - factory-net
```

Deploy the application with:

```bash
ofa device up app_grafana_connector.yml
```

## Configuration

The connector supports the following environment variables.

| Variable            | Default | Description                                |
| ------------------- | ------- | ------------------------------------------ |
| `LOG_LEVEL`         | `INFO`  | Application log level.                     |
| `LOG_HTTP_REQUESTS` | `False` | Enables logging of incoming HTTP requests. |
| `CACHE_TTL`         | `1.0`   | Lifetime of cached asset states (seconds). |

## Configuring Grafana

The connector is designed to be used with the **Infinity** datasource.

### Install the datasource

Configure Grafana to install the plugin automatically:

```yaml
environment:
  GF_INSTALL_PLUGINS: yesoreyeram-infinity-datasource
```

### Create the datasource

Create an **Infinity** datasource.

Example configuration (assuming OpenFactory is configured with `OPENFACTORY_BASE_DOMAIN=openfactory.local`):

* Base URL

```
http://openfactory-grafana-connector.openfactory.local
```

### Query an asset

Each Grafana panel simply performs a GET request such as

```
/assets/<ASSET-UUID>
```

The connector returns the complete asset state as JSON.

Each panel can then select the attribute it wishes to display (for example `Temp`, `avail`, or `AssetType`).

Because the connector caches complete asset states, multiple panels requesting the same asset generate only a single request to the OpenFactory API during the cache lifetime.

## Design

The Grafana Connector intentionally contains no application-specific logic.

Its responsibilities are limited to:

* exposing a REST API for Grafana,
* retrieving the current state of OpenFactory assets,
* caching recently requested asset states,
* returning the state as JSON.

This design allows the connector to remain unchanged even if the underlying OpenFactory state provider evolves in the future.
