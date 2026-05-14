from ...models.cncsettings import CNCSettings
from .send_cmd import send_cmd


class HAL:
    """
    Hardware abstraction layer
    """

    def home_cycle(self):
        print("Homing...")
        return send_cmd("home_cycle", [])

    def zprobe(self):
        probe_speed = CNCSettings.query.filter_by(key="probe_speed").first()
        probe_height = CNCSettings.query.filter_by(key="probe_height").first()
        z_rise = CNCSettings.query.filter_by(key="z_rise").first()

        if not probe_speed:
            return "Z-Probe speed must be defined in Z-Probe settings"
        if not probe_height:
            return "Z-Probe height must be defined in Z-Probe settings"
        if not z_rise:
            return "Z-Probe rise must be defined in Z-Probe settings"

        print("Z-Probe...")
        return send_cmd("zprobe", [("Input", f"{probe_speed.value} {probe_height.value} {z_rise.value}")])

    def clear_offsets(self):
        print("Clear offsets ...")
        return send_cmd("clear_offsets", [])

    def connect(self):
        port = CNCSettings.query.filter_by(key="cnc_port").first()
        if not port:
            return "USB port of CNC must be defined in settings"

        print("Connecting...")
        return send_cmd("connect", [("Input", port.value)])

    def kill_alarm(self):
        print("Unlock alarm state...")
        ret = send_cmd("kill_alarm", [])
        if not ret:
            ret + 'error'
        return ret

    def gcode(self, gcode):
        print("Sending g-code")
        return send_cmd("gcode", [("Input", gcode)])

    def load_nc_file(self, nc_file):
        print("Load nc-file", nc_file)
        return send_cmd("load_nc_file", [("Input", nc_file)])

    def start_cycle(self, nc_file):
        print("Sending start-cycle with nc-file", nc_file)
        return send_cmd("start_cycle", [("Input", nc_file)])

    def feed_hold(self):
        print("Feed hold")
        return send_cmd("feed_hold", [])

    def resume(self):
        print("Resume")
        return send_cmd("resume", [])

    def tool_id(self, tool_id):
        print("Set tool-id", tool_id)
        return send_cmd("set_tool_id", [("Input", tool_id.upper())])


cnc = HAL()
