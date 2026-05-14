"""
Routes for File Manager Blueprint
"""
import os
import datetime
from html import unescape
from flask_login import login_required
from flask import render_template, request, redirect, url_for, send_from_directory, flash, current_app, session
from ...config import Config
from ..core.hal import cnc
from . import file_manager_blueprint


@file_manager_blueprint.route('/')
@login_required
def index():
    if 'current_folder' not in session:
        session['current_folder'] = Config.NC_FILES_FOLDER
    current_folder = session.get('current_folder')
    files = []
    if current_folder == Config.NC_FILES_FOLDER:
        folders = []
    else:
        folders = [{'foldername': '..', 'created': ''}]
    for filename in os.listdir(current_folder):
        file_path = os.path.join(current_folder, filename)
        if os.path.isfile(file_path):
            file_info = {
                'filename': filename,
                'size': os.path.getsize(file_path),
                'modified': datetime.datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            }
            files.append(file_info)
        elif os.path.isdir(file_path):
            folder_info = {
                'foldername': filename,
                'created': datetime.datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
            }
            folders.append(folder_info)

    selected_file = request.args.get('file')

    return render_template('file_manager/filesBase.html',
                           current_folder='nc-files://' + os.path.relpath(current_folder, Config.NC_FILES_FOLDER),
                           folders=folders,
                           files=files,
                           selected_file=selected_file,
                           title='File manager home')


@file_manager_blueprint.route('/open_folder', methods=['POST'])
@login_required
def open_folder():
    new_folder = request.form.get('selected_folder_open')
    if new_folder:
        if new_folder == '..':
            session['current_folder'] = os.path.dirname(session['current_folder'])
        else:
            session['current_folder'] = os.path.join(session['current_folder'], new_folder)
        return redirect(url_for('files.index'))
    else:
        return '', 204


@file_manager_blueprint.route('/make_folder', methods=['POST'])
@login_required
def make_folder():
    new_folder = request.form.get('newFolderName')
    os.makedirs(os.path.join(session['current_folder'], new_folder))
    return redirect(url_for('files.index'))


@file_manager_blueprint.route('/delete_folder', methods=['POST'])
@login_required
def delete_folder():
    folder = request.form.get('selected_folder_delete')
    if folder:
        folder_path = os.path.join(session['current_folder'], folder)
        if len(os.listdir(folder_path)) == 0:
            os.rmdir(folder_path)
            flash(f"Folder '{folder}' removed", 'success')
        else:
            flash("Folder is not empty", 'danger')

    return redirect(url_for('files.index'))


@file_manager_blueprint.route('/load', methods=['POST'])
@login_required
def load_file():
    selected_file = request.form.get('selected_file_load')
    if selected_file:
        current_app.nc_file = os.path.join(session['current_folder'], selected_file)
        cnc.load_nc_file(current_app.nc_file)
        return redirect(url_for('cnc.index'))
    else:
        return '', 204


@file_manager_blueprint.route('/get_file_content/<filename>')
def get_file_content(filename):
    try:
        # Read the file content
        with open(os.path.join(session['current_folder'], filename), 'r') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return 'File not found', 404


@file_manager_blueprint.route('/edit', methods=['POST'])
@login_required
def edit_file():
    selected_file = request.form.get('selected_file_edit')
    if selected_file:
        with open(os.path.join(session['current_folder'], selected_file), 'r') as file:
            content = file.read()
        return render_template('file_manager/fileEdit.html',
                               selected_file=selected_file,
                               content=content,
                               title='Edit ' + selected_file)
    else:
        return '', 204


@file_manager_blueprint.route('/save/<filename>', methods=['POST'])
@login_required
def save_file(filename):
    content = request.form.get('file_content')
    with open(os.path.join(session['current_folder'], filename), 'w', newline='\n') as file:
        file.write(unescape(content).replace('\r', ''))
        flash(f"File '{filename}' saved", 'success')
    return redirect(url_for('files.index'))


@file_manager_blueprint.route('/upload', methods=['POST'])
@login_required
def upload_file():
    # Handle file upload
    if 'file' not in request.files:
        flash('No file part.', 'danger')
        return redirect(url_for('files.index'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file.', 'danger')
        return redirect(url_for('files.index'))

    file.save(os.path.join(session['current_folder'], file.filename))
    return redirect(url_for('files.index'))


@file_manager_blueprint.route('/download/', methods=['POST'])
@login_required
def download_file():
    selected_file = request.form.get('selected_file')
    if selected_file:
        os.path.join(session['current_folder'], selected_file)
        return send_from_directory(session['current_folder'], selected_file, as_attachment=True)
    else:
        return '', 204


@file_manager_blueprint.route('/delete/', methods=['POST'])
@login_required
def delete_file():
    selected_file = request.form.get('selected_file')
    if selected_file:
        filepath = os.path.join(session['current_folder'], selected_file)
        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f"File '{selected_file}' removed", 'success')
    return redirect(url_for('files.index'))
