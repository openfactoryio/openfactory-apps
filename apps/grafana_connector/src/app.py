import os
import time
from typing import Any
from openfactory.apps import OpenFactoryFastAPIApp
from openfactory.kafka import KSQLDBClient
from openfactory.assets import Asset


class GrafanaConnector(OpenFactoryFastAPIApp):
    """
    OpenFactory Grafana Connector.

    This application exposes the current state of OpenFactory assets through a
    REST API suitable for Grafana's Infinity datasource.

    To reduce the number of requests sent to the OpenFactory API, asset states
    are cached in memory for a short configurable time-to-live (TTL). Multiple
    requests for the same asset during the TTL are therefore served directly
    from the cache.

    Attributes:
        CACHE_TTL (float): Lifetime of cached asset states, in seconds.
        asset_cache (dict): In-memory cache mapping asset UUIDs to their cached state
            and cache timestamp.
    """

    CACHE_TTL = float(os.getenv("CACHE_TTL", "1.0"))

    def __init__(self, **kwargs):
        """
        Initializes the Grafana connector.

        Args:
            **kwargs: Keyword arguments forwarded to :class:`OpenFactoryFastAPIApp`.
        """
        super().__init__(**kwargs)
        self.asset_cache = {}

    def configure_routes(self):
        """ Configures the REST API endpoints exposed by the connector. """

        @self.api.get("/assets/{asset_uuid}")
        async def get_asset(asset_uuid: str) -> dict[str, Any]:
            """
            Returns the current state of an OpenFactory asset.

            The endpoint first checks the in-memory cache. If a valid cached
            state exists, it is returned immediately. Otherwise, the asset is
            queried through the OpenFactory API, its current state is cached,
            and the resulting JSON object is returned.

            Args:
                asset_uuid: UUID of the asset.

            Returns:
                dict[str, Any]: Dictionary mapping asset attribute IDs to their current values.
            """

            now = time.monotonic()
            cached = self.asset_cache.get(asset_uuid)
            if cached:
                age = now - cached["timestamp"]
                if age < self.CACHE_TTL:
                    return cached["data"]

            asset = Asset(asset_uuid, ksqlClient=self.ksql)

            try:
                data = {}
                attributes = asset.attributes()

                self.logger.debug(
                    "Serving asset '%s' with %d attributes: %s",
                    asset_uuid,
                    len(attributes),
                    ", ".join(attributes),
                )

                for attr in attributes:
                    data[attr] = getattr(asset, attr).value

            finally:
                asset.close()

            self.asset_cache[asset_uuid] = {
                "timestamp": time.monotonic(),
                "data": data,
            }

            return data


app = GrafanaConnector(
    ksqlClient=KSQLDBClient(os.getenv("KSQLDB_URL", "http://localhost:8088")),
    bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
    loglevel=os.getenv("LOG_LEVEL", "INFO"),
    log_http_requests=os.getenv("LOG_HTTP_REQUESTS", "true").lower() == "true",
)

app.run()
