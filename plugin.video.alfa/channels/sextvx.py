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

host = 'https://www.sextvx.com'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/es/recent/"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/es/popular/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/es/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/es/results?search_query=%s&r=1" % (host,texto)
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
    matches = soup.find_all('div', class_='video')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['data-src']
        url = urlparse.urljoin(item.url,url)
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
    matches = soup.find_all('div', class_='video')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        if "search_query" in item.url:
            thumbnail = elem.img['src']
        else:
            thumbnail = elem.img['data-src']
        time = elem.find('span', class_='duration').next_sibling
        quality = elem.find('span', class_='hd-res')
        if quality:
            quality = quality.text
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time,quality,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        url = urlparse.urljoin(host, url)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
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
    soup = create_soup(item.url).find('video', class_='vplayer')
    matches = soup.find_all('source')
    for elem in matches:
        url = elem['src']
        quality = elem['title']
        itemlist.append(item.clone(action="play", title= quality, url=url))
    return itemlist[::-1]

def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('video', class_='vplayer')
    matches = soup.find_all('source')
    for elem in matches:
        url = elem['src']
        quality = elem['title']
        itemlist.append(['%s' %quality, url])
    return itemlist[::-1]
