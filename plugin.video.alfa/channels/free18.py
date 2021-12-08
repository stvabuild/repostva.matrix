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
from bs4 import BeautifulSoup

host = 'http://www.free18.net'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/search/%s-p1.html" % (host,texto)
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
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='cateories_image')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('strong').text
        thumbnail = elem.img['src']
        cantidad = elem.find('var').text
        title = "%s (%s)" %(title, cantidad)
        url = urlparse.urljoin(item.url,url)
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='video_video')
    for elem in matches:
        url = elem.find('strong').a['href']
        title = elem.find('strong').a['title']
        thumbnail = elem.img['src']
        stime = elem.find(style="float: left").text
        if stime:
            title = "[COLOR yellow]%s[/COLOR] %s" % (stime,title)
        url = urlparse.urljoin(item.url,url)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail, plot=plot,
                              contentTitle = title))
    next_page = soup.find('span', class_='ThisPage').find_next_siblings("a")
    if next_page:
        next_page = next_page[0]['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    url = soup.find(id='hdPlayer').find('source')['src']
    itemlist.append(item.clone(action="play", title = "mp4", url=url ))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    url = soup.find(id='hdPlayer').find('source')['src']
    itemlist.append(item.clone(action="play", url=url ))
    return itemlist