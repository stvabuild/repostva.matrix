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

host = 'https://en.paradisehill.cc'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/all/?sort=created_at"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/popular/?filter=month&sort=by_likes"))
    itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "/actors/?sort=by_likes"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/studios/?sort=by_likes"))

    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/?sort=by_likes"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/?pattern=%s" % (host,texto)
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
    matches = soup.find_all('div', class_='item')
    for elem in matches:
        url = elem.a['href']
        thumbnail = elem.find('img')['src']
        title = elem.find('img')['alt']
        url = urlparse.urljoin(item.url,url)
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    matches = soup.find_all('div', class_='item list-film-item')
    for elem in matches:
        url = elem.a['href']
        thumbnail = elem.find('img', itemprop='image')['src']
        title = elem.img['alt']
        url = urlparse.urljoin(item.url,url)
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', class_='fp-playlist').find_all('a')
    for elem in matches:
        url = elem['href']
        title = elem.text
        if not url.startswith("https"):
            url = "https:%s" % url
        itemlist.append(item.clone(action="play", title=title, url=url) )
    return itemlist

