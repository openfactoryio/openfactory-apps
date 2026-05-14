import json
import time
import re
import queue
from flask import Response
from openfactory.assets import Asset


# list of queues of connected clients
clients = []


def event_stream(client_queue):
    """
    SSE generator for a specific client
    """
    try:
        while True:
            try:
                data = client_queue.get(timeout=10)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                yield ": keep-alive\n\n"
                time.sleep(0.1)
    finally:
        # Remove the client from the list on disconnect
        if client_queue in clients:
            clients.remove(client_queue)


def on_condition(msg_key, msg_value, client_queue):
    """
    Process new condition
    """
    level = re.sub(r"^\{.*?\}", "", msg_value['TAG']).lower()
    data = {
        "msg": f"{msg_value['id']}: {msg_value['VALUE']}",
        "level": level
    }

    # Broadcast message
    client_queue.put(data)


def init_conditions_streaming_thread(app, ksqlClient):
    """
    Initialize the streaming thread and attach SSE route to Flask app
    """

    print('Starting conditions stream listening')

    # Create CNC asset
    from ..models.cncsettings import CNCSettings
    with app.app_context():
        cnc_uuid = CNCSettings.query.filter_by(key="cnc_uuid").first()

    if cnc_uuid is None:
        return

    cnc = Asset(cnc_uuid.value, ksqlClient)

    # Attach the SSE route to the app
    @app.route('/conditions')
    def conditions():
        # create queue for connected client
        client_queue = queue.Queue()
        clients.append(client_queue)

        # get current condition of CNC and broadcast it
        motion_condition = next((item for item in cnc.conditions() if item['ID'] == 'motion'), None)
        if motion_condition:
            level = re.sub(r"^\{.*?\}", "", motion_condition['TAG']).lower()
            data = {
                "msg": f"motion: {motion_condition['VALUE']}",
                "level": level
            }
            client_queue.put(data)

        # subscribe to asset conditions
        cnc.subscribe_to_conditions(lambda msg_key, msg_value: on_condition(msg_key, msg_value, client_queue))

        return Response(
            event_stream(client_queue),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
