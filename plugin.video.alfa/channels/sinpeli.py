# -*- coding: utf-8 -*-
# -*- Channel SinPeli -*-
# -*- Created for Alfa Addon -*-
# -*- By the Alfa Development Group -*-

import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import base64
from channels import filtertools
from bs4 import BeautifulSoup
from core import servertools
from core.item import Item
from channels import autoplay
from lib.AlfaChannelHelper import ToroPlay
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://www.sinpeli.com/'
AlfaChannel = ToroPlay(host, )

IDIOMAS = {'la': 'LAT', 'ca': 'CAST', 'su': 'VOSE'}
list_idiomas = list(set(IDIOMAS.values()))

list_servers = ['okru', 'yourupload', 'mega']
list_quality = []


def mainlist(item):
    logger.info()

    itemlist = list()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel,
                         action="list_all",
                         thumbnail=get_thumb("All", auto=True),
                         title="Todas",
                         url=host
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         action="section",
                         thumbnail=get_thumb("language", auto=True),
                         title="Idiomas",
                         url=host
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         action="section",
                         thumbnail=get_thumb("quality", auto=True),
                         title="Calidad",
                         url=host
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         action="section",
                         thumbnail=get_thumb("genres", auto=True),
                         title="Generos",
                         url=host
                         )
                    )

    itemlist.append(Item(channel=item.channel,
                         action="search",
                         thumbnail=get_thumb("search", auto=True),
                         url=host + "?s=",
                         title="Buscar..."
                         )
                    )

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item, postprocess=get_languages)


def section(item):
    logger.info()

    if item.title == "Generos":
        return AlfaChannel.section(item, menu_id="351")
    elif item.titl == "Idiomas":
        return AlfaChannel.section(item, menu_id="415")
    else:
        return AlfaChannel.section(item, menu_id="421")


def findvideos(item):
    logger.info()

    itemlist = list()
    infoLabels = item.infoLabels

    soup, matches = AlfaChannel.get_video_options(item.url)

    for btn in matches:
        b_data = btn["data-player"]
        srv = btn.span.text.lower()
        if "trailer" in srv.lower():
            continue
        try:
            lang = btn.span.next_sibling.text[:2]
        except:
            lang = "la"

        itemlist.append(Item(channel=item.channel,
                             action='play',
                             infoLabels=infoLabels,
                             language=IDIOMAS.get(lang.lower(), "LAT"),
                             b_data=b_data,
                             server=srv,
                             title=srv,
                             url=item.url
                            )
                        )

    itemlist = sorted(itemlist, key=lambda i: i.server)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and (
            not item.videolibrary or item.extra != 'findvideos'):
        itemlist.append(Item(action="add_pelicula_to_library",
                             contentTitle=item.contentTitle,
                             channel=item.channel,
                             extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url
                            )
                        )

    return itemlist


def play(item):
    logger.info()
    itemlist = list()

    try:
        url = BeautifulSoup(base64.b64decode(item.b_data.encode("utf-8")), "html5lib").iframe["src"]
        item.url = url
        item.server = ""
        itemlist.append(item)
        itemlist = servertools.get_servers_itemlist(itemlist)
    except:
        pass

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        if texto != '':
            item.url += texto
            item.search = True
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

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host
        elif categoria == 'latino':
            item.url = host + "idioma/latino/"
        elif categoria == 'castellano':
            item.url = host + "idioma/castellano"
        elif categoria == 'infantiles':
            item.url = host + 'animacion'
        elif categoria == 'terror':
            item.url = host + 'terror'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def get_languages(*args):
    logger.info()

    try:
        lang = args[1].find("span", class_="languages").text.strip()[:2]
    except:
        lang = "la"

    args[2].language = IDIOMAS.get(lang.lower(), "la")

    return args[2]