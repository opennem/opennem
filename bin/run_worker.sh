# celery -A opennem.tasks.app worker --loglevel=INFO
python -m bin.huey_flush
huey_consumer -w 4 -k thread opennem.workers.scheduler.huey
