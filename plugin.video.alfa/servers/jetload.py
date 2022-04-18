# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector jetload By Alfa development Group
# --------------------------------------------------------
import re
from core import httptools, jsontools
from core import scrapertools
from platformcode import logger

video_urls = []
def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    subtitles = ""
    response = httptools.downloadpage(page_url)
    global data
    data = response.data
    if not response.sucess or "Not Found" in data or "File was deleted" in data or "is no longer available" in data:
        return False, "[jetload] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    media_url = scrapertools.find_single_match(data, '<video src="([^"]+)"')
    if media_url:
        ext = media_url[-4:]
        if ext == 'm3u8':
            media_url = ''
        video_urls.append(["%s [Jetload]" % (ext), media_url])

    return video_urls
