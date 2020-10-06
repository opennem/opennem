from huey import RedisHuey, crontab

from opennem.settings import scrapy_settings

# from opennem.api.exporter import wem_run_all


huey = RedisHuey("opennem.exporter", host=scrapy_settings.cache_url)


# @huey.periodic_task(crontab(minute="*/10"))
# def wem_export_task():
#     wem_run_all()
