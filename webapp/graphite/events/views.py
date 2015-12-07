import datetime

import pytz

from django.contrib.sites.models import RequestSite
from django.shortcuts import render_to_response, get_object_or_404
from django.utils.timezone import now, make_aware
from django.core.paginator import Paginator, EmptyPage
from django.views.decorators.cache import cache_page

from graphite.compat import HttpResponse
from graphite.util import json, epoch
from graphite.events.models import Event
from graphite.render.attime import parseATTime

from graphite.settings import EVENTS_PER_PAGE, _PAGE_LINKS, DEFAULT_CACHE_DURATION

from graphite.util import render_to

class EventEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return epoch(obj)
        return json.JSONEncoder.default(self, obj)


def get_page_range(paginator, page):
    """
    Generate page range
    """

    page_range = []
    if 4>page:
        if len(paginator.page_range)>_PAGE_LINKS:
            page_range = [p for p in range(1, _PAGE_LINKS+1)]
        else:
            page_range=paginator.page_range
    else:
        for p in paginator.page_range:
            if p<page:
                if page-p<(_PAGE_LINKS)//2:
                    page_range.append(p)
            if p>=page:
                if p-page<(_PAGE_LINKS)//2:
                    page_range.append(p)

        if len(page_range)>_PAGE_LINKS and page>5:
            page_range = page_range[:-1]
    return page_range


@cache_page(60 * 15)
@render_to('events.html')
def view_events(request, page_id=1):

    if request.method == "GET":
        try:
            page_id = int(page_id)
        except ValueError:
            page_id = 1
        events = fetch(request)
        paginator = Paginator(events, EVENTS_PER_PAGE)
        try:
            events = paginator.page(page_id)
        except EmptyPage:
            events = paginator.page(paginator.num_pages)
        pages = get_page_range(paginator, page_id)
        return locals()
    else:
        return post_event(request)


def detail(request, event_id):
    e = get_object_or_404(Event, pk=event_id)
    context = {'event': e}
    return render_to_response("event.html", context)


def post_event(request):
    if request.method == 'POST':
        event = json.loads(request.body)
        assert isinstance(event, dict)

        if 'when' in event:
            when = make_aware(
                datetime.datetime.utcfromtimestamp(event['when']),
                pytz.utc)
        else:
            when = now()
        Event.objects.create(
            what=event['what'],
            tags=event.get("tags"),
            when=when,
            data=event.get("data", ""),
        )
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=405)


def get_data(request):
    if 'jsonp' in request.REQUEST:
        response = HttpResponse(
          "%s(%s)" % (request.REQUEST.get('jsonp'),
              json.dumps(fetch(request), cls=EventEncoder)),
          content_type='text/javascript')
    else:
        response = HttpResponse(
            json.dumps(fetch(request), cls=EventEncoder),
            content_type="application/json")
    return response

def fetch(request):
    if request.GET.get("from") is not None:
        time_from = parseATTime(request.GET["from"])
    else:
        time_from = datetime.datetime.fromtimestamp(0)

    if request.GET.get("until") is not None:
        time_until = parseATTime(request.GET["until"])
    else:
        time_until = now()

    tags = request.GET.get("tags")
    if tags is not None:
        tags = request.GET.get("tags").split(" ")

    return [x.as_dict() for x in
            Event.find_events(time_from, time_until, tags=tags)]
