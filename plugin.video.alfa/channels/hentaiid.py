# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from core import httptools
from core import scrapertools
from core.item import Item
from platformcode import logger
from channels import filtertools
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = ['mixdrop']

CHANNEL_HOST = "http://hentai-id.tv/"


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(action="series", title="Novedades",
                         url=urlparse.urljoin(CHANNEL_HOST, "archivos/h2/"), extra="novedades"))
    itemlist.append(item.clone(action="generos", title="Por géneros", url=CHANNEL_HOST))
    itemlist.append(item.clone(action="series", title="Sin Censura",
                         url=urlparse.urljoin(CHANNEL_HOST, "archivos/sin-censura/")))
    itemlist.append(item.clone(action="series", title="High Definition",
                         url=urlparse.urljoin(CHANNEL_HOST, "archivos/high-definition/")))
    itemlist.append(item.clone(action="series", title="Mejores Hentais",
                         url=urlparse.urljoin(CHANNEL_HOST, "archivos/ranking-hentai/")))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def generos(item):
    logger.info()

    itemlist = []
    data = re.sub(r"\n|\r|\t|\s{2}", "", httptools.downloadpage(item.url).data)

    pattern = 'id="hentai2"><div[^>]+>(.*?)</div></div>'
    data = scrapertools.find_single_match(data, pattern)

    patron = 'href="([^"]+)"[^>]+>(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, title in matches:
        # logger.debug("title=[{0}], url=[{1}]".format(title, url))
        itemlist.append(item.clone(action="series", title=title, url=url))

    return itemlist


def series(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2}", "", httptools.downloadpage(item.url).data)

    pattern = "<div class='wp-pagenavi'>(.*?)</div>"
    pagination = scrapertools.find_single_match(data, pattern)

    pattern = '<div class="col-xs-12 col-md-12 col-lg-9px-3"><ul>(.*?)</ul><div class="clearfix">'
    data = scrapertools.find_single_match(data, pattern)

    pattern = '<a href="([^"]+)".*?<img src="([^"]+)" title="([^"]+)"'
    matches = re.compile(pattern, re.DOTALL).findall(data)

    if item.extra == "novedades":
        action = "findvideos"
    else:
        action = "episodios"

    for url, thumbnail, title in matches:
        show = title
        # logger.debug("title=[{0}], url=[{1}], thumbnail=[{2}]".format(title, url, thumbnail))
        itemlist.append(item.clone(action=action, title=title, contentTitle = title, url=url,
                             show=show, thumbnail=thumbnail, fanart=thumbnail, folder=True))

    if pagination:
        page = scrapertools.find_single_match(pagination, '>(?:Page|Página)\s*(\d+)\s*(?:of|de)\s*\d+<')
        pattern = 'href="([^"]+)">%s<' % (int(page) + 1)
        url_page = scrapertools.find_single_match(pagination, pattern)

        if url_page:
            itemlist.append(item.clone(action="series", title=">> Página Siguiente", url=url_page))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    data = re.sub(r"\n|\r|\t|\s{2}", "", httptools.downloadpage(item.url).data)
    pattern = '<div class="box-entry-title text-center">Lista de Capítulos</div>(.*?)</div></div>'

    data = scrapertools.find_single_match(data, pattern)
    patron = '<a href="([^"]+)"[^>]+>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapertools.unescape(scrapedtitle)
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = item.thumbnail
        plot = item.plot

        # logger.debug("title=[{0}], url=[{1}], thumbnail=[{2}]".format(title, url, thumbnail))
        itemlist.append(item.clone(action="findvideos", title=title, contentTitle = title, url=url,
                             thumbnail=thumbnail, plot=plot,
                             fanart=thumbnail))

    return itemlist


def findvideos(item):
    logger.info()

    data = httptools.downloadpage(item.url).data
    video_urls = []
    down_urls = []
    patron = '<(?:iframe)?(?:IFRAME)?\s*(?:src)?(?:SRC)?="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url in matches:
        if 'goo.gl' in url or 'tinyurl' in url:
            video = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers["location"]
            video_urls.append(video)
        else:
            video_urls.append(url)
    paste = scrapertools.find_single_match(data, 'https://gpaste.us/([a-zA-Z0-9]+)')
    if paste:
        try:
            new_data = httptools.downloadpage('https://gpaste.us/'+paste).data

            bloq = scrapertools.find_single_match(new_data, 'id="input_text">(.*?)</div>')
            matches = bloq.split('<br>')
            for url in matches:
                down_urls.append(url)
        except:
            pass
    video_urls.extend(down_urls)
    from core import servertools
    itemlist = servertools.find_video_items(data=",".join(video_urls))
    for videoitem in itemlist:
        videoitem.contentTitle = item.contentTitle
        videoitem.channel = item.channel
        videoitem.thumbnail = item.thumbnail
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    return itemlist
