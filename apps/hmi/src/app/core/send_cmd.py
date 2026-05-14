from ...db import ksql
from ...models.cncsettings import CNCSettings
from openfactory.assets import Asset


def send_cmd(cmd, args):
    """
    Send command to OpenFactory
    Returns OK on success or error message
    """
    uuid = CNCSettings.query.filter_by(key="sup_uuid").first()
    if not uuid:
        return "CNC SUPERVISOR UUID must be defined in settings"

    cnc = Asset(asset_uuid=uuid.value, ksqlClient=ksql)
    cnc.method(method=cmd, sender_uuid='CNC-HMI', args=args)
    print('sent cmd', cmd, args)

    return "OK"
