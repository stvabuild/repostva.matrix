# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector streamkiwi By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from platformcode import logger
import requests


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    httptools.downloadpage(page_url)
    source = page_url.replace("/e/", "/s/")
    data = requests.get(source, allow_redirects=False)
    if data.code == 404:
        return False, "[stream.kiwi] El archivo no existe o  ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)

    video_urls = []
    url = data.headers["location"]
    ext = url[-3:]
    url = url + "|verifypeer=false"
    video_urls.append(["%s [stream.kiwi]" % ext, url])

    return video_urls
