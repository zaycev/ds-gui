# coding: utf-8

from django.conf.urls import url
from django.conf.urls import patterns

urlpatterns = patterns("search.views",
    url(r"^$", "home", name="home"),
    url(r"^find/$", "find", name="find"),
)
