# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector jplayer By Alfa development Group
# --------------------------------------------------------

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


from core import httptools
from core import jsontools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "no longer exists" in data or "to copyright issues" in data:
        return False, "[jplayer] El video ha sido borrado"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    post = {"r":"", "d":"www.jplayer.club"}
    data = httptools.downloadpage(page_url, post=post).data
    json = jsontools.load(data)["data"]
    for _url in json:
        url = _url["file"]
        label = _url["label"]
        video_urls.append([label +" [jplayer]", url])

    return video_urls
