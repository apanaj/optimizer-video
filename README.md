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

## End Points
### Upload Video. `get` and `post` method
get:
```
<server_url>/upload?url=http://example.com/input.mpg&webhook=127.0.0.1
```

post:
```
<server_url>/upload


form parameter key: `file`
```

response:
```json
{
    "task_id": "32673e20-efab-42ee-99f4-855949d80051"
}
```

### Check Task Status. `get` method
```
<server_url>/status/<task_id>
```

example pending response:
```json
{
    "percent": "38",
    "state": "PROGRESS",
    "status": "In Progress"
}
```

complete response
```json
{
    "percent": 100,
    "state": "SUCCESS",
    "status": "Completed"
}
```

### pull video file. `get` method
```
<server_url>/pull/<file_key>
```

### Create expiration mongo index
```json
db.fs.files.createIndex( { "uploadDate": 1 }, { expireAfterSeconds: 3600 * 2 } )
```