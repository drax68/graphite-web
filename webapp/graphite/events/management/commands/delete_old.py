# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from graphite.events.models import Event
from graphite.settings import KEEP_EVENTS_DAYS
if not KEEP_EVENTS_DAYS:
    KEEP_EVENTS_DAYS = 365


class Command(BaseCommand):
    args = ''
    help = 'Delete old images'

    def handle(self, *args, **options):
        d = datetime.now() - timedelta(days=KEEP_EVENTS_DAYS)
        for i in Event.objects.filter(when__lte=d):
            print "Deleting - {} {}".format(i.when, i.what)
            try:
                i.delete()
            except:
                pass
