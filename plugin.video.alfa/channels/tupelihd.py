# -*- coding: utf-8 -*-
# -*- Channel TuPeliHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

from bs4 import BeautifulSoup
from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from channels import filtertools, autoplay
from core import tmdb

host = "https://www.tupelihd.com/"

IDIOMAS = {'español': 'CAST', 'latino': 'LAT', 'vose': 'VOSE'}
list_language = IDIOMAS.values()
list_quality = []
list_servers = ['openload',  'streamango', 'uploadmp4', 'vidoza']


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(
        Item(channel=item.channel,
             title="Peliculas",
             action="sub_menu",
             thumbnail=get_thumb('movies', auto=True),
             mode='movies'))

    itemlist.append(
        Item(channel=item.channel,
             title="Series",
             action="sub_menu",
             thumbnail=get_thumb('tvshows', auto=True),
             mode='tvshows'))

    itemlist.append(
        Item(channel=item.channel,
             title="Buscar",
             action="search",
             url=host + "/?s=",
             mode='search',
             thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    if item.title == 'Peliculas':
        url = host + "todas-las-peliculas/"
    else:
        url = host + "series/"

    itemlist.append(
        Item(channel=item.channel,
             title="Todas",
             action="list_all",
             url=url,
             thumbnail=get_thumb('all', auto=True),
             mode=item.mode))

    itemlist.append(
        Item(channel=item.channel,
             title="Generos",
             action="section",
             thumbnail=get_thumb('genres', auto=True),
             mode=item.mode))

    return itemlist

def list_all(item):
    logger.info

    itemlist = list()

    data = httptools.downloadpage(item.url).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    for elem in soup.find_all("li", class_="TPostMv"):
        url = elem.a["href"]
        thumb = elem.img["src"]
        title = elem.h2.text
        cleantitle = title
        year = ''
        tvshow = elem.find("span", class_="TpTv BgA")

        if not tvshow:
            year = elem.find("span", class_="Date AAIco-date_range").text
            extra_info = elem.find("span", class_="calidad").text.split("|")

            try:
                language = extra_info[1].strip().encode('utf-8')
            except:
                language = ''

            if not config.get_setting("unify"):
                title += ' [%s]' % IDIOMAS.get(language.lower(), language)

        new_item = Item(channel=item.channel, title='%s' % title, url=url, thumbnail=thumb, infoLabels={'year': year})

        if tvshow:
            new_item.action = 'seasons'
            new_item.contentSerieName = cleantitle
            if item.mode != 'search':
                new_item.mode = 'tvshows'

        else:
            new_item.action = 'findvideos'
            new_item.contentTitle = cleantitle
            if item.mode != 'search':
                new_item.mode = 'movies'

        if item.mode == new_item.mode or item.mode == 'search':
            itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    # Pagination

    try:
        next_page = soup.find("a", class_="next page-numbers")["href"]
        itemlist.append(Item(channel=item.channel, title='Siguiente >>', url=next_page, action='list_all'))
    except:
        pass
    return itemlist


def section(item):
    logger.info()

    itemlist = list()
    data = httptools.downloadpage(host).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    if item.title.lower() == 'generos':
        soup = soup.find("li", id="menu-item-29")
        section_data = soup.find_all("li")

    for elem in section_data:
        title = elem.text
        url = elem.a["href"]
        itemlist.append(Item(channel=item.channel, title=title, url=url, action='list_all', mode=item.mode))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()

    data = httptools.downloadpage(item.url).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    infoLabels = item.infoLabels

    for elem in soup.find_all("div", class_="AA-link"):

        title = elem.text
        infoLabels['season'] = elem.span.text

        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                     action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodesxseasons(item):
    logger.info()

    itemlist = list()
    episodes = None

    data = httptools.downloadpage(item.url).data
    data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    season = item.infoLabels['season']

    for elem in soup.find_all("div", class_="Wdgt AABox"):
        season_num = elem.find("div")["data-tab"]
        if int(season_num) == season:
            episodes = elem
            break

    if episodes:

        infoLabels = item.infoLabels

        for epi in episodes.find_all("tr"):
            epi_info = epi.find(class_="MvTbTtl")
            url = epi_info.a["href"]
            epi_num = epi.find(class_="Num").text
            epi_title = epi_info.a.text
            title = '%sx%s - %s' % (season, epi_num, epi_title)
            infoLabels['episode'] = epi_num
            itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                                 infoLabels=infoLabels))

        tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    data = httptools.downloadpage(item.url).data
    data = scrapertools.unescape(data)

    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    for elem in soup.find_all("li", class_="STPb"):

        extra_info = elem.find_all("span")[1].text.split(' - ')

        if 'trailer' in extra_info[0].lower():
            continue

        lang = extra_info[0]

        url_info = soup.find(id=elem["data-tplayernv"])
        url = url_info.iframe["src"]
        title = add_lang(lang)

        itemlist.append(Item(channel=item.channel, title='%s'+title, url=url, action='play', infoLabels=item.infoLabels,
                             language=lang))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist


def add_lang(lang):

    if '.' in lang.lower():
        lang = 'vose'
    elif 'espa' in lang.lower():
        lang = 'español'

    title = ''
    if not config.get_setting("unify"):
        if lang:
            title += ' [%s]' % IDIOMAS.get(lang.lower(), '')
    return title


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    if texto != '':
        return list_all(item)
    else:
        return []

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host+'todas-las-peliculas/'

        elif categoria == 'infantiles':
            item.url = host + 'peliculas/animacion/'
        elif categoria == 'terror':
            item.url = host + 'peliculas/terror/'
        item.mode = 'movies'        
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist