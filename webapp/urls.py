# coding: utf-8

# Copyright (C) University of Southern California (http://usc.edu)
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE


from django.conf.urls import url
from django.conf.urls import patterns

urlpatterns = patterns("search.views",
    url(r"^$", "home", name="home"),
    url(r"^find/$", "find", name="find"),
)
