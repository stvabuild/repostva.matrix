# -*- coding: utf-8 -*-
# -*- Channel Peliculas Premium -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys

PY3 = False
if sys.version_info[0] >= 3:
    PY3 = True
    unicode = str
    unichr = chr
    long = int

import datetime
from core import servertools
from core import httptools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
from lib.AlfaChannelHelper import DooPlay
from channels import autoplay
from channels import filtertools

IDIOMAS = {'LA': 'LAT', 'ES': 'CAST', 'SB': 'VOSE', "EN": "VO"}

list_language = list(IDIOMAS.values())

list_quality = list()

list_servers = ['fembed',
                'doodstream',
                'streamtape',
                'mystream'
                ]

host = 'https://peliculaspremium.com/'
AlfaChannel = DooPlay(host)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel,
                         title="Peliculas",
                         action="sub_menu",
                         thumbnail=get_thumb('movies', auto=True),
                         url=host + 'peliculas?get=movies'
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         title="Series",
                         action="list_all",
                         thumbnail=get_thumb('tvshows', auto=True),
                         url=host + 'peliculas?get=tv'
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         title="Buscar",
                         action="search",
                         thumbnail=get_thumb('search', auto=True),
                         url=host + '?s='
                         )
                    )

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()
    c_year = datetime.datetime.now().year

    itemlist.append(Item(channel=item.channel,
                         title="Estrenos",
                         action="list_all",
                         url=host + 'release/%s' % c_year,
                         thumbnail=get_thumb('Premieres', auto=True)
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         title="Todas",
                         action="list_all",
                         url=host + 'peliculas?get=movies',
                         thumbnail=get_thumb('All', auto=True)
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         title="Generos",
                         action="seccion",
                         url=host + 'peliculas?get=movies',
                         thumbnail=get_thumb('genres', auto=True)
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         title="Por Año",
                         action="seccion",
                         url=host,
                         thumbnail=get_thumb('year', auto=True),
                         )
                    )

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item)


def seccion(item):
    logger.info()

    if item.title == 'Generos':
        return AlfaChannel.section(item, section="genres")
    else:
        itemlist = AlfaChannel.section(item, menu_id="8131")
        return sorted(itemlist, key=lambda i: i.title, reverse=True)


def seasons(item):
    logger.info()

    return AlfaChannel.seasons(item)


def episodesxseason(item):
    logger.info()

    return AlfaChannel.episodes(item)


def episodios(item):
    logger.info()

    itemlist = list()

    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()

    soup = AlfaChannel.create_soup(item.url)
    json_url = soup.find("iframe")["src"].replace("html", "json")
    json_data = httptools.downloadpage(json_url).json

    for elem in json_data:
        lang = IDIOMAS.get(elem["lang"], "VOSE")
        links = elem["links"]

        for v_data in links:
            url = v_data["enlace"]
            if "movcloud" in url:
                continue
            itemlist.append(Item(channel=item.channel, title="%s", action='play', language=lang, url=url,
                                 infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType != "episode":
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                     url=item.url, action="add_pelicula_to_library", extra="findvideos",
                     contentTitle=item.contentTitle))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    try:
        if texto != '':
            return AlfaChannel.search_results(item)
        else:
            return []
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + 'peliculas?get=movies'

        elif categoria == 'infantiles':
            item.url = host + 'animacion.html'

        elif categoria == 'terror':
            item.url = host + 'terror'

        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
