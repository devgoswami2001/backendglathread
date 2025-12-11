# glathread/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "glathread.settings")

app = Celery("glathread")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
