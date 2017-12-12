import subprocess
import uuid
import os
import hashlib
import pycurl
from io import BytesIO

from bson import ObjectId
from flask import Blueprint, request, current_app, jsonify, url_for, \
    make_response
from urllib.parse import urlparse
from os.path import splitext, basename
from furl import furl


import exc
from extensions import fs
from tasks import video_converter

mod = Blueprint('views', __name__)


def md5sum(string):
    m = hashlib.md5()
    m.update(string.encode('utf-8'))
    return m.hexdigest()


def check_url_file(url):
    buffer = BytesIO()

    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.HEADER, True)
    c.setopt(c.NOBODY, True)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()

    response_code = c.getinfo(c.RESPONSE_CODE)
    # total_time = c.getinfo(c.TOTAL_TIME)
    c.close()

    if response_code == 404:
        raise exc.FileNotFoundException

    if response_code >= 400:
        raise exc.FileNotValidException


def save_video_from_url(url):
    check_url_file(url)

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
        cmd_download = 'wget --no-check-certificate -O {filepath} {url}'.format(
            filepath=source_filepath, url=url)
        # print(cmd_download)

        download_process = subprocess.Popen(
            cmd_download,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True)
        download_process_result = download_process.communicate()
        if ' failed: ' in download_process_result[0].decode('iso-8859-1'):
            raise exc.FileNotDownloadException

    return source_filepath


def save_video_from_form(file):
    orig_filename, file_ext = splitext(basename(file.filename))
    saved_filename = str(uuid.uuid4()) + file_ext
    source_filepath = current_app.config['MEDIA_FOLDER'] + saved_filename
    file.save(source_filepath)
    return source_filepath


def get_webhook(webhook_encode):
    if not webhook_encode:
        raise exc.WebhookRequiredException

    webhook = furl(webhook_encode)
    webhook_path = webhook.origin + webhook.pathstr.rstrip('/')
    if webhook_path not in current_app.config['WEB_HOOKS']:
        raise exc.WebhookNotValidException

    return webhook


@mod.route('/upload', methods=['GET', 'POST'])
def get_video():
    if request.method == 'POST':
        # ----------------------------------
        # ---------- POST METHOD -----------
        # ----------------------------------
        if 'file' not in request.files:
            return jsonify({'error': '`file` key not found in form data'}), 400

        webhook = get_webhook(request.form.get('webhook'))

        watermark = request.form.get('watermark')
        if watermark and watermark not in ['tr', 'tl', 'br', 'bl']:
            raise exc.WatermarkIsNotValidException

        filename = save_video_from_form(request.files['file'])
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
            raise exc.WatermarkIsNotValidException

        filename = save_video_from_url(url)

    task = video_converter.apply_async(kwargs=dict(
        input_file=filename,
        watermark=watermark,
        client_ip=request.remote_addr,
        webhook=webhook.url
    ))

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


@mod.route('/pull/<file_id>')
def pull_file(file_id):
    if current_app.config['ONLY_PULL_FROM_SERVER_HOST'] and \
                    current_app.config['SERVER_HOST'] != request.host:
        raise exc.ServerHostIsNotValidException

    key = request.args.get('key')
    if not key:
        return jsonify({'error': '`key` argument is requirement'}), 400

    grid_out = fs.find_one({'_id': ObjectId(file_id), 'key': key})
    if grid_out is None:
        raise exc.FileNotFoundException

    response = make_response(grid_out.read())
    mimtype_dict = {
        'video': 'video/mp4',
        'screenshot': 'image/jpeg'
    }
    response.mimetype = mimtype_dict[grid_out._file['type']]
    response.headers['Content-Disposition'] = 'attachment'

    return response
