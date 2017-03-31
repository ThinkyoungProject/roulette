#!/usr/bin/env python 
# encoding: utf-8

__author__ = 'hasee'


from twisted.internet.defer import Deferred, DeferredList, inlineCallbacks, returnValue
from twisted.internet import reactor
import traceback
import logging
import time


def is_receive_complete(json_data):
    json_start = False
    json_tag_count = 0
    for chr in json_data:
        if chr == '{':
            if json_start is False:
                json_start = True
            json_tag_count = json_tag_count + 1
        elif chr == '}':
            json_tag_count = json_tag_count - 1
        if json_start is True and json_tag_count == 0:
            return True
    return False


def to_utf8(data):
    if type(data) is None:
        return ''
    elif type(data) is str:
        return data
    elif type(data) is unicode:
        return data.encode("utf8")
    else:
        return data


def to_localtime_str(gmtime_str):
    gmtime = time.strptime(gmtime_str, "%Y-%m-%dT%H:%M:%S")
    timestamp = time.mktime(gmtime) + 8 * 3600
    localtime = time.localtime(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", localtime)


@inlineCallbacks
def sleep(sec):
    d = Deferred()
    reactor.callLater(sec, d.callback, None)
    yield d

