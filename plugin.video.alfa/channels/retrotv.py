# -*- coding: utf-8 -*-
# -*- Channel RetroTV -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channels import filtertools
from core import scrapertools
from core import servertools
from core.item import Item
from channels import autoplay
from lib.AlfaChannelHelper import ToroPlay
from platformcode import logger
from channelselector import get_thumb


host = "https://retrotv.org/"
AlfaChannel = ToroPlay(host, tv_path="/tv")

list_idiomas = ['LAT']
list_servers = ['okru', 'yourupload', 'mega']
list_quality = []


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title="Todas", action="list_all",
                         url=host + "category/animacion/", thumbnail=get_thumb("all", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Animación", action="list_all",
                         url=host + "lista-series", thumbnail=get_thumb("animacion", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Series", action="list_all",
                         url=host + "category/liveaction/", thumbnail=get_thumb("tvshows", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section", url=host,
                         thumbnail=get_thumb("genres", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section", url=host,
                         thumbnail=get_thumb("alphabet", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url= host + "?s=",
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item)


def section(item):
    logger.info()

    if item.title == "Generos":
        return AlfaChannel.section(item, menu_id="2460")
    elif item.title == "Alfabetico":
        return AlfaChannel.section(item, section="alpha", action="list_alpha")


def list_alpha(item):
    logger.info()

    return AlfaChannel.list_alpha(item)


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
    # soup = create_soup(item.url).find("ul", class_="TPlayerNv").find_all("li")
    soup, matches = AlfaChannel.get_video_options(item.url)

    infoLabels = item.infoLabels

    for btn in matches:
        opt = btn["data-tplayernv"]
        srv = btn.span.text.lower()
        if "opci" in srv.lower():
            # srv = "okru"
            continue
        itemlist.append(Item(channel=item.channel, title=srv, url=item.url, action='play', server=srv, opt=opt,
                             language='LAT', infoLabels=infoLabels))

    itemlist = sorted(itemlist, key=lambda i: i.server)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_idiomas, list_quality)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    logger.info()
    itemlist = list()

    soup = AlfaChannel.create_soup(item.url).find("div", class_="TPlayerTb", id=item.opt)
    url = scrapertools.find_single_match(str(soup), 'src="([^"]+)"')
    url = re.sub("amp;|#038;", "", url)
    url = AlfaChannel.create_soup(url).find("div", class_="Video").iframe["src"]
    itemlist.append(item.clone(url=url, server=""))
    itemlist = servertools.get_servers_itemlist(itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        if texto != '':

            item.url += texto
            return list_all(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

