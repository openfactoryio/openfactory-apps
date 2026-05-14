import json
import re
import sys
import queue

from flask import Response
from queue import Empty
from openfactory.assets import Asset


# connected SSE clients
clients = []


def event_stream(client_queue):
    """
    SSE generator:
     - Streams queue data to one connected client
     - Sends keepalive packets when idle
     - Cleans up disconnected clients
    """

    # initial packet
    yield "data: {}\n\n"

    try:
        while True:
            try:
                data = client_queue.get(timeout=5)

                print('Got it and need to update page now:', data)

                yield f"data: {json.dumps(data)}\n\n"

            except Empty:
                # keepalive packet
                yield "data: {}\n\n"

            sys.stdout.flush()

    except GeneratorExit:
        # browser disconnected
        print("Client disconnected")

    finally:
        # cleanup queue
        if client_queue in clients:
            clients.remove(client_queue)


def broadcast_condition(msg_key, msg_value):
    """
    Broadcast condition to all connected clients
    """

    print(f"[{msg_key}] {msg_value}")

    level = re.sub(r"^\{.*?\}", "", msg_value['TAG']).lower()

    data = {
        "msg": f"{msg_value['id']}: {msg_value['VALUE']}",
        "level": level
    }

    print(f"[{level}] {data}")

    # broadcast to all connected clients
    for client_queue in clients.copy():
        try:
            client_queue.put_nowait(data)
        except Exception as e:
            print("Queue error:", str(e))


def init_error_streaming_thread(app, ksql):
    """
    Initialize SSE error streaming
    """

    print('Starting error stream listening')

    # Subscribe to CNC conditions
    from ..models.cncsettings import CNCSettings

    with app.app_context():
        setting = CNCSettings.query.filter_by(key="cnc_uuid").first()

    if setting is None:
        print("No CNC UUID configured")
        return

    cnc = Asset(asset_uuid=setting.value, ksqlClient=ksql)
    cnc.subscribe_to_conditions(broadcast_condition)

    # SSE route
    @app.route('/error')
    def error():

        # dedicated queue per client
        client_queue = queue.Queue()

        clients.append(client_queue)

        return Response(
            event_stream(client_queue),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
