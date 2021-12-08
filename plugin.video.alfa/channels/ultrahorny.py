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
import requests
from lib import servop
import os

host = 'https://ultrahorny.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?filter=latest"))
    itemlist.append(item.clone(title="Mas visto" , action="lista", url=host + "/?filter=most-viewed"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/?filter=popular"))
    itemlist.append(item.clone(title="Mas largo" , action="lista", url=host + "/?filter=longest"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s" % (host,texto)
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
    matches = soup.find_all('li', class_='tag-menu')
    for elem in matches:
        url = elem.a['href']
        title = elem.text.strip()
        thumbnail = ""
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    itemlist.sort(key=lambda x: x.title)
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
    matches = soup.find_all('div', class_='video-block')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('span', class_='title').text.strip()
        thumbnail = elem.img['data-src']
        time = elem.find('span', class_='duration')
        if time:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time.text, title)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    url = soup.find('div', class_='video-player').iframe['src']
    itemlist.append(Item(channel=item.channel, title='%s', contentTitle = item.contentTitle, url=url, action='play'))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    url = soup.find('div', class_='video-player').iframe['src']
    itemlist.append(Item(channel=item.channel, title='%s', contentTitle = item.contentTitle, url=url, action='play'))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    return itemlist

