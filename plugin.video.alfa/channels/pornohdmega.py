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
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['gounlimited']


host = 'https://www.pornohdmega.com'


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?filter=latest"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/?filter=most-viewed"))
    itemlist.append(item.clone(title="Mas popular" , action="lista", url=host + "/?filter=popular"))
    itemlist.append(item.clone(title="Mas largo" , action="lista", url=host + "/?filter=longest"))
    itemlist.append(item.clone(title="Canal" , action="catalogo", url=host + "/categories/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/tags/"))
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a href="([^"]+)" class="tag.*?'
    patron += 'aria-label="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        numero = scrapertools.find_single_match(scrapedtitle, '\((\d+)')
        thumbnail = ""
        scrapedplot = ""
        if int(numero) > 10:
            itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                                  thumbnail=thumbnail , plot=scrapedplot) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<article id="post-\d+".*?'
    patron += '<a href="([^"]+)" title="([^"]+)".*?'
    patron += 'src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        scrapedplot = ""
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=thumbnail , plot=scrapedplot) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<article id="post-\d+".*?'
    patron += '<a href="([^"]+)" title="([^"]+)".*?'
    patron += 'src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        if "0p" in scrapedtitle:
            quality = scrapertools.find_single_match(scrapedtitle, '(\d+p)')
            title = scrapertools.find_single_match(scrapedtitle, '([^"]+)(?:-| |)\d+p')
            title = "[COLOR red]%s[/COLOR] %s" % (quality,title)
        else:
            title = scrapedtitle
        thumbnail = scrapedthumbnail
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, contentTitle = title, url=scrapedurl,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot,))
    next_page = scrapertools.find_single_match(data, '<li><a class="current">.*?<a href="([^"]+)" class="inactive">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div\s+class="responsive-player".*?(?:src|SRC)="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for url in matches:
        itemlist.append(item.clone(action="play", title= "%s", contentTitle=item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist


