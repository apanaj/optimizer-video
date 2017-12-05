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
  "task_id": "cbbb2683-4de4-4cd3-a20a-c911a8ebb292",
  "status": "OK",
  "key": "5a255f04c09e5f54e3384da5",
  "timestamp_now": 1512398596,
  "file": {
    "md5": "c60913975d5a7bab4c71395759ac2825",
    "size": 1134077,
    "seconds": 5,
    "date_upload": "2017-12-04 14:43:16.299000"
  },
  "_link": {
    "video": "127.0.0.1/pull/5a255f04c09e5f54e3384da5?key=6TGkDtZka1MnzyROORxPRrQQuXS8AbmH",
    "screenshot": "127.0.0.1/pull/5a255f04c09e5f54e3384dab?key=6TGkDtZka1MnzyROORxPRrQQuXS8AbmH"
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
