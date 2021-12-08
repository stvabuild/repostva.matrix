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

host = 'https://www.xvideos.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host))
    itemlist.append(item.clone(title="Lo mejor" , action="lista", url=host + "/best/"))
    itemlist.append(item.clone(title="Pornstar" , action="catalogo", url=host + "/pornstars-index"))
    itemlist.append(item.clone(title="WebCAM" , action="catalogo", url=host + "/webcam-models-index"))
    itemlist.append(item.clone(title="Canal" , action="catalogo", url=host + "/channels-index/from/worldwide/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/tags"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?k=%s&sort=uploaddate" % (host, texto)
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
    patron = '<li><a href="([^"]+)"><b>([^<]+)</b><span class="navbadge default">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        title = "%s (%s)" % (scrapedtitle, cantidad)
        itemlist.append(item.clone(action="lista", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>|amp;", "", data)
    patron = '<div class="thumb"><a href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += '<span class="profile-name">([^<]+)</span>.*?'
    patron += '<span class="with-sub">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedurl = urlparse.urljoin(host,scrapedurl) + "/videos/new/0"
        title = "%s (%s)" % (scrapedtitle, cantidad)
        itemlist.append(item.clone(action="lista", title=title, url=scrapedurl,
                              thumbnail=scrapedthumbnail , plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)" class="no-page next-page">Siguiente')
    if next_page=="":
        next_page = scrapertools.find_single_match(data, '<li><a class="active".*?<a href="([^"]+)"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>|amp;", "", data)
    patron = 'data-id="(\d+)".*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '</a>(.*?)<div class=.*?'
    patron += '<a href="[^"]+" title="([^"]+)".*?'
    patron += '<span class="duration">([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,quality,scrapedtitle,scrapedtime in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (scrapedtime, scrapedtitle)
        scrapedurl = "/video%s/" % scrapedurl
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        thumbnail = scrapedthumbnail.replace("THUMBNUM" , "10")
        quality = scrapertools.find_single_match(quality, 'mark">([^<]+)</span>')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (scrapedtime, quality, scrapedtitle)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=scrapedurl,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)" class="no-page next-page">')
    if next_page=="":
        next_page = scrapertools.find_single_match(data, '<li><a class="active".*?<a href="([^"]+)"')
    next_page = next_page.replace("#", "")
    if next_page:
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