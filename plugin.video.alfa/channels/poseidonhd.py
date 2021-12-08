# -*- coding: utf-8 -*-
# -*- Channel PoseidonHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
from core import httptools
from core.item import Item
from core import servertools
from core import scrapertools
from channelselector import get_thumb
from platformcode import config, logger
from lib.AlfaChannelHelper import ToroFilm
from channels import filtertools, autoplay


IDIOMAS = {'mx': 'Latino', 'dk': 'Latino', 'es': 'Castellano', 'en': 'VOSE', 'gb': 'VOSE', 'de': 'Alemán',
           "Latino": "Latino", "Español": "Castellano", "Subtitulado": "VOSE", "usa": "VOSE", "mexico": "Latino",
           "espana": "Castellano"}

list_language = list(set(IDIOMAS.values()))

list_quality = []

list_servers = [
    'gvideo',
    'fembed'
    ]

host = 'https://tekilaz.co/'
AlfaChannel = ToroFilm(host, tv_path="/series")


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='sub_menu',
                         thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Series',  action='sub_menu',
                         thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Por Año', action='section', url=host,
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True),  extra='movie'))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def sub_menu(item):
    logger.info()

    itemlist = list()

    c_type = "movies" if item.title == "Peliculas" else item.title.lower()

    if c_type == "movies":
        itemlist.append(Item(channel=item.channel, title='Destacadas', url='%scategory/destacadas/' % host,
                             action='list_all', thumbnail=get_thumb('hot', auto=True), c_type=c_type))

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + c_type, action='list_all',
                         thumbnail=get_thumb('all', auto=True), c_type=c_type))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section', url=host,
                         thumbnail=get_thumb('genres', auto=True), c_type=c_type))

    return itemlist


def list_all(item):
    logger.info()

    if item.c_type != "search":
        item.url += "?type=%s" % item.c_type
    return AlfaChannel.list_all(item, postprocess=get_language_and_set_filter)


def section(item):
    logger.info()

    if item.title == "Generos":
        return AlfaChannel.section(item, menu_id="66646")[1:]
    else:
        return AlfaChannel.section(item, section="year")


def seasons(item):
    logger.info()

    return AlfaChannel.seasons(item)


def episodesxseason(item):
    logger.info()

    return AlfaChannel.episodes(item)


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = list()
    servers = {'drive': 'gvideo', 'fembed': 'fembed', "player": "oprem", "openplay": "oprem", "embed": "mystream"}

    soup, matches = AlfaChannel.get_video_options(item.url)

    for elem in matches:

        srv, lang = re.sub(r"\s+", "", elem.find("span", class_="server").text).split("-")
        opt = elem.a["href"].replace("#","")
        try:
            url = soup.find("div", id="%s" % opt).find("iframe")["data-src"]
        except:
            continue
        if srv.lower() in ["waaw", "jetload"]:
           continue
        if srv.lower() in servers:
           srv = servers[srv.lower()]

        itemlist.append(Item(channel=item.channel, title=srv, url=url, action="play", infoLabels=item.infoLabels,
                             language=IDIOMAS.get(lang, lang), server=srv))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             contentTitle=item.contentTitle))

    return itemlist


def play(item):
    logger.info()

    itemlist = list()
    try:
        data = AlfaChannel.create_soup(item.url).find("input")["value"]
        base_url = "%sr.php" % host
        post = {"data": data}
        url = httptools.downloadpage(base_url, post=post).url
        if "fs.%s" % host.replace("https://", "") in url:
            api_url = "%sr.php" % host.replace("https://", "https://fs.")
            v_id = scrapertools.find_single_match(url, r"\?h=([A-z0-9]+)")
            post = {"h": v_id}
            url = httptools.downloadpage(api_url, post=post).url
        itemlist.append(item.clone(url=url, server=""))
        itemlist = servertools.get_servers_itemlist(itemlist)
    except:
        pass

    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        item.c_type = "search"
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

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'movies'
        elif categoria == 'infantiles':
            item.url = host + 'category/animacion/'
        elif categoria == 'terror':
            item.url = host + 'category/terror/'
        item.type = "movies"
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def get_language_and_set_filter(*args):
    logger.info()

    langs = list()

    if "/series" in args[2].url:
        args[2].context = filtertools.context(args[3], list_language, list_quality)
    else:
        lang_list = args[1].find("span", class_="lang").find_all("img")
        try:
            for lang in lang_list:
                flag = scrapertools.find_single_match(lang["src"], '/flag-([^\.]+)\.')
                langs.append(IDIOMAS.get(flag.lower(), "VOSE"))
        except:
           pass

        args[2].language = langs

    return args[2]

