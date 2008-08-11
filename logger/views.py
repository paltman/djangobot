
import datetime

from django.conf import settings
from django.template import RequestContext
from django.views.decorators.cache import never_cache
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.date_based import archive_day
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.core.paginator import Paginator, InvalidPage

from logger.models import Channel, Message

def smart_page_range(paginator):
    # TODO: make this smarter :P
    page_range = [1, 2, 3, 4, "..."]
    page_range.extend(range(paginator.num_pages - 3, paginator.num_pages + 1))
    return page_range

def channel_search(request, channel_name):
    channel = get_object_or_404(Channel, name="#%s" % channel_name)
    query = request.GET.get("q", "")
    paginator = Paginator(Message.search.query(query).filter(channel_id=channel.pk).order_by("logged"), settings.PAGINATE_BY)
    try:
        page_number = int(request.GET.get("page", 1))
    except ValueError:
        return HttpResponseBadRequest()
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        raise Http404
    context = {
        "channel": channel,
        "channel_name": channel_name, # used for {% url %}
        "date": datetime.datetime.today(),
        "page": page,
        "page_range": smart_page_range(paginator),
        "paginator": paginator,
        "is_paginated": paginator.count >= settings.PAGINATE_BY,
        "messages": page.object_list,
    }
    return render_to_response("logger/channel_detail.html", 
        context, context_instance=RequestContext(request))

def channel_detail(request, channel_name):
    channel = get_object_or_404(Channel, name="#%s" % channel_name)
    paginator = Paginator(channel.message_set.all(), settings.PAGINATE_BY)
    try:
        page_number = int(request.GET.get("page", paginator.num_pages))
    except ValueError:
        return HttpResponseBadRequest()
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        raise Http404
    context = {
        "channel": channel,
        "channel_name": channel_name, # used for {% url %}
        "date": datetime.datetime.today(),
        "page": page,
        "page_range": smart_page_range(paginator),
        "paginator": paginator,
        "is_paginated": paginator.count >= settings.PAGINATE_BY,
        "messages": page.object_list,
    }
    return render_to_response("logger/channel_detail.html", 
        context, context_instance=RequestContext(request))
channel_detail = never_cache(channel_detail)

def channel_detail_day(request, channel_name, year, month, day):
    channel = get_object_or_404(Channel, name="#%s" % channel_name)
    date = datetime.date(*map(int, (year, month, day)))
    return render_to_response("logger/channel_detail_day.html", {
        "channel": channel,
        "channel_name": channel_name, # used for {% url %}
        "date": date,
        "messages": channel.message_set.filter(
            logged__range=(date, date + datetime.timedelta(days=1)),
        ).order_by("logged"),
    }, context_instance=RequestContext(request))
