from prometheus_client import Info, Gauge
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response


# Metrics definitions
BUILD_INFO = Info(
    "monitor_build",
    "Build information for the OpenFactory Monitor"
)

DEPLOYED_ASSETS = Gauge(
    "deployed_assets_count",
    "Number of assets currently deployed in OpenFactory"
)

AVAILABLE_ASSETS = Gauge(
    "available_assets_count",
    "Number of assets currently available in OpenFactory"
)

UNAVAILABLE_ASSETS = Gauge(
    "unavailable_assets_count",
    "Number of assets currently unavailable in OpenFactory"
)

APP_END_TO_END_LATENCY = Gauge(
    "asset_attribute_end_to_end_latency_seconds",
    "End-to-end latency for Asset Attribute changes"
)

INGESTION_LATENCY = Gauge(
    "asset_attribute_ingestion_latency_seconds",
    "Latency from Asset Attribute emission to ingestion"
)

KSQLLATENCY = Gauge(
    "ksqldb_latency_seconds",
    "Latency introduced by KsqlDB transport"
)

KAFKA_LATENCY = Gauge(
    "kafka_latency_seconds",
    "Latency introduced by Kafka transport (inside Kafka cluster)"
)

FAN_OUT_LAYER_LATENCY = Gauge(
    "fan_out_layer_latency_seconds",
    "Latency introduced by the fan-out layer"
)

SHDR_LATENCY = Gauge(
    "shdr_end_to_end_latency_seconds",
    "End-to-end latency for SHDR devices"
)

SHDR_GATEWAY_LATENCY = Gauge(
    "shdr_gateway_latency_seconds",
    "Latency introduced by the SHDR Gateway"
)

SHDR_KAFKA_LATENCY = Gauge(
    "shdr_kafka_latency_seconds",
    "Latency introduced by the SHDR Kafka transport (producer to asset-forwarder)"
)


def metrics_endpoint():
    """
    FastAPI endpoint for Prometheus scraping.
    """
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
