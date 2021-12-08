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

host = 'https://fuckamouth.com'   #  http://freehdporn.ru     https://fuckamouth.com   http://hd-porn.co


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host))
    itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "/pornstars"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/porn/search?search=%s" % (host, texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="post thumb-border">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img data-src="([^"]+)".*?'
    patron += 'alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        title = scrapedtitle
        thumbnail = urlparse.urljoin(host,scrapedthumbnail)
        url = scrapedurl
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)" rel="next"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    logger.debug(data)
    patron = '<div class="item large-3.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?'
    patron +='alt="([^"]+)".*?'
    patron += '<div class="thumb-stats pull-left">(.*?)<div class="thumb-stats pull-right">.*?'
    patron += '<span>([^>]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,thumbnail,scrapedtitle,quality,time in matches:
        if "HD" in quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time, scrapedtitle)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time, scrapedtitle)
        if not thumbnail.startswith("https"):
            thumbnail = "%s/%s" %(host,thumbnail)
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)" rel="next"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url= scrapertools.find_single_match(data, '<iframe sandbox="[^"]+" src="([^"]+)"')
    patron = '<iframe sandbox="[^"]+" src="([^"]+)"'
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url= scrapertools.find_single_match(data, '<iframe sandbox="[^"]+" src="([^"]+)"')
    pornstars = scrapertools.find_multiple_matches(data, '<h3 class="hireq">([^<]+)<')
    pornstar = ' & '.join(pornstars)
    pornstar = "[COLOR cyan]%s[/COLOR]" % pornstar
    lista = item.title.split()
    logger.debug(lista)
    if "HD" in item.title:
        lista.insert (5, pornstar)
    else:
        lista.insert (3, pornstar)
    item.title = ' '.join(lista)
    patron = '<iframe sandbox="[^"]+" src="([^"]+)"'
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist