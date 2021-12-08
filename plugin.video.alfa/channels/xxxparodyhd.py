# -*- coding: utf-8 -*-
#------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from platformcode import config, logger
from core import httptools, scrapertools, tmdb
from core import servertools
from core.item import Item
from channels import filtertools
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['mangovideo']

host = 'https://xxxparodyhd.net'   #'https://watchpornfree.info'  playpornx

def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevas" , action="lista", url=host + "/movies/"))
    itemlist.append(item.clone(title="Mas Vistas" , action="lista", url=host + "/most-viewed/"))
    itemlist.append(item.clone(title="Mejor Valoradas" , action="lista", url=host + "/most-rating/"))
    itemlist.append(item.clone(title="Año" , action="years", url=host))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/%s" % (host,texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def years(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'>Releases</a>(.*?)</ul>')
    patron  = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist[::-1]


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if item.title == "Canal" :
        data = scrapertools.find_single_match(data,'>Studios</a>(.*?)</ul>')
    else:
        data = scrapertools.find_single_match(data,'>Categories</a>(.*?)</ul>')
    patron  = '<a href="([^"]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div data-movie-id="\d+".*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'oldtitle="([^"]+)".*?'
    patron += 'data-lazy-src="([^"]+)".*?rel="tag">(\d+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedyear in matches:
        scrapedplot = ""
        itemlist.append(item.clone(action="findvideos", title=scrapedtitle, contentTitle=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot, infoLabels={'year':scrapedyear}) )
    next_page = scrapertools.find_single_match(data,'<li class=\'active\'>.*?href=\'([^\']+)\'>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = ' - on ([^"]+)" href="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle,url in matches:
        # if "streamz" in url:
            # url = url.replace("streamz.cc", "stream2.vg").replace("streamz.vg", "stream2.vg")
        if not "vidup" in url and not "vev.io/" in url:
            itemlist.append(item.clone(action="play", title = "%s", contentTitle=item.title, url=url ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist
