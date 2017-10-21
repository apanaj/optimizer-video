## Video Optimizer
This micro service is a video converter that designed for given videos by `get` and `post` method

#### Technologies
```
- flask: web application
- ffmpeg: video converter
- celery: asynchronous task queue
- redis: celery result backend
- RabbitMQ: celery broker
```

#### Running celery app manually
```bash
celery -A tasks worker --loglevel=info
```

#### Example upload video request
get:
```
http://127.0.0.1:5000/upload?url=http://example.com/input.mpg
```

post:
```
http://127.0.0.1:5000/upload


form parameter key: file
```

response:
```json
{
    "filename": "/tmp/958be144-19f4-4261-a0bf-aee45478a0c7.mp4",
    "task_id": "32673e20-efab-42ee-99f4-855949d80051"
}
```

#### Check Task Status
pending response:
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