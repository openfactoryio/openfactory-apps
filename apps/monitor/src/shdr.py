import asyncio
import logging
from openfactory.assets.utils.time_methods import current_timestamp


class SHDRServer:
    """
    Simple mocke SHDR device to serve as probe.

    The server listens for TCP connections and periodically sends
    SHDR-formatted observations to connected clients.
    """

    def __init__(self, logger: logging.Logger, host: str = "0.0.0.0", port: int = 7878,):
        """
        Initialize the SHDR server.

        Args:
            logger: Logger used to report server activity.
            host: Host interface on which to listen.
            port: TCP port on which to listen.
        """
        self.logger = logger
        self.host = host
        self.port = port

    async def start(self):
        """ Start the SHDR server and serve clients indefinitely. """
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )

        self.logger.info(f"SHDR server listening on {self.host}:{self.port}")

        async with server:
            await server.serve_forever()

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """
        Handle a connected SHDR client.

        Periodically sends mock SHDR observations until the client
        disconnects.

        Args:
            reader: Stream used to receive data from the client.
            writer: Stream used to send data to the client.
        """
        peer = writer.get_extra_info("peername")
        self.logger.info(f"SHDR client connected: {peer}")
        try:
            while True:
                ts = current_timestamp()
                writer.write(f"{ts}|probe|{ts}\n".encode())
                await writer.drain()
                await asyncio.sleep(1)

        except (
            ConnectionResetError,
            BrokenPipeError,
            ConnectionAbortedError,
        ):
            self.logger.info(f"SHDR client disconnected: {peer}")

        finally:
            writer.close()
