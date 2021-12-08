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
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.fetishshrine.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas" , action="lista", url=host + "/latest-updates/"))
    itemlist.append(item.clone(title="Popular" , action="lista", url=host + "/most-popular/"))
    itemlist.append(item.clone(title="Mejor Valorado" , action="lista", url=host + "/top-rated/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/?q=%s" % (host, texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)" title="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<span class="vids">(\d+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = "%s (%s)" % (scrapedtitle,cantidad)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)" itemprop="url">.*?'
    patron += 'contentUrl="([^"]+)" alt="([^"]+)">.*?'
    patron += '<span itemprop="duration" class="length">(.*?)</span>(.*?)<span class="thumb-info">'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,duracion,calidad  in matches:
        url = scrapedurl
        if ">HD<" in calidad:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" %(duracion,scrapedtitle)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" %(duracion,scrapedtitle)
        thumbnail = scrapedthumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=scrapedthumbnail, contentTitle = title ))
    next_page = scrapertools.find_single_match(data,'<li><a data=\'\d+\' href="([^"]+)" title="Next">')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
