import subprocess
import uuid
import os
import hashlib
from bson.errors import InvalidId

from bson.objectid import ObjectId
from flask import Blueprint, request, current_app, jsonify, url_for, \
    make_response
from urllib.parse import urlparse
from os.path import splitext, basename
from gridfs import NoFile

from exception import LargeFileException, FileSizeException
from extensions import fs
from tasks import video_converter

mod = Blueprint('views', __name__)


def md5sum(string):
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()


def check_url_file_size(url):
    cmd_check_file_size = "wget --spider " + url + " 2>&1 | awk '/Length/ {print $2}'; exit 0"
    try:
        file_size = int(subprocess.check_output(cmd_check_file_size,
                                                stderr=subprocess.STDOUT,
                                                shell=True))
    except ValueError:
        raise FileSizeException

    if file_size > current_app.config['MAX_CONTENT_LENGTH']:
        raise LargeFileException

    return file_size


def save_video_from_url(url):
    check_url_file_size(url)

    md5sum(url)
    disassembled = urlparse(url)
    orig_filename, file_ext = splitext(basename(disassembled.path))

    file_exists = False
    if current_app.config['URL_CACHE']:
        saved_filename = md5sum(url) + file_ext
        source_filepath = current_app.config['MEDIA_FOLDER'] + saved_filename
        if os.path.isfile(source_filepath):
            file_exists = True
    else:
        saved_filename = str(uuid.uuid4()) + file_ext

    source_filepath = current_app.config['MEDIA_FOLDER'] + saved_filename

    if not file_exists:
        cmd_download_video = 'wget --no-check-certificate -O {filepath} {url}'.format(
            filepath=source_filepath, url=url)
        print(cmd_download_video)
        subprocess.Popen(cmd_download_video, shell=True).communicate()
    return source_filepath


def save_video_from_form(file):
    orig_filename, file_ext = splitext(basename(file.filename))
    saved_filename = str(uuid.uuid4()) + file_ext
    source_filepath = current_app.config['MEDIA_FOLDER'] + saved_filename
    file.save(source_filepath)
    return source_filepath


@mod.route('/upload', methods=['GET', 'POST'])
def get_video():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': '`file` key not found in form data'})

        filename = save_video_from_form(request.files['file'])
    else:
        url = request.args.get('url')
        if not url:
            return jsonify({'error': '`url` parameter required'})

        disassembled = urlparse(url)
        orig_filename, file_ext = splitext(basename(disassembled.path))
        if not file_ext:
            return jsonify({'error': '`file extension` is not valid'}), 400

        filename = save_video_from_url(url)

    # task = video_converter(filename)
    task = video_converter.apply_async(args=[filename])
    return jsonify(
        {'filename': filename,
         'task_id': task.task_id
         }), 202, {
               'X-Progress': url_for('views.task_status',
                                     task_id=task.task_id,
                                     _external=True)
           }


@mod.route('/status/<task_id>')
def task_status(task_id):
    task = video_converter.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'percent': 0,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'percent': task.info.get('percent', 0),
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'percent': 1,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)


@mod.route('/pull/<file_id>')
def pull_file(file_id):
    try:
        file = fs.get(ObjectId(file_id))
    except (InvalidId, NoFile):
        return jsonify({'error': 'File not found'}), 404

    response = make_response(file.read())
    response.mimetype = 'video/mp4'
    response.headers['Content-Disposition'] = 'attachment'

    fs.delete(ObjectId(file_id))

    return response
