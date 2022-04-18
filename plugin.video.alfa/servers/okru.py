# -*- coding: utf-8 -*-

import re

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = ''
    data = httptools.downloadpage(page_url).data
    if "copyrightsRestricted" in data or "COPYRIGHTS_RESTRICTED" in data or "LIMITED_ACCESS" in data:
        return False, "[Okru] El archivo ha sido eliminado por violación del copyright"
    elif "notFound" in data or not "u0026urls" in data:
        return False, "[Okru] El archivo no existe o ha sido eliminado"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []

    data = httptools.downloadpage(page_url).data
    data = scrapertools.decodeHtmlentities(data).replace('\\', '')
    # URL del vídeo
    for type, url in re.findall(r'\{"name":"([^"]+)","url":"([^"]+)"', data, re.DOTALL):
        url = url.replace("%3B", ";").replace("u0026", "&")
        if "mobile" in type:
            continue
        video_urls.append([type + " [okru]", url])

    return video_urls
