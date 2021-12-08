# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    if "/player/" in page_url:
        data = httptools.downloadpage(page_url).data
        media_url = scrapertools.find_single_match(data, '<source src="([^"]+)"')
    else:
        data = httptools.downloadpage(page_url).page
        media_url = scrapertools.find_single_match(data, '\'file\': \'([^"]+)\',')
    video_urls = []
    video_urls.append([scrapertools.get_filename_from_url(media_url)[-4:] + " [fakingstv]", media_url])

    return video_urls
