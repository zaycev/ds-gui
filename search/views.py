# coding: utf-8

import json

from microidx import MicroIndex

from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import render_to_response


mi = MicroIndex("index_eng")


def index(request):
    return render_to_response("index.html", {})


def find(request):

    query = request.GET.get("query", "").encode("utf-8")
    store = request.GET.get("store", "eng")
    mfreq = request.GET.get("mfreq", "0")


    sub_queries = [t.replace(" ", "").split(":") for t in query.split(" AND ")]
    query = []

    print sub_queries

    for sub_query in sub_queries:
        word, pos, idx = None, None, None
        if len(sub_query) == 0:
            continue
        if len(sub_query) == 1:
            word = sub_query[0]
        elif len(sub_query) == 2:
            word, pos = sub_query
        elif len(sub_query) == 3:
            word, pos, idx = sub_query

        if pos is not None and pos == "*":
                pos = None

        if idx is not None:
            if idx == "*":
                idx = None
            else:
                idx = int(idx)

        query.append((word, pos, idx))

    print query

    triples = mi.find(query, min_freq=int(mfreq))

    return HttpResponse(json.dumps(triples), status=200, content_type="application/json")