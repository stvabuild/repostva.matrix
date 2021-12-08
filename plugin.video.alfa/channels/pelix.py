# -*- coding: utf-8 -*-
# -*- Channel Pelix -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb, jsontools
from core.item import Item
from platformcode import config, logger
from channels import autoplay
from channels import filtertools
from bs4 import BeautifulSoup

host = 'https://pelix.me'

list_language = ["LAT"]
list_quality = list()
list_servers = ['zplayer', 'streamtape', 'mega', 'torrent']


def mainlist(item):
    logger.info()
    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all", url=host + "/peliculas/",
                         thumbnail=get_thumb('all', auto=True)))
    # itemlist.append(Item(channel=item.channel, title="Mas Vistas", action="list_all", url=host + "favorites",
                         # thumbnail=get_thumb('more watched', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Años", action="section", thumbnail=get_thumb('year', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)
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


def list_all(item):
    logger.info()
    itemlist = list()
    soup = create_soup(item.url).find('main', class_='site-main')
    matches = soup.find_all("article", class_="post")
    for elem in matches:
        url = elem.a["href"]
        title = elem.h2.text.strip()
        thumb = elem.img["src"]
        year = "-"
        itemlist.append(Item(channel=item.channel, title=title, contentTitle=title, url=url, action="findvideos",
                            thumbnail=thumb, infoLabels={'year': year}))
    tmdb.set_infoLabels_itemlist(itemlist, True)
    try:
        next_page = soup.find("a", class_="nextpostslink")
        if next_page:
            next_page = next_page["href"]
            itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=next_page, action='list_all',
                                 section=item.section))
    except:
        pass
    return itemlist


def section(item):
    logger.info()
    itemlist = list()
    soup = create_soup(host)
    action = 'list_all'
    menu = soup.find_all("ul", class_="sub-menu")
    if item.title == "Generos":
        matches = menu[0].find_all("li", class_="menu-item")
    else:
        matches = menu[1].find_all("li", class_="menu-item")
    for elem in matches:
        url = elem.a["href"]
        if not url.startswith("http"):
            url = host + url
        title = elem.a.text
        itemlist.append(Item(channel=item.channel, title=title, url=url, action=action, section=item.section))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = list()
    video_urls = []
    soup = create_soup(item.url)
    matches = soup.find_all("li", class_="sdpid")
    for elem in matches:
        url = elem['data-playerid']
        video_urls.append(url) 
        lang = elem.img['src']
        if "mx.png" in lang:
            lang = "LAT"
        itemlist.append(Item(channel=item.channel, action="play", title='%s', url=url,
                             language=lang, infoLabels=item.infoLabels))
    matches = soup.find('tbody').find_all('tr')
    for elem in matches:
        url = elem['url']
        url = url.replace(".nz/file/", ".nz/embed/").replace(".live/download/", ".live/embed/")
        if "streamtape" in url:
            url = scrapertools.find_single_match(url, 'https://streamtape.com/v/(\w+)/')
            url = "https://streamtape.com/e/%s/" %url
        lang = elem.find('td', class_='lalang')
        if lang:
            lang = "LAT"
        if not url in video_urls:
            video_urls.append(url)
            itemlist.append(Item(channel=item.channel, action="play", title='%s', url=url,
                                 language=lang, infoLabels=item.infoLabels))
    # logger.debug(video_urls)
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    if item.contentType == 'movie':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                     url=item.url, action="add_pelicula_to_library", extra="findvideos",
                     contentTitle=item.contentTitle))
    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    item = Item()
    try:
        if categoria in ['peliculas', 'latino', 'torrent']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + 'category/infantil'
        elif categoria == 'terror':
            item.url = host + 'category/terror'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
    return itemlist

