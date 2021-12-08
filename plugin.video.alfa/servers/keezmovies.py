# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import logger

#como spankwire ".net//" lo quita y necesita 

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False, "[keezmovies] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    patron  = '"quality_(\d+)p":"([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for quality, scrapedurl in matches:
        url =  scrapedurl.replace("\/", "/").replace("\u0026", "&")
        video_urls.append(["[keezmovies] %sp" %quality, url])
    return video_urls
