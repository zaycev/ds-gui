# coding: utf-8

# Copyright (C) University of Southern California (http://usc.edu)
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import json
import logging
import microidx
import traceback

from microidx import MicroIndex

from django.http import HttpResponse
from django.shortcuts import render_to_response


logger = logging.getLogger(__name__)


indexes = {
    "eng":     (MicroIndex("index_eng.ldb"),        "English"),
    "eng_gen": (MicroIndex("index_eng_gen.ldb"),    "English (generalized)"),

    "rus":     (None,                               "Russian"),
    "rus_gen": (None,                               "Russian (generalized)"),

    "spa":     (None,                               "Spanish"),
}


def json_response(json_dict):
    return HttpResponse(json.dumps(json_dict), status=200, content_type="application/json")


def home(request):
    return render_to_response("index.html", {})

W_NONE = {"v": "<NONE>", "p":None, "w":[], "t":0}
W_EMPY = {"v": "<->", "p":None, "w":[], "t":0}

def format_arg(query_words, arg, max_len=16):
    if arg == "<NONE>":
        return W_NONE
    if arg == "<->":
        return W_EMPY
    words = arg.split("||")
    lastw_pos = words[-1].split("-")
    if len(lastw_pos) > 2:
        lastw = "-".join(lastw_pos[:-1])
        pos = lastw_pos[-1]
    else:
        lastw, pos = lastw_pos
    words[-1] = lastw
    trimed = 0

    if len(words) == 1:
        visible = words[0]

    else:
        filtered = list(filter(lambda w: w in query_words, words))
        if len(filtered) == 0:
            filtered = words
        elif len(filtered) != len(words):
            trimed = 1

        visible = filtered[0]
        for w in filtered[1:]:
            if len(visible) >= max_len:
                trimed = 1
                break
            visible += ", "
            visible += w

    return {
        "v": visible,
        "p": pos,
        "w": words,
        "t": trimed,
    }

def format_triples(query_words, triples):
    result = []
    for rel_type, a1, a2, a3, a4, a5, tr_fr, tr_no in triples:
        result.append({
            "t": rel_type,
            "n": tr_no,
            "f": tr_fr,
            "a1": format_arg(query_words, a1),
            "a2": format_arg(query_words, a2),
            "a3": format_arg(query_words, a3),
            "a4": format_arg(query_words, a4),
            "a5": format_arg(query_words, a5),
        })
    return result


def find(request):

    query = request.GET.get("query", "").encode("utf-8")
    index = request.GET.get("index", None)
    mfreq = request.GET.get("mfreq", "0")
    rtype = request.GET.get("rtype", None)
    rpage = request.GET.get("rpage", "1")

    page_size = 256
    freq = MicroIndex.parse_frequency(mfreq)
    rpage = int(rpage)

    logging.info("%r\t%r\t%r\t%r\t%r" % (query, index,  mfreq, rtype, rpage))

    if index is None or index not in indexes:
        result = {
            "error":            True,
            "error_code":       1,
            "error_msg":        "Index key '%r' not found." % index,
            "found_triples":    [],
            "total_triples":    0,
            "page_size":        page_size,
            "pages":            0,
            "page":             0,
            "index":            index,
            "mfreq":            str(freq),
            "rtype":            rtype,
            "query":            str(query),
            "query_words":      [],
            "url":              request.build_absolute_uri(),
        }
        logging.error("Index key '%r' not found." % index)
        return json_response(result)

    mi_index = indexes[index][0]

    try:
        query = mi_index.parse_query(query)
    except microidx.MicroIndexQueryParsingError:
        error_msg = traceback.format_exc()
        result = {
            "error":            True,
            "error_code":       2,
            "error_msg":        "Error while parsing query: %r" % error_msg,
            "found_triples":    [],
            "total_triples":    0,
            "page_size":        page_size,
            "pages":            0,
            "page":             0,
            "index":            index,
            "mfreq":            str(freq),
            "rtype":            rtype,
            "query":            str(query),
            "query_words":      [],
            "url":              request.build_absolute_uri(),
        }
        logging.error("Error while parsing query: %r" % error_msg)
        return json_response(result)
    query_words = [sq[0] for sq in query]
    try:
        page = int(rpage) - 1
        if page < 0:
            page = 0
        offset = page * page_size
        result_page, result_size, offset = mi_index.find(query,
                                                         limit=page_size,
                                                         offset=offset,
                                                         rel_type=rtype,
                                                         freq=freq,
        )
        for i, t in enumerate(result_page):
            t[-1] = int(t[-1])
            t.append(i + offset + 1)

        pages = result_size / page_size + 1
        result = {
            "error":            False,
            "error_code":       None,
            "error_msg":        None,
            "found_triples":    format_triples(query_words, result_page),
            "total_triples":    result_size,
            "page_size":        page_size,
            "pages":            pages,
            "page":             rpage,
            "index":            index,
            "mfreq":            str(freq),
            "rtype":            rtype,
            "query":            str(query),
            "query_words":      query_words,
            "url":              request.build_absolute_uri(),
        }
    except microidx.MicroIndexQueryExecutionError:
        error_msg = traceback.format_exc()
        result = {
            "error":            True,
            "error_code":       3,
            "error_msg":        "Error while executing query: %r" % error_msg,
            "found_triples":    [],
            "total_triples":    0,
            "page_size":        page_size,
            "pages":            0,
            "page":             0,
            "index":            index,
            "mfreq":            str(freq),
            "rtype":            rtype,
            "query":            query,
            "query_words":      query_words,
            "url":              request.build_absolute_uri(),
        }
        logging.error("Error while executing query: %r" % error_msg)
        return json_response(result)

    logging.info("Found %d results. Returned %d starting from %d." % (result_size, page_size, offset))
    return json_response(result)
