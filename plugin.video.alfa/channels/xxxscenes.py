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
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = []

host = 'https://xxxscenes.net'    # https://www.netflixporno.net   https://mangoporn.net   https://speedporn.net


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/page/1?filter=latest"))
    itemlist.append(item.clone(title="Mas visto" , action="lista", url=host + "/page/1?filter=most-viewed"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/page/1?filter=popular"))
    itemlist.append(item.clone(title="Pornstar" , action="categorias", url=host + "/pornstars"))
    itemlist.append(item.clone(title="Canal" , action="canal", url=host + "/studios"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/genres"))
    itemlist.append(item.clone(title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)

    return itemlist




def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/%s" % (host,texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def canal(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='tag-item')
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text.strip()
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='video-block')
    for elem in matches:
        url = elem.a['href']
        title = elem.find(class_='title').text.strip()
        cantidad = elem.find(class_='video-datas').text.strip()
        thumbnail = elem.img['data-src']
        if cantidad:
            title = "%s (%s)" % (title,cantidad)
        itemlist.append(item.clone(action="lista", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail) )
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
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
    matches = soup.find_all('div', class_='video-block')
    for elem in matches:
        url = elem.a['href']
        title = elem.find(class_='title').text.strip()
        time = elem.find(class_='duration').text.strip()
        thumbnail = elem.img['data-src']
        if time:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, url=url, thumbnail=thumbnail,
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
    video_urls = []
    soup = create_soup(item.url)
    plot = soup.find(id="video-actors").text.strip()
    matches = soup.find_all('li', class_='hosts-buttons-wpx')
    for elem in matches:
        url= elem.a['href']
        if not url in video_urls:
            video_urls += url
            itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url, plot=plot))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

