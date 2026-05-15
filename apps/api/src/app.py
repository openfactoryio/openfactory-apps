import os
from openfactory.apps import OpenFactoryFastAPIApp
from openfactory.kafka import KSQLDBClient
from endpoints import router


class OpenFactoryAPIApp(OpenFactoryFastAPIApp):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # expose OFA app inside FastAPI
        self.api.state.ofa_app = self

        # include router
        self.api.include_router(router)


app = OpenFactoryAPIApp(
    ksqlClient=KSQLDBClient(os.getenv("KSQLDB_URL", "http://localhost:8088")),
    bootstrap_servers=os.getenv("KAFKA_BROKER", "localhost:9092"),
    loglevel=os.getenv("LOG_LEVEL", "INFO")
)

app.run()
