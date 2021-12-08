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
list_quality = ['default']
list_servers = ['gounlimited']
host = 'http://freepornstreams.org'    #es http://xxxstreams.org http://fullxxxmovies.net

                                # k2s

def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Peliculas" , action="lista", url=host + "/free-full-porn-movies/"))
    itemlist.append(item.clone(title="Videos" , action="lista", url=host + "/videos/"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
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
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if item.title == "Categorias" :
        data = scrapertools.find_single_match(data,'filehosts</h3>(.*?)</aside>')
    else:
        data = scrapertools.find_single_match(data,'Popular Paysites</h3>(.*?)</aside>')
    patron  = '<a href="([^"]+)".*?>(.*?)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        if not "Featured" in scrapedtitle:
            scrapedplot = ""
            scrapedthumbnail = ""
            scrapedurl = scrapedurl.replace ("http://freepornstreams.org/freepornst/stout.php?s=100,75,65:*&#038;u=" , "")
            itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                                   thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<article id="post-\d+".*?'
    patron += '<a href="([^"]+)" rel="bookmark">(.*?)</a>.*?'
    patron += '<img src="([^"]+.jpg)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    logger.debug(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        if '/HD' in scrapedtitle : title= "[COLOR red]HD[/COLOR] %s" % scrapedtitle
        elif 'SD' in scrapedtitle : title= "[COLOR red]SD[/COLOR] %s" % scrapedtitle
        elif 'FullHD' in scrapedtitle : title= "[COLOR red]FullHD[/COLOR] %s" % scrapedtitle
        elif '1080' in scrapedtitle : title= "[COLOR red]1080p[/COLOR] %s" % scrapedtitle
        else: title = scrapedtitle
        thumbnail = scrapedthumbnail.replace("jpg#", "jpg")
        plot = ""
        if not "manyvids" in title:
            itemlist.append(item.clone(action="findvideos", title=title, url=scrapedurl, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot) )
    next_page = scrapertools.find_single_match(data, '<div class="nav-previous"><a href="([^"]+)"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
    patron = '<a href="([^"]+)" rel="nofollow[^>]+>(?:<strong>|)\s*(?:Streaming|Download)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        if not "ubiqfile" in url:
            itemlist.append(item.clone(action='play',title="%s", contentTitle=item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist
