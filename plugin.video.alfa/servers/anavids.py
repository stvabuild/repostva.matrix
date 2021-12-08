# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertools
from platformcode import logger
from lib import jsunpack
from bs4 import BeautifulSoup


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    if "File is no longer available as it expired or has been deleted" in data:
        return False, "[anavids] El fichero ha sido borrado"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    patron = 'a href="#" onclick="([^"]+)".*?(\d+x\d+),'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for v_data, qlty in matches:
        dl_url = eval(v_data)
        dl_data = httptools.downloadpage(dl_url, headers={"referer": page_url}).data
        dl_data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", dl_data)
        url = scrapertools.find_single_match(dl_data, '<a href="([^"]+)">Direct Download Link</a>')
        url = url+"|verifypeer=false"
        video_urls.append(["%s [anavids]" % qlty, url])

    return video_urls


def download_video(id, mode, hash):
    return "https://anavids.com/dl?op=download_orig&id=%s&mode=%s&hash=%s" % (id, mode, hash)