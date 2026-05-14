"""
Routes for CNC Blueprint
"""
import os
from flask_login import login_required
from flask import render_template, request, redirect, url_for, current_app
from . import cnc_blueprint
from ..core.hal import cnc
from .core import msg


@cnc_blueprint.route('/')
@login_required
def index():
    loaded_nc_file = {
        'name': None,
        'content': ''
    }
    if current_app.nc_file:
        loaded_nc_file['name'] = os.path.basename(current_app.nc_file)
        try:
            # Read the file content
            with open(current_app.nc_file, 'r') as file:
                loaded_nc_file['content'] = file.read()
        except FileNotFoundError:
            return 'nc-File not found', 404

    return render_template('cnc/cncBase.html',
                           title='CNC home',
                           nc_file=loaded_nc_file)


@cnc_blueprint.route('/home_cycle', methods=['POST'])
@login_required
def home_cycle():
    ret = cnc.home_cycle()
    if ret == "OK":
        msg('Started homing cycle', "success")
    else:
        msg(ret, "fault")
    return '', 204


@cnc_blueprint.route('/zprobe', methods=['POST'])
@login_required
def zprobe():
    ret = cnc.zprobe()
    if ret == "OK":
        msg('Started zero finding', "success")
    else:
        msg(ret, "fault")
    return '', 204


@cnc_blueprint.route('/clear_offsets', methods=['POST'])
@login_required
def clear_offsets():
    ret = cnc.clear_offsets()
    if ret == "OK":
        msg('Started zero finding', "success")
    else:
        msg(ret, "fault")
    return '', 204


@cnc_blueprint.route('/connect', methods=['POST'])
@login_required
def connect():
    ret = cnc.connect()
    if ret == "OK":
        msg('Connecting to CNC', "success")
    else:
        msg(ret, "fault")
    return '', 204


@cnc_blueprint.route('/kill_alarm', methods=['POST'])
@login_required
def kill_alarm():
    ret = cnc.kill_alarm()
    if ret == "OK":
        msg('Unlocking alarm state. Caution ! Motion unlocked', "warning")
    else:
        msg(ret, "fault")
    return '', 200


@cnc_blueprint.route('/gcode_run', methods=['POST'])
@login_required
def gcode_run():
    gcode = request.form.get('gcode')
    ret = cnc.gcode(gcode)
    if ret == "OK":
        msg(f"Sent '{gcode}' to CNC", 'normal')
    else:
        msg(ret, "fault")
    return redirect(url_for('cnc.index'))


@cnc_blueprint.route('/start_cycle', methods=['POST'])
@login_required
def start_cycle():
    ret = cnc.start_cycle(current_app.nc_file)
    if ret == "OK":
        msg('Start cycle', "normal")
    else:
        msg(ret, "fault")
    return redirect(url_for('cnc.index'))


@cnc_blueprint.route('/feed_hold')
@login_required
def feed_hold():
    ret = cnc.feed_hold()
    if ret == "OK":
        msg('Feed hold', "normal")
    else:
        msg(ret, "fault")
    return '', 204


@cnc_blueprint.route('/resume')
@login_required
def resume():
    ret = cnc.resume()
    if ret == "OK":
        msg('Resume', "normal")
    else:
        msg(ret, "fault")
    return redirect(url_for('cnc.index'))


@cnc_blueprint.route('/tool_id', methods=['POST'])
@login_required
def tool_id():
    tool_id = request.form.get('tool_id')
    ret = cnc.tool_id(tool_id)
    if ret == "OK":
        msg(f"Set '{tool_id}'", 'normal')
    else:
        msg(ret, "fault")
    return redirect(url_for('cnc.index'))
