import asyncio
import json
import threading
import time
from flask import Response
from openfactory.assets import Asset


# SSE generator
def event_stream(queue):
    while True:
        data = queue.get()
        yield f"data: {json.dumps(data)}\n\n"


# Thread function to fetch CNC status
def start_async_stream(queue, ksql, app):

    def format_numbers(value):
        try:
            # Attempt to convert to float and format as +XX.XXX
            return f"{float(value):+7.3f}"
        except ValueError:
            # Return value as-is for non-numerical entries
            return value

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    while True:
        from ..models.cncsettings import CNCSettings
        with app.app_context():
            uuid = CNCSettings.query.filter_by(key="cnc_uuid").first()

        if uuid is None:
            return

        cnc = Asset(asset_uuid=uuid.value, ksqlClient=ksql)

        # get all samples
        state = cnc.samples()

        # build a dictionnary
        dic = {
            item['ID']: format_numbers(item['VALUE'])
            for item in state
            if item['VALUE'] != "UNAVAILABLE"
        }

        # add tool_id
        tool_id = cnc.tool_id.value
        if tool_id != "UNAVAILABLE":
            dic['tool_id'] = tool_id

        # adds line in case does not exist (or was UNAVAILABLE)
        dic.setdefault('line', 0)

        queue.put(dic)
        time.sleep(0.3)


def init_state_streaming_thread(app, ksql):
    """
    Initialize the streaming thread and attach SSE route to Flask app
    """

    print('Starting state stream listening')

    from queue import Queue
    queue = Queue()

    # Start the async streaming thread
    thread = threading.Thread(target=start_async_stream, args=(queue, ksql, app))
    thread.daemon = True
    thread.start()

    # Attach the SSE route to the app
    @app.route('/state')
    def state():
        return Response(
            event_stream(queue),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
