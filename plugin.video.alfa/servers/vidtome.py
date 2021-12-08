# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File Does not Exist" in data:
        return False, "[Vidto.me] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    data = httptools.downloadpage(page_url).data
    code = scrapertools.find_single_match(data, 'name="code" value="([^"]+)')
    hash = scrapertools.find_single_match(data, 'name="hash" value="([^"]+)')
    post = "op=download1&code=%s&hash=%s&imhuman=Proceed+to+video" %(code, hash)
    data1 = httptools.downloadpage("http://m.vidtome.stream/playvideo/%s" %code, post=post).data
    video_urls = []
    media_urls = scrapertools.find_multiple_matches(data1, 'file: "([^"]+)')
    for media_url in media_urls:
        ext = scrapertools.get_filename_from_url(media_url)[-4:]
        video_urls.append(["%s [vidto.me]" % (ext), media_url])
    video_urls.reverse()
    for video_url in video_urls:
        logger.info("%s" % (video_url[0]))
    return video_urls
