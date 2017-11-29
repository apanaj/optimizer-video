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

### Example response to webhook
```json
{
  "task_id": "9521f1f5-b807-45a5-913e-b6776f97e323",
  "key": "5a1ec261c09e5f100e6ba81e",
  "timestamp_now": 1511965281,
  "file": {
    "md5": "4f59ce29a025d5e7b802e74fb47ab838",
    "size": 1151052,
    "seconds": 5,
    "date_upload": "2017-11-29 14:21:21.967000"
  },
  "_link": {
    "video": "/pull/9521f1f5-b807-45a5-913e-b6776f97e323?key=3QgN7ehujKOHpsY0VthcpfqZjQDdcpxg&type=video",
    "screenshot": "/pull/9521f1f5-b807-45a5-913e-b6776f97e323?key=3QgN7ehujKOHpsY0VthcpfqZjQDdcpxg&type=screenshot"
  }
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
