# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data, server
    data = httptools.downloadpage(page_url).data
    server = scrapertools.find_single_match(page_url, 'https://(?:www.|es.|)([A-z0-9-]+).(?:com|net)')
    if "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, "[%s] El fichero no existe o ha sido borrado" %server
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    patron  = '<source (?:id="video_source_\d+" |data-fluid-hd |)src="([^"]+)".*?title="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url,quality in matches:
        url += "|Referer=%s" % page_url
        video_urls.append(["[%s] %s" %(server,quality), url])
    return video_urls
