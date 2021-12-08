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
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools
from channels import filtertools
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['mangovideo']

# https://playpornfree.org/   https://streamporn.pw/  https://mangoporn.net/   https://watchfreexxx.net/   https://losporn.org/  https://xxxstreams.me/  https://speedporn.net/

host = 'https://watchpornfree.info'   #'https://xxxparodyhd.net'      playpornx

                                # KTP no resuelve

def mainlist(item):
    logger.info("")
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Videos" , action="lista", url=host + "/scenes/"))
    itemlist.append(item.clone(title="Peliculas" , action="lista", url=host))
    itemlist.append(item.clone(title="Parodia" , action="lista", url=host + "/category/parodies"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host))
    itemlist.append(item.clone(title="Año" , action="categorias", url=host))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info("")
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info("")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if item.title == "Canal":
        data = scrapertools.find_single_match(data,'Studios</a>(.*?)</ul>')
    if item.title == "Año":
        data = scrapertools.find_single_match(data,'Years</a>(.*?)</ul>')
    if item.title == "Categorias":
        data = scrapertools.find_single_match(data,'>Categories</div>(.*?)</ul>')
    patron  = 'href="([^"]+)".*?>([^"]+)</a></li>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle  in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle
        scrapedthumbnail = ""
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist

def lista(item):
    logger.info("")
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<article class="TPost B">.*?'
    patron += '<a href="([^"]+)">.*?'
    patron += 'src="([^"]+)".*?'
    patron += '<div class="Title">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        itemlist.append(item.clone(action="findvideos", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, contentTitle=scrapedtitle, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<a class="next page-numbers" href="([^"]+)">Next &raquo;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    links_data = scrapertools.find_single_match(data, '<div id="pettabs">(.*?)</ul>')
    patron = 'href="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(links_data)
    for url in matches:
        if "streamz" in url:
            url = url.replace("streamz.cc", "stream2.vg").replace("streamz.vg", "stream2.vg")
        if not "vidup" in url and not "vev.io" in url:
            itemlist.append(item.clone(title='%s', url=url, action='play', language='VO',contentTitle = item.contentTitle))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

