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

host = 'https://fapality.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas" , action="lista", url=host + "/newest/"))
    itemlist.append(item.clone(title="Mas Vistas" , action="lista", url=host + "/popular/"))
    itemlist.append(item.clone(title="Mejor valorada" , action="lista", url=host + "/top/"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/channels/"))
    itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "/pornstars/"))
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
    patron = '<div class="item"><a href="([^"]+)" title="([^"]+)">.*?'
    patron += '<img src="([^"]+)">.*?'
    patron += '<div class="right">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle.replace("movies", "") + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page_url = scrapertools.find_single_match(data,'<li itemprop="url" class="current">.*?<a href="([^"]+)"')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page_url) )
    if "/categories/" in item.url:
        itemlist = sorted(itemlist, key=lambda i: i.title)
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li\s+class="masonry-item item.*?'
    patron += '<a href="([^"]+)" class="kt_imgrc popfire" title="([^"]+)" >.*?'
    patron += '<img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail  in matches:
        title = scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle) )
    next_page_url = scrapertools.find_single_match(data,'<li itemprop="url" class="current">.*?<a href="([^"]+)"')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page_url) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<source id="video_source_\d+" src="([^"]+)".*?'
    patron += 'title="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url, quality  in matches:
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    return itemlist[::-1]


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<source id="video_source_\d+" src="([^"]+)".*?'
    patron += 'title="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url, quality  in matches:
        itemlist.append(['%s' %quality, url])
    return itemlist[::-1]
