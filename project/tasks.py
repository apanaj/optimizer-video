import string
import random
import calendar
import time
import subprocess
import re
import gridfs
import os
import requests

from os.path import splitext, split, join, dirname, basename
from pymongo import MongoClient
from celery import Task

from extensions import celery_app
from config import DefaultConfig


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        db = MongoClient().video_optimizer
        fs = gridfs.GridFS(db)

        converted_filepath = retval['output_file']
        client_ip = retval['client_ip']
        webhook = retval['webhook']

        key = ''.join(random.SystemRandom().choice(
            string.ascii_uppercase +
            string.digits +
            string.ascii_lowercase) for _ in range(32))

        file_id = fs.put(open(converted_filepath, 'rb'),
                         key=key,
                         task_id=task_id,
                         filename=task_id + '.mp4',
                         clientIP=client_ip,
                         webhook=webhook,
                         )
        print('FileID: {}'.format(file_id))
        print('Key: {}'.format(key))

        filepath = dirname(converted_filepath)
        converted_filename = basename(converted_filepath)
        origin_filepath = join(filepath,
                               converted_filename.replace('convert-', ''))

        os.remove(origin_filepath)
        os.remove(converted_filepath)

        doc = fs.get(file_id)._file

        def send_callback_request():
            response = requests.post(webhook, json={
                'task_id': task_id,
                'key': str(doc['_id']),
                'timestamp_now': calendar.timegm(time.gmtime()),
                'file': {
                    'md5': doc['md5'],
                    'size': doc['length'],
                    'date_upload': str(doc['uploadDate']),
                },
                '_link': {
                    'pull': '/pull/' + task_id + '?key=' + doc['key']
                }
            })
            print(response.status_code)
            return response.reason

        for i in range(DefaultConfig.RETRY_CALLBACK_REQUEST_COUNT):
            try:
                reason = send_callback_request()
                db.fs.files.update_one(
                    {'_id': file_id},
                    {'$set': {'callback_response': reason}})
                if reason == 'OK':
                    break
            except requests.exceptions.ConnectionError:
                db.fs.files.update_one(
                    {'_id': file_id},
                    {'$set': {'callback_response': 'ConnectionError'}})
                print('ConnectionError- FileID: {}'.format(file_id))
            time.sleep(3)

        print('/pull/' + task_id + '?key=' + doc['key'])

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(base=CallbackTask, bind=True)
def video_converter(self, input_file, client_ip, webhook):
    path, filename = split(input_file)
    orig_filename, file_ext = splitext(filename)
    output_file = join(path, 'convert-' + orig_filename + '.mp4')

    options = '-vcodec h264 -acodec aac -strict -2'
    cmd_convert = 'ffmpeg -y -i {input_file} {options} {output_file}'.format(
        input_file=input_file, options=options, output_file=output_file)
    print(cmd_convert)
    process = subprocess.Popen(cmd_convert,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True,
                               shell=True)
    duration_match = None
    fps_match = None

    hours = None
    minutes = None
    seconds = None
    fps = None
    frames = None

    for line in process.stdout:
        if not duration_match:
            pattern = 'Duration:\s+(\d{2}):(\d{2}):([-+]?[0-9]*\.?[0-9]+.), start:'
            # pattern = 'Duration:\s+(\d{2}):(\d{2}):(\d{2}), start:'
            duration_match = re.search(pattern, line)
            if duration_match:
                hours = int(duration_match.groups()[0])
                minutes = int(duration_match.groups()[1])
                seconds = int(duration_match.groups()[2][:2])

        if not fps_match:
            pattern = '(\d+) tbr,'
            fps_match = re.search(pattern, line)
            if fps_match:
                fps = int(fps_match.groups()[0])

        if seconds is not None and fps is not None:
            frames = (hours * 3600 + minutes * 60 + seconds) * fps

        if frames:
            pattern = 'frame=\s+(\d+) fps'
            current_frame_match = re.search(pattern, line)
            if current_frame_match:
                current_frame = int(current_frame_match.groups()[0])
                percent = str(current_frame / frames)[2:4]

                self.update_state(state='PROGRESS',
                                  meta={'percent': percent,
                                        'status': 'In Progress'})
    return {
        'percent': 100,
        'status': 'Completed',
        'output_file': output_file,
        'client_ip': client_ip,
        'webhook': webhook
    }
