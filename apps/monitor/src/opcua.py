import asyncio
import logging
from openfactory.assets.utils.time_methods import current_timestamp
from asyncua import Server
from asyncua.common.node import Node
from asyncua.common.callback import CallbackType
from asyncua.common.callback import ServerItemCallback


class OPCUAServer:
    """
    Simple mock OPC UA device to serve as probe.

    The server exposes a single OPC UA variable named ``Probe`` whose
    value is updated every second with the current timestamp.

    Expose address space:
        Objects
        └── ProbeObject
            └── Probe    (String)
    """

    def __init__(self, logger: logging.Logger, opcua_endpoint: str = "opc.tcp://0.0.0.0:4840"):
        """
        Initialize the OPC UA server.

        Args:
            logger: Logger used to report server activity.
            opcua_endpoint: OPC UA endpoint on which to listen.
        """
        self.logger = logger
        self.opcua_endpoint = opcua_endpoint

        self.server: Server = Server()
        self.probe: Node | None = None

    def on_subscription_created(self, event: ServerItemCallback, _):
        """ Called when a monitored item is created. """
        self.logger.info(
            "[OPC UA Probe] Monitored item created "
            "(external=%s)\n"
            "    request=%r\n"
            "    response=%r",
            event.is_external,
            event.request_params,
            event.response_params,
        )

    def on_subscription_deleted(self, event: ServerItemCallback, _):
        """ Called when a monitored item is deleted. """
        self.logger.info(
            "[OPC UA Probe] Monitored item deleted "
            "(external=%s)\n"
            "    request=%r\n"
            "    response=%r",
            event.is_external,
            event.request_params,
            event.response_params,
        )

    def on_subscription_modified(self, event: ServerItemCallback, _):
        """ Called when a monitored item is modified. """
        self.logger.info(
            "[OPC UA Probe] Monitored item modified "
            "(external=%s)\n"
            "    request=%r\n"
            "    response=%r",
            event.is_external,
            event.request_params,
            event.response_params,
        )

    async def start(self) -> None:
        """
        Start the OPC UA server and serve clients indefinitely.
        """
        self.logger.info("[OPC UA Probe] Creating OpenFactory OPC UA Server")
        await self.server.init()

        # Register diagnostic callbacks
        self.server.subscribe_server_callback(
            CallbackType.ItemSubscriptionCreated,
            self.on_subscription_created,
        )

        self.server.subscribe_server_callback(
            CallbackType.ItemSubscriptionDeleted,
            self.on_subscription_deleted,
        )

        self.server.subscribe_server_callback(
            CallbackType.ItemSubscriptionModified,
            self.on_subscription_modified,
        )

        self.server.set_endpoint(self.opcua_endpoint)
        self.server.set_server_name("OpenFactory OPC UA Server")

        uri = "http://openfactory"
        idx = await self.server.register_namespace(uri)
        self.logger.info("[OPC UA Probe] Registered namespace %s (idx=%d)", uri, idx)

        objects = self.server.nodes.objects

        probe_object = await objects.add_object(idx, "ProbeObject")

        self.probe = await probe_object.add_variable(idx, "Probe", current_timestamp())
        self.logger.info("[OPC UA Probe] Created Probe variable")

        self.logger.info(f"[OPC UA Probe] OPC UA server listening on {self.opcua_endpoint}")

        async with self.server:
            self.logger.info("[OPC UA Probe] Accepting OPC UA connections")
            try:
                while True:
                    try:
                        await self.probe.write_value(current_timestamp())
                        self.logger.debug("[OPC UA Probe] Emitted a Probe event")
                    except Exception:
                        self.logger.exception("[OPC UA Probe] Failed to update Probe value")
                        raise
                    await asyncio.sleep(1)

            finally:
                self.logger.info("[OPC UA Probe] OpenFactory OPC UA Server stopping")
