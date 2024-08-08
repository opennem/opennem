# celery -A opennem.tasks.app worker --loglevel=INFO
python -m bin.huey_flush
huey_consumer -w4 -f -k process opennem.workers.scheduler.huey
