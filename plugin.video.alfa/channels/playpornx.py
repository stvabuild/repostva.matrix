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

# https://playpornfree.org/   https://streamporn.pw/  https://mangoporn.net/   https://watchfreexxx.net/   https://losporn.org/  https://xxxstreams.me/  https://speedporn.net/
# "https://watchfreexxx.net/"  #  pandamovie https://watchpornfree.info  #'https://xxxparodyhd.net'  'http://www.veporns.com'  'http://streamporno.eu'

host = 'https://watchfreexxx.net'        #  https://www.netflixporno.net   https://xxxscenes.net   https://mangoporn.net   https://speedporn.net


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevo" , action="lista", url=host + "/adult/?filter=latest"))
    itemlist.append(item.clone(title="Mas visto" , action="lista", url=host + "/adult/?filter=most-viewed"))
    itemlist.append(item.clone(title="Popular" , action="lista", url=host + "/adult/?filter=popular"))
    itemlist.append(item.clone(title="Pornstars" , action="categorias", url=host + "/adult/pornstars/"))
    itemlist.append(item.clone(title="Canal" , action="canal", url=host + "/adult/xxx-studios/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/adult/genres/"))
    itemlist.append(item.clone(title="Buscar", action="search", url=host + "/adult/"))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/%s" % (item.url,texto)
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
        title = elem.a['title'].replace("&nbsp;", "" )
        if elem.img:
            thumbnail = elem.img['data-src'].replace("amp;", "")
        else:
            thumbnail = ""
        cantidad = elem.find(class_='video-datas')
        if cantidad:
            title = "%s (%s)" %(title, cantidad.text.strip())
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=thumbnail) )
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
        if elem.img:
            thumbnail = elem.img['data-src']
        else:
            thumbnail = ""
        year = elem.find(class_='duration').text.strip()
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
    matches = soup.find_all('li', class_='hosts-buttons-wpx')
    for elem in matches:
        url= elem.a['href']
        if not url in video_urls:
            video_urls += url
            itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

