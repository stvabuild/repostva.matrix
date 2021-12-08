# -*- coding: utf-8 -*-
# -*- Channel TuCineClasico -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from core.item import Item
from core import servertools
from core import scrapertools
from channelselector import get_thumb
from platformcode import config, logger
from lib.AlfaChannelHelper import DooPlay
from channels import filtertools, autoplay


IDIOMAS = {'es': 'CAST', 'en': 'VOSE'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['supervideo']

host = "https://online.tucineclasico.es/"
AlfaChannel = DooPlay(host, movie_path="peliculas/")


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Todas", url=host+'peliculas', action="list_all",
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=host,
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Años", action="section", url=host,
                        thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...",  url=host + '?s=',  action="search",
                         thumbnail=get_thumb('search', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item)


def section(item):
    logger.info()

    if item.title == "Generos":
        return AlfaChannel.section(item, section="genre")
    elif item.title == "Años":
        return AlfaChannel.section(item, section="year")


def findvideos(item):
    logger.info()

    itemlist = list()

    soup, matches = AlfaChannel.get_video_options(item.url)

    for elem in matches:
        if elem["data-nume"] == "trailer":
            continue
        lang = elem.find("span", class_="flag").img["src"]
        lang = scrapertools.find_single_match(lang, "/flags/([^.]+).")
        data = AlfaChannel.get_data_by_post(elem).json
        url = data.get("embed_url", "")
        if not url or "youtube" in url:
            continue

        itemlist.append(Item(channel=item.channel, title='%s', action='play', url=url,
                            language=IDIOMAS.get(lang, "VOSE"), infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def search_results(item):

    return AlfaChannel.search_results(item, postprocess=get_lang)


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.first = 0
        if texto != '':
            return search_results(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def get_lang(*args):

    langs = list()
    try:
        lang_list = args[1].find_all("span", class_="flag")
        for lang in lang_list:
            lang = scrapertools.find_single_match(lang["style"], r'/flags/(.*?).png\)')
            if not lang in langs:
                langs.append(lang)
    except:
        langs = ""

    args[2].language = langs
    return args[2]
