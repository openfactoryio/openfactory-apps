from ..conditions_stream import clients


def msg(msg, category):
    data = {
        "msg": msg,
        "level": category
    }
    print("data to put", data)

    # broadcast to all connected clients
    for client_queue in clients:
        try:
            print("sending")
            client_queue.put_nowait(data)
        except Exception as e:
            print("Queue error:", str(e))
