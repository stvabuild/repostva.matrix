# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Streamz By Alfa development Group
# --------------------------------------------------------

import re
from core import httptools
from platformcode import logger
from core import scrapertools

def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)
    
    if "<b>File not found, sorry!</b" in data.data:
        return False, "[Streamz] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    gl_url = "https://get.streamz.tw/getlink-%s.dll" % data.url.split('/')[-1][1:]
    url = httptools.downloadpage(gl_url, follow_redirects=False).headers["location"]

    video_urls.append([".mp4 [Streamz]", url])

    return video_urls

