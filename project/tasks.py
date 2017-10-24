import subprocess
import re
import gridfs
import os
import requests

from os.path import splitext, split, join, dirname, basename
from pymongo import MongoClient
from celery import Task

from extensions import celery_app


class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        db = MongoClient().video_optimizer
        fs = gridfs.GridFS(db)

        converted_filepath = retval['output_file']
        file_id = fs.put(open(converted_filepath, 'rb'),
                         filename=task_id + '.mp4')
        print('FileID: {}'.format(file_id))

        filepath = dirname(converted_filepath)
        converted_filename = basename(converted_filepath)
        origin_filepath = join(filepath,
                               converted_filename.replace('convert-', ''))

        os.remove(origin_filepath)
        os.remove(converted_filepath)

        doc = fs.get(file_id)._file
        # TODO: send request to real webhook
        requests.post('http://127.0.0.1:5001/webhook', json={
            'key': str(doc['_id']),
            'filename': doc['filename'],
            'md5': doc['md5'],
            'chunkSize': doc['chunkSize'],
            'length': doc['length'],
            'uploadDate': str(doc['uploadDate'])
        })

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass


@celery_app.task(base=CallbackTask, bind=True)
def video_converter(self, input_file, client_ip):
    # TODO: save client_ip to db
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
        'output_file': output_file
    }
