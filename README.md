# Video Optimizer
This micro service is a asynchronous video converter.

## Technologies
```
- flask: web application
- ffmpeg: video converter
- celery: asynchronous task queue
- redis: celery result backend
- RabbitMQ: celery broker
- mongodb: file info and file storage database
```

## Running celery app manually
```bash
celery -A tasks worker --loglevel=info
```

## Watermark position options:
```
tl → Top Left
tr → Top Right
bl → Bottom Left
br → Bottom Right
```

## End Points
### Upload Video. `get` and `post` method
get:
```
<server_url>/upload?url=http://example.com/input.mpg&webhook=http://127.0.0.1&watermark=bl
```

post:
```
<server_url>/upload


form parameter key: `file`
```

response:
```json
{
    "result": {
        "_link": {
            "progress": "http://127.0.0.1:5000/status/3573f19f-84b1-4a3b-bda2-300ecb96e6ed"
        },
        "task_id": "3573f19f-84b1-4a3b-bda2-300ecb96e6ed"
    },
    "status": "ACCEPTED"
}
```

### Check Task Status. `HEAD` method
```
<server_url>/status/<task_id>
```

example pending response:
```
X-Percent → 38
X-State → In Progress
X-Status → PROGRESS
```

complete response
```
X-Percent → 100
X-State → SUCCESS
X-Status → Completed
```

### Example SUCCESS response to webhook
```json
{
  "task_id": "4d408ec6-c5bd-4564-8a77-5c9933a08cac",
  "status": "OK",
  "key": "5a390fb4c09e5f41a4dd8715",
  "timestamp_now": 1513689012,
  "file": {
    "md5": "c0eadd80927d010be9fc3c96394786df",
    "size": 487510,
    "seconds": 5,
    "date_upload": "2017-12-19 13:10:12.592000"
  },
  "meta": {
    "ExifToolVersion": 10.1,
    "FileSize": "476 kB",
    "FileModifyDate": "2017:12:19 16:40:11+03:30",
    "FileAccessDate": "2017:12:19 16:40:12+03:30",
    "FileInodeChangeDate": "2017:12:19 16:40:11+03:30",
    "FileType": "MP4",
    "FileTypeExtension": "mp4",
    "MIMEType": "video/mp4",
    "MajorBrand": "MP4  Base Media v1 [IS0 14496-12:2003]",
    "MinorVersion": "0.2.0",
    "CompatibleBrands": [
      "isom",
      "iso2",
      "avc1",
      "mp41"
    ],
    "MovieDataSize": 482471,
    "MovieDataOffset": 48,
    "MovieHeaderVersion": 0,
    "CreateDate": "0000:00:00 00:00:00",
    "ModifyDate": "0000:00:00 00:00:00",
    "TimeScale": 1000,
    "Duration": "5.33 s",
    "PreferredRate": 1,
    "PreferredVolume": "100.00%",
    "PreviewTime": "0 s",
    "PreviewDuration": "0 s",
    "PosterTime": "0 s",
    "SelectionTime": "0 s",
    "SelectionDuration": "0 s",
    "CurrentTime": "0 s",
    "NextTrackID": 3,
    "TrackHeaderVersion": 0,
    "TrackCreateDate": "0000:00:00 00:00:00",
    "TrackModifyDate": "0000:00:00 00:00:00",
    "TrackID": 1,
    "TrackDuration": "5.28 s",
    "TrackLayer": 0,
    "TrackVolume": "0.00%",
    "ImageWidth": 640,
    "ImageHeight": 360,
    "GraphicsMode": "srcCopy",
    "OpColor": "0 0 0",
    "CompressorID": "avc1",
    "SourceImageWidth": 640,
    "SourceImageHeight": 360,
    "XResolution": 72,
    "YResolution": 72,
    "BitDepth": 24,
    "VideoFrameRate": 25,
    "MatrixStructure": "1 0 0 0 1 0 0 0 1",
    "MediaHeaderVersion": 0,
    "MediaCreateDate": "0000:00:00 00:00:00",
    "MediaModifyDate": "0000:00:00 00:00:00",
    "MediaTimeScale": 48000,
    "MediaDuration": "5.33 s",
    "MediaLanguageCode": "und",
    "HandlerDescription": "SoundHandler",
    "Balance": 0,
    "AudioFormat": "mp4a",
    "AudioChannels": 2,
    "AudioBitsPerSample": 16,
    "AudioSampleRate": 48000,
    "HandlerType": "Metadata",
    "HandlerVendorID": "Apple",
    "Encoder": "Lavf56.40.101",
    "AvgBitrate": "724 kbps",
    "ImageSize": "640x360",
    "Megapixels": 0.23,
    "Rotation": 0
  },
  "_link": {
    "video": "http://127.0.0.1:5000/pull/5a390fb4c09e5f41a4dd8715?key=yjvadhWOuQSbTuOenIGHa5qMWNKD37uz",
    "screenshot": "http://127.0.0.1:5000/pull/5a390fb4c09e5f41a4dd8718?key=yjvadhWOuQSbTuOenIGHa5qMWNKD37uz"
  }
}
```

### Example FAILED response to webhook
```
{
  "task_id": "fbfc3e73-5ae8-43ba-a30f-fa25e23f3429",
  "status": "FAILED",
  "timestamp_now": 1512398950,
  "exception": "No active exception to reraise"
}
```

### pull video and screenshot file. `get` method
```
<server_url>/pull/<task_id>?key=<key>&type=<video|screenshot>
```

### Create expiration mongo index
```javascript
db.fs.files.createIndex( { "uploadDate": 1 }, { expireAfterSeconds: 3600 * 2 } )
```
