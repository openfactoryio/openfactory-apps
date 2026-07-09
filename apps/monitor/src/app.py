import os
import asyncio
import time
import statistics
from typing import Annotated
from datetime import datetime
from openfactory import OpenFactory
from openfactory.assets import Asset
from openfactory.assets.utils import current_timestamp
from openfactory.apps import OpenFactoryFastAPIApp, SampleAttribute, EventAttribute, ofa_method
from openfactory.kafka import KSQLDBClient
from openfactory.utils import register_device_connector, deregister_device_connector
from openfactory.schemas.devices import Device
from openfactory.schemas.connectors.opcua import OPCUAConnectorSchema
from openfactory.connectors.opcua.opcua_connector import OPCUAConnector
from openfactory.schemas.connectors.shdr import SHDRConnectorSchema
from openfactory.connectors.shdr.shdr_connector import SHDRConnector
from .opcua import OPCUAServer
from .shdr import SHDRServer
from . import metrics


PROMETHEUS_METRICS_PATH = "/metrics"


class OpenFactoryMonitorApp(OpenFactoryFastAPIApp):
    """
    OpenFactory Monitor Application
    """

    METRICS_UPDATE_INTERVAL = 15

    prometheus_metrics_path = EventAttribute(value=PROMETHEUS_METRICS_PATH, tag="Prometheus.metrics_path")

    deployed_assets = SampleAttribute(tag='OpenFactory.Metrics')
    available_assets = SampleAttribute(tag='OpenFactory.Metrics')
    unavailable_assets = SampleAttribute(tag='OpenFactory.Metrics')
    metrics_last_update = EventAttribute(tag='OpenFactory.Metrics')

    app_cmd_end_to_end_latency = SampleAttribute(tag='OpenFactory.App.Metrics')
    app_attribute_end_to_end_latency = SampleAttribute(tag='OpenFactory.App.Metrics')
    ingestion_latency = SampleAttribute(tag='OpenFactory.App.Metrics')

    kafka_latency = SampleAttribute(tag='OpenFactory.Metrics')
    ksqldb_latency = SampleAttribute(tag='OpenFactory.Metrics')
    fan_out_layer_latency = SampleAttribute(tag='OpenFactory.Metrics')

    shdr_end_to_end_latency = SampleAttribute(tag='OpenFactory.App.Metrics')
    shdr_gateway_latency = SampleAttribute(tag='OpenFactory.App.Metrics')
    shdr_kafka_latency = SampleAttribute(tag='OpenFactory.App.Metrics')

    opcua_end_to_end_latency = SampleAttribute(tag='OpenFactory.App.Metrics')
    opcua_gateway_latency = SampleAttribute(tag='OpenFactory.App.Metrics')
    opcua_kafka_latency = SampleAttribute(tag='OpenFactory.App.Metrics')

    probe_event = EventAttribute(tag='OpenFactory.Metrics')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ofa = OpenFactory(ksqlClient=self.ksql)

        self.subscribe_to_attribute('probe_event', on_message=self.on_probe_event)
        self.latency_data = []
        self.cmd_latency_data = []
        self.opcua_latency_data = []
        self.shdr_latency_data = []

        # OpenFactory connectors
        self.shdr_connector = None
        if os.getenv("SHDR_PROBE") == 'true':
            self.monitor_shdr_connector()
        self.opcua_connector = None
        if os.getenv("OPCUA_PROBE") == 'true':
            self.monitor_opcua_connector()

        # Build info metrics
        metrics.BUILD_INFO.info({
            "version": os.environ.get('APPLICATION_VERSION', 'UNKNOWN'),
        })

        # Register metrics with OpenFactory
        self.register_prometheus_metrics(metrics_port=4000, metrics_path=PROMETHEUS_METRICS_PATH)

        # Expose Prometheus metrics
        self.api.get(PROMETHEUS_METRICS_PATH)(metrics.metrics_endpoint)

    @ofa_method()
    def probe_cmd(self, probe: Annotated[str, "Time stamp"]):
        """ Probe command for OpenFactory command latency calculations. """
        # Current time
        now = current_timestamp()
        now_time = datetime.fromisoformat(now.replace('Z', '+00:00'))
        cmd_time = datetime.fromisoformat(probe.replace('Z', '+00:00'))

        # Compute time difference in seconds
        end_to_end_latency = (now_time - cmd_time).total_seconds()

        # Append as dict to list
        self.cmd_latency_data.append(
            {
                'cmd_end_to_end_latency': end_to_end_latency,
            }
        )

        self.logger.debug(f"Probe command {probe}, latency {end_to_end_latency}")

    def monitor_opcua_connector(self):
        """ Configure monitoring of the OPCUA connector """
        self.logger.info('Configure OPCUA Connector monitoring')

        self.opcua_connector = OPCUAConnector(
            deployment_strategy=None,
            ksqlClient=self.ksql,
            bootstrap_servers=self.bootstrap_servers)

        self.opcua = OPCUAServer(self.logger)
        self.connect_opcua_probe()
        self.opcua_asset = Asset(asset_uuid="OPCUA-PROBE", ksqlClient=self.ksql)
        self.opcua_asset.subscribe_to_attribute(attribute_id='probe', on_message=self.on_opcua_probe_event)

    def connect_opcua_probe(self):
        """ Connect the mocked OPC UA device. """
        data = {
            "type": "opcua",
            "server": {
                "uri": f"opc.tcp://{self.asset_uuid.lower()}:4840",
                "subscription": {
                    "publishing_interval": 10,
                    "sampling_interval": 0,
                },
            },
            "variables": {
                "probe": {
                    "browse_path": "0:Root/0:Objects/2:ProbeObject/2:Probe",
                    "tag": "Probe"
                }
            },
        }
        connector_schema = OPCUAConnectorSchema(**data)
        opcua_device = Device(uuid='OPCUA-PROBE', connector=connector_schema)
        self.opcua_connector.deploy(device=opcua_device, yaml_config_file="")
        register_device_connector(opcua_device, self.ksql)

    def deconnect_opcua_probe(self):
        """ Deconnect the mocked OPCUA device. """
        self.opcua_asset.close()
        self.logger.info("Deconnect OPCUA Probe")
        self.opcua_connector.tear_down(device_uuid="OPCUA-PROBE")
        deregister_device_connector(device_uuid="OPCUA-PROBE", bootstrap_servers=self.bootstrap_servers)

    def monitor_shdr_connector(self):
        """ Configure monitoring of the SHDR connector """
        self.logger.info('Configure SHDR Connector monitoring')

        self.shdr_connector = SHDRConnector(
            deployment_strategy=None,
            ksqlClient=self.ksql,
            bootstrap_servers=self.bootstrap_servers)

        self.shdr = SHDRServer(self.logger)
        self.connect_shdr_probe()
        self.shdr_asset = Asset(asset_uuid="SHDR-PROBE", ksqlClient=self.ksql)
        self.shdr_asset.subscribe_to_attribute(attribute_id='probe', on_message=self.on_shdr_probe_event)

    def connect_shdr_probe(self):
        """ Connect the mocked SHDR device. """
        data = {
            "type": "shdr",
            "host": self.asset_uuid.lower(),
            "port": 7878,
            "data": {
                "probe": {
                    "tag": "Probe",
                    "type": "Events"
                }
            }
        }
        connector_schema = SHDRConnectorSchema(**data)
        shdr_device = Device(uuid='SHDR-PROBE', connector=connector_schema)
        self.shdr_connector.deploy(device=shdr_device, yaml_config_file="")
        register_device_connector(shdr_device, self.ksql)

    def deconnect_shdr_probe(self):
        """ Deconnect the mocked SHDR device. """
        self.shdr_asset.close()
        self.logger.info("Deconnect SHDR Probe")
        self.shdr_connector.tear_down(device_uuid="SHDR-PROBE")
        deregister_device_connector(device_uuid="SHDR-PROBE", bootstrap_servers=self.bootstrap_servers)

    def on_opcua_probe_event(self, msg_key, msg_value):
        """ Gather latency data for OPCUA device. """

        # Current time
        now = current_timestamp()

        # Extract timestamp from message
        device_ts = msg_value['VALUE']
        ingestion_ts = msg_value['attributes']['ingestion_timestamp']
        kafka_ts = msg_value['attributes']['kafka_timestamp']
        forwarder_ts = msg_value['attributes']['asset_forwarder_timestamp']

        # Compute time difference in seconds
        now_time = datetime.fromisoformat(now.replace('Z', '+00:00'))
        device_time = datetime.fromisoformat(device_ts.replace('Z', '+00:00'))
        ingestion_time = datetime.fromisoformat(ingestion_ts.replace('Z', '+00:00'))
        kafka_time = datetime.fromisoformat(kafka_ts.replace('Z', '+00:00'))
        forwarder_time = datetime.fromisoformat(forwarder_ts.replace('Z', '+00:00'))

        end_to_end_latency = (now_time - device_time).total_seconds()
        opcua_gateway_latency = (kafka_time - ingestion_time).total_seconds()
        kafka_latency = (forwarder_time - kafka_time).total_seconds()
        fan_out_layer_latency = (now_time - forwarder_time).total_seconds()

        # Append as dict to list
        self.opcua_latency_data.append(
            {
                'opcua_end_to_end_latency': end_to_end_latency,
                'opcua_gateway_latency': opcua_gateway_latency,
                'opcua_kafka_latency': kafka_latency,
            }
        )

        self.logger.debug(
            f"OPCUA end-to-end latency={end_to_end_latency:.3f}s, "
            f"OPCUA Gateway latency={opcua_gateway_latency:.3f}s, "
            f"Kafka latency={kafka_latency:.3f}s, "
            f"Fan-out latency={fan_out_layer_latency:.3f}s, "
        )

    def on_shdr_probe_event(self, msg_key, msg_value):
        """ Gather latency data for SHDR device. """

        # Current time
        now = current_timestamp()

        # Extract timestamp from message
        device_ts = msg_value['VALUE']
        ingestion_ts = msg_value['attributes']['ingestion_timestamp']
        kafka_ts = msg_value['attributes']['kafka_timestamp']
        forwarder_ts = msg_value['attributes']['asset_forwarder_timestamp']

        # Compute time difference in seconds
        now_time = datetime.fromisoformat(now.replace('Z', '+00:00'))
        device_time = datetime.fromisoformat(device_ts.replace('Z', '+00:00'))
        ingestion_time = datetime.fromisoformat(ingestion_ts.replace('Z', '+00:00'))
        kafka_time = datetime.fromisoformat(kafka_ts.replace('Z', '+00:00'))
        forwarder_time = datetime.fromisoformat(forwarder_ts.replace('Z', '+00:00'))

        end_to_end_latency = (now_time - device_time).total_seconds()
        shdr_gateway_latency = (kafka_time - ingestion_time).total_seconds()
        kafka_latency = (forwarder_time - kafka_time).total_seconds()
        fan_out_layer_latency = (now_time - forwarder_time).total_seconds()

        # Append as dict to list
        self.shdr_latency_data.append(
            {
                'shdr_end_to_end_latency': end_to_end_latency,
                'shdr_gateway_latency': shdr_gateway_latency,
                'shdr_kafka_latency': kafka_latency,
            }
        )

        self.logger.debug(
            f"SHDR end-to-end latency={end_to_end_latency:.3f}s, "
            f"SHDR Gateway latency={shdr_gateway_latency:.3f}s, "
            f"Kafka latency={kafka_latency:.3f}s, "
            f"Fan-out latency={fan_out_layer_latency:.3f}s, "
        )

    def on_probe_event(self, msg_key, msg_value):
        """ Gather latency data for OpenFactoryApp attribute. """

        # Current time
        now = current_timestamp()

        # Extract timestamp from message
        attribute_ts = msg_value['VALUE']
        app_ts = msg_value['attributes']['timestamp']
        kafka_ts = msg_value['attributes']['kafka_timestamp']
        forwarder_ts = msg_value['attributes']['asset_forwarder_timestamp']

        # Compute time difference in seconds
        now_time = datetime.fromisoformat(now.replace('Z', '+00:00'))
        attribute_time = datetime.fromisoformat(attribute_ts.replace('Z', '+00:00'))
        app_time = datetime.fromisoformat(app_ts.replace('Z', '+00:00'))
        kafka_time = datetime.fromisoformat(kafka_ts.replace('Z', '+00:00'))
        forwarder_time = datetime.fromisoformat(forwarder_ts.replace('Z', '+00:00'))

        end_to_end_latency = (now_time - attribute_time).total_seconds()
        ksqldb_latency = (app_time - attribute_time).total_seconds()
        ingestion_latency = (kafka_time - app_time).total_seconds()
        kafka_latency = (forwarder_time - kafka_time).total_seconds()
        fan_out_layer_latency = (now_time - forwarder_time).total_seconds()

        # Append as dict to list
        self.latency_data.append(
            {
                'app_ts': app_ts,
                'now': now,
                'end_to_end_latency': end_to_end_latency,
                'ksqldb_latency': ksqldb_latency,
                'ingestion_latency': ingestion_latency,
                'kafka_latency': kafka_latency,
                'fan_out_layer_latency': fan_out_layer_latency,
            }
        )

        self.logger.debug(
            f"End-to-end latency={end_to_end_latency:.3f}s, "
            f"Ksqldb latency={ksqldb_latency:.3f}s, "
            f"Ingestion latency={ingestion_latency:.3f}s, "
            f"Kafka latency={kafka_latency:.3f}s, "
            f"Fan-out latency={fan_out_layer_latency:.3f}s, "
        )

    def update_metrics(self):
        """ Update metrics """
        self.logger.debug("Gathering metrics")
        unavailable_assets = len(self.ofa.unavailable_assets_uuid())
        available_assets = len(self.ofa.available_assets_uuid())
        deployed_assets = len(self.ofa.assets_uuid())
        self.unavailable_assets = unavailable_assets
        self.available_assets = available_assets
        self.deployed_assets = deployed_assets
        metrics.UNAVAILABLE_ASSETS.set(unavailable_assets)
        metrics.AVAILABLE_ASSETS.set(available_assets)
        metrics.DEPLOYED_ASSETS.set(deployed_assets)

        self.metrics_last_update = current_timestamp()

        if self.latency_data:
            app_attribute_end_to_end_latency = statistics.mean([x['end_to_end_latency'] for x in self.latency_data])
            ksqldb_latency = statistics.mean([x['ksqldb_latency'] for x in self.latency_data])
            ingestion_latency = statistics.mean([x['ingestion_latency'] for x in self.latency_data])
            kafka_latency = statistics.mean([x['kafka_latency'] for x in self.latency_data])
            fan_out_layer_latency = statistics.mean([x['fan_out_layer_latency'] for x in self.latency_data])

            self.app_attribute_end_to_end_latency = app_attribute_end_to_end_latency
            self.ksqldb_latency = ksqldb_latency
            self.ingestion_latency = ingestion_latency
            self.kafka_latency = kafka_latency
            self.fan_out_layer_latency = fan_out_layer_latency

            metrics.APP_END_TO_END_LATENCY.set(app_attribute_end_to_end_latency)
            metrics.INGESTION_LATENCY.set(ingestion_latency)
            metrics.KAFKA_LATENCY.set(kafka_latency)
            metrics.KSQLLATENCY.set(ksqldb_latency)
            metrics.FAN_OUT_LAYER_LATENCY.set(fan_out_layer_latency)

        if self.cmd_latency_data:
            app_cmd_end_to_end_latency = statistics.mean([x['cmd_end_to_end_latency'] for x in self.cmd_latency_data])
            self.app_cmd_end_to_end_latency = app_cmd_end_to_end_latency

        if self.shdr_latency_data:
            shdr_end_to_end_latency = statistics.mean([x['shdr_end_to_end_latency'] for x in self.shdr_latency_data])
            shdr_gateway_latency = statistics.mean([x['shdr_gateway_latency'] for x in self.shdr_latency_data])
            shdr_kafka_latency = statistics.mean([x['shdr_kafka_latency'] for x in self.shdr_latency_data])
            self.shdr_end_to_end_latency = shdr_end_to_end_latency
            self.shdr_gateway_latency = shdr_gateway_latency
            self.shdr_kafka_latency = shdr_kafka_latency

            metrics.SHDR_LATENCY.set(shdr_end_to_end_latency)
            metrics.SHDR_GATEWAY_LATENCY.set(shdr_gateway_latency)
            metrics.SHDR_KAFKA_LATENCY.set(shdr_kafka_latency)

        if self.opcua_latency_data:
            opcua_end_to_end_latency = statistics.mean([x['opcua_end_to_end_latency'] for x in self.opcua_latency_data])
            opcua_gateway_latency = statistics.mean([x['opcua_gateway_latency'] for x in self.opcua_latency_data])
            opcua_kafka_latency = statistics.mean([x['opcua_kafka_latency'] for x in self.opcua_latency_data])
            self.opcua_end_to_end_latency = opcua_end_to_end_latency
            self.opcua_gateway_latency = opcua_gateway_latency
            self.opcua_kafka_latency = opcua_kafka_latency

            metrics.OPCUA_LATENCY.set(opcua_end_to_end_latency)
            metrics.OPCUA_GATEWAY_LATENCY.set(opcua_gateway_latency)
            metrics.OPCUA_KAFKA_LATENCY.set(opcua_kafka_latency)

        self.latency_data = []
        self.cmd_latency_data = []
        self.opcua_latency_data = []
        self.shdr_latency_data = []

    async def async_main_loop(self):

        if self.shdr_connector:
            self.logger.info('Starting SHDR Connector monitoring')
            asyncio.create_task(self.shdr.start())
        if self.opcua_connector:
            self.logger.info('Starting OPCUA Connector monitoring')
            asyncio.create_task(self.opcua.start())
        last_metrics_update = 0

        while True:
            now = time.monotonic()

            if now - last_metrics_update >= self.METRICS_UPDATE_INTERVAL:
                self.update_metrics()
                last_metrics_update = now

            now_ofa = current_timestamp()
            self.probe_event = now_ofa
            self.method('probe_cmd', sender_uuid=self.asset_uuid, args=[('probe', now_ofa)])

            await asyncio.sleep(1)

    def app_event_loop_stopped(self):
        """ Shutdown operations. """
        if self.shdr_connector:
            self.deconnect_shdr_probe()
        if self.opcua_connector:
            self.deconnect_opcua_probe()


app = OpenFactoryMonitorApp(
    ksqlClient=KSQLDBClient(os.getenv("KSQLDB_URL", "http://localhost:8088")),
    bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
    loglevel=os.getenv("LOG_LEVEL", "INFO")
)

app.run()
