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

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.pornodiamant.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/filme/"))
    itemlist.append(item.clone(title="Canal" , action="catalogo", url=host + "/channels/"))
    itemlist.append(item.clone(title="PornStar" , action="catalogo", url=host + "/pornostars/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/suchen/?q=%s" % texto
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a itemprop="url" href="([^"]+)".*?'
    patron += 'data-src="([^"]+)" alt="([^"]+)".*?'
    patron += '</svg>([^<]+)</'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle, cantidad in matches:
        title = "%s (%s)" %(scrapedtitle,cantidad.strip())
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data, 'itemprop="url" href="([^"]+)" title="Nächste">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a href="([^"]+)" data-category-gtmname="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '</svg>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        title = "%s (%s)" %(scrapedtitle,cantidad.strip())
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data, 'itemprop="url" href="([^"]+)" title="Nächste">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a href="([^"]+)" data-video-id.*?'
    patron += 'data-src="([^"]+)" alt="([^"]+)".*?'
    patron += '</svg>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,time in matches:
        time = time.strip()
        title = "[COLOR yellow]%s[/COLOR] %s" % (time, scrapedtitle)
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, 'itemprop="url" href="([^"]+)" title="Nächste">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<source src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        url = url.replace("&amp;", "&")
        itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<source src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        url = url.replace("&amp;", "&")
        itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist

