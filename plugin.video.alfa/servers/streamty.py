# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Streamty By Alfa development Group
# --------------------------------------------------------

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File was deleted" in data:
        return False, "[Streamty] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []

    packed = scrapertools.find_single_match(data, "text/javascript'>(eval.*?)\s*</script>")
    unpacked = jsunpack.unpack(packed)
    
    media_url = scrapertools.find_single_match(unpacked, 'file:"([^"]+)"')
    #media_url += "|Referer=%s" %page_url
    if "m3u8" in media_url:
        ext = "m3u8"
    video_urls.append(["%s [streamty]" % (ext), media_url])

    return video_urls
