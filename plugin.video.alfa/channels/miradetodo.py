# -*- coding: utf-8 -*-
# -*- Channel MiraDeTodo -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
import base64
from core import tmdb
from core import httptools
from core.item import Item
from core import scrapertools
from core import servertools
from bs4 import BeautifulSoup
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


IDIOMAS = {'la': 'LAT', 'su': 'VOSE', 'ca': 'CAST'}
list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'streamtape',
    'doodstream',
    'evoload',
    ]

host = 'https://miradetodo.co/'


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title='Peliculas',
                         action='sub_menu', thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Series',
                         action='sub_menu', thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "?s=",
                         thumbnail=get_thumb("search", auto=True)))


    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = []
    base_url = host
    is_tvshow = False
    if item.title == "Series":
        base_url += "series/"
        is_tvshow = True

    itemlist.append(item.clone(title="Todas",
                               action="list_all",
                               thumbnail=get_thumb('all', auto=True),
                               url=base_url + 'page/1/'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="section",
                               url=base_url + 'page/1/',
                               thumbnail=get_thumb('genres', auto=True),
                               is_tvshow=is_tvshow
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="section",
                               url=base_url + 'page/1/',
                               thumbnail=get_thumb('year', auto=True),
                               is_tvshow=is_tvshow
                               ))

    return itemlist


def create_soup(url, post=None, unescape=False):
    logger.info()

    if post:
        data = httptools.downloadpage(url, post=post).data
    else:
        data = httptools.downloadpage(url, headers={"referer":host}).data

    if unescape:
        data = scrapertools.unescape(data)

    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def section(item):
    logger.info()

    itemlist = list()
    soup = create_soup(host)
    if item.is_tvshow:
        soup = soup.find("div", id="serieshome")
    else:
        soup = soup.find("div", id="moviehome")

    if item.title == "Generos":
        matches = soup.find("div", class_="categorias").find_all("li", class_="cat-item")
    elif item.title == "Calidad":
        matches = soup.find("div", class_="categorias").find_all("li", class_="cat-item")
    else:
        matches = soup.find("div", class_="filtro_y").find_all("li")
    for elem in matches:
        url = elem.a["href"]
        title = elem.a.text
        itemlist.append(Item(channel=item.channel, title=title.title(), action="list_all", url=url))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url).find("div", class_="peliculas")
    matches = soup.find_all("div", class_="item")

    for elem in matches:
        url = elem.a["href"]
        title = elem.find("div", class_="fixyear").h2.text
        title = re.sub(r"\(\d{4}(?:-Actualidad|-\d{4})?\)", "", title)
        year = elem.find("span", class_="year").text
        thumb = elem.img["src"]

        new_item = Item(channel=item.channel, title=title, url=url,
                        thumbnail=thumb, infoLabels={"year": year})

        if not "series/" in url:
            new_item.contentTitle = title
            new_item.action = "findvideos"
        else:
            new_item.contentSerieName = title
            new_item.action = "seasons"

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, True)

    try:
        url_next_page = soup.find("div", class_="nav-previous").a["href"]
    except:
        return itemlist

    if url_next_page:
        itemlist.append(Item(channel=item.channel, title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find_all("span", class_="se-t")
    infoLabels = item.infoLabels

    for elem in matches:
        season = elem.text
        title = "Temporada %s" % season
        infoLabels["season"] = season

        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseason',
                             context=filtertools.context(item, list_language, list_quality), infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = list()

    soup = create_soup(item.url)

    mmatches = soup.find_all("div", class_="se-c")
    infoLabels = item.infoLabels
    season = infoLabels["season"]
    matches = soup.find_all("div", class_="se-c")

    for elem in matches:
        if elem.find("span", class_="se-t").text != str(season):
            continue

        epi_list = elem.find("ul", class_="episodios")
        for epi in epi_list.find_all("li"):
            info = epi.find("div", class_="episodiotitle")
            url = info.a["href"]
            epi_name = info.a.text
            epi_num = epi.find("div", class_="numerando").text.split(" x ")[1]
            infoLabels["episode"] = epi_num
            title = "%sx%s - %s" % (season, epi_num, epi_name)

            itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                                 infoLabels=infoLabels))

    tmdb.set_infoLabels_itemlist(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()


    soup = create_soup(item.url)
    matches = soup.find("ul", class_="idTabs").find_all("a")
    if not matches:
        return itemlist

    for lang_opt in matches:

        if not "episodio" in item.url:
            lang = re.sub("audio", "", lang_opt.text.lower()).strip()[:2]
        else:
            lang = "su"
        player_id = lang_opt.get("href", "")[1:]
        if player_id.lower() in ["info", "links"]:
            continue
        player_data = soup.find("div", id=player_id)
        if player_data:
            player_url = player_data.iframe.get("data-lazy-src", "")
        else:
            player_url = player_data.a["href"]
        v_data = create_soup(player_url, unescape=True).find_all("a")
        for pl in v_data:
            b_url = scrapertools.find_single_match(pl.get("href", ""), "id=([A-Za-z0-9+/=]+)")
            try:
                if PY3:
                    url = base64.b64decode(bytes(b_url, "utf-8"))
                else:
                    url = base64.b64decode(b_url)
            except:
                continue
            if url:
                itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url,
                                     language=lang, infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.first = 0
        if texto != '':
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    itemlist = list()
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + 'page/1/'
        elif categoria == 'infantiles':
            item.url = host + 'category/animacion/'
        elif categoria == 'terror':
            item.url = host + 'category/terror/'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
