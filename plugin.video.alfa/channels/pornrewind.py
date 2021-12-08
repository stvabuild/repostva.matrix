# -*- coding: utf-8 -*-
#------------------------------------------------------------

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re
import os

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.pornrewind.com'

# Pagina en grogui

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/videos/?sort_by=post_date"))
    itemlist.append(item.clone(title="Mejor valorados" , action="lista", url=host + "/videos/?sort_by=rating"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/videos/?sort_by=video_viewed"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = host + "/search/%s/" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="swiper-slide">.*?'
    patron  += '<a href="([^"]+)".*?'
    patron  += 'data-src="([^"]+)".*?'
    patron  += '<span class="cats-title">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<a class="thumb" href="([^"]+)" title="([^"]+)".*?'
    patron += '<img class="lazyload" data-src="([^"]+)".*?'
    patron += '<span>(.*?)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]" + scrapedtime + "[/COLOR] " + scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<li class="direction"><a href="([^"]+)" data-ajax="pagination">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page ) )
    return itemlist


def findvideos(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data= scrapertools.find_single_match(data, '<div class="player">(.*?)<div class="media-info">')
    patron = '<(?:IFRAME SRC|iframe src)="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl in matches:
        url=scrapedurl
    if "kt_player" in data:
        url = item.url
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data= scrapertools.find_single_match(data, '<div class="player">(.*?)<div class="media-info">')
    patron = '<(?:IFRAME SRC|iframe src)="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl in matches:
        url=scrapedurl
    if "kt_player" in data:
        url = item.url
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist