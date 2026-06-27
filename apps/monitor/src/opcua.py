import asyncio
import logging
from openfactory.assets.utils.time_methods import current_timestamp
from asyncua import Server
from asyncua.common.node import Node


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

    async def start(self) -> None:
        """
        Start the OPC UA server and serve clients indefinitely.
        """
        await self.server.init()

        self.server.set_endpoint(self.opcua_endpoint)
        self.server.set_server_name("OpenFactory OPC UA Server")

        uri = "http://openfactory"
        idx = await self.server.register_namespace(uri)

        objects = self.server.nodes.objects

        probe_object = await objects.add_object(idx, "ProbeObject")

        self.probe = await probe_object.add_variable(
            idx,
            "Probe",
            current_timestamp(),
        )

        self.logger.info(f"OPC UA server listening on {self.opcua_endpoint}")

        async with self.server:
            while True:
                await self.probe.write_value(current_timestamp())
                await asyncio.sleep(1)
