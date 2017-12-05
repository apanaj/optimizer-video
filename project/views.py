import subprocess
import uuid
import os
import hashlib

from flask import Blueprint, request, current_app, jsonify, url_for, \
    make_response
from urllib.parse import urlparse
from os.path import splitext, basename
from furl import furl

from exception import LargeFileException, FileSizeException, \
    WebhookRequiredException, WebhookNotValidException
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
    ## its not necessary
    # check_url_file_size(url)

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


def get_webhook(webhook_encode):
    if not webhook_encode:
        raise WebhookRequiredException

    webhook = furl(webhook_encode)
    webhook_path = webhook.origin + webhook.pathstr
    if webhook_path not in current_app.config['WEB_HOOKS']:
        raise WebhookNotValidException

    return webhook


@mod.route('/upload', methods=['GET', 'POST'])
def get_video():
    if request.method == 'POST':
        # ----------------------------------
        # ---------- POST METHOD -----------
        # ----------------------------------
        if 'file' not in request.files:
            return jsonify({'error': '`file` key not found in form data'}), 400
        filename = save_video_from_form(request.files['file'])

        webhook = get_webhook(request.form.get('webhook'))

        watermark = request.form.get('watermark')
        if watermark and watermark not in ['tr', 'tl', 'br', 'bl']:
            return jsonify({'error': '`watermark` is not valid'}), 400
    else:
        # ----------------------------------
        # ----------- GET METHOD -----------
        # ----------------------------------
        url = furl(request.args.get('url')).url
        if not url:
            return jsonify({'error': '`url` parameter required'}), 400

        webhook = get_webhook(request.args.get('webhook'))

        watermark = request.args.get('watermark')
        if watermark and watermark not in ['tr', 'tl', 'br', 'bl']:
            return jsonify({'error': '`watermark` is not valid'}), 400

        disassembled = urlparse(url)
        orig_filename, file_ext = splitext(basename(disassembled.path))
        if not file_ext:
            return jsonify({'error': '`file extension` is not valid'}), 400

        filename = save_video_from_url(url)

    task = video_converter.apply_async(args=[
        filename, watermark, request.remote_addr, webhook.url])
    return jsonify(
        {
            'status': 'ACCEPTED',
            'result': {
                'task_id': task.task_id,
                '_link': {
                    'progress': url_for('views.task_status',
                                        task_id=task.task_id,
                                        _external=True),
                }
            }
        }), 202


@mod.route('/status/<task_id>', methods=['HEAD'])
def task_status(task_id):
    task = video_converter.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'X-State': task.state,
            'X-Percent': 0,
            'X-Status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'X-State': task.state,
            'X-Percent': task.info.get('percent', 0),
            'X-Status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['X-Result'] = task.info['result']
    else:
        # something went wrong in the background job
        response = {
            'X-State': task.state,
            'X-Percent': 1,
            'X-Status': str(task.info),  # this is the exception raised
        }
    return '', 204, response


@mod.route('/pull/<task_id>')
def pull_file(task_id):
    key = request.args.get('key')
    if not key:
        return jsonify({'error': '`key` argument is requirement'}), 400

    file_type = request.args.get('type')
    if not file_type:
        return jsonify({'error': '`type` argument is requirement'}), 400

    file_type = file_type.lower()
    if file_type not in ['video', 'screenshot']:
        return jsonify({'error': '`type` is not valid'}), 400

    file = fs.find_one({'task_id': task_id, 'key': key, 'type': file_type})
    if file is None:
        return jsonify({'error': 'File not found'}), 404

    response = make_response(file.read())
    mimtype_dict = {
        'video': 'video/mp4',
        'screenshot': 'image/jpeg'
    }
    response.mimetype = mimtype_dict[file_type]
    response.headers['Content-Disposition'] = 'attachment'

    return response
