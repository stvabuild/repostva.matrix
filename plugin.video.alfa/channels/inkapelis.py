# -*- coding: utf-8 -*-
# -*- Channel InkaPelis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re
from core import httptools
from core.item import Item
from core import scrapertools
from core import servertools
from channelselector import get_thumb
from platformcode import config, logger
from channels import filtertools, autoplay
from lib.AlfaChannelHelper import DooPlay
import sys


PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


IDIOMAS = {'latino': 'LAT', 'castellano': 'CAST', 'subtitulado': 'VOSE'}
list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'fembed',
    'streampe',
    'gounlimited',
    'mystream',
    'gvideo'
    ]

canonical = {
             'channel': 'inkapelis', 
             'host': config.get_setting("current_host", 'inkapelis', default=''), 
             'host_alt': ["https://www1.inkapelis.li/"], 
             'host_black_list': ["http://ww1.inkapelis.in/", "https://inkapelis.in/", "https://inkapelis.me/", 
                                 "https://ww1.inkapelis.de/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'forced_proxy_ifnot_assistant': 'ProxyWeb:hide.me', 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
AlfaChannel = DooPlay(host, "/pelicula", canonical=canonical)


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='menu_movies',
                         thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Series', url=host + 'serie', action='list_all',
                         thumbnail=get_thumb('tvshows', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section',
                         thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def menu_movies(item):
    logger.info()

    itemlist = list()

    itemlist.append(Item(channel=item.channel, title='Ultimas', url=host + 'estado/estrenos-hd/', action='list_all',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'pelicula', action='list_all',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Castellano', url=host + 'idioma/castellano', action='list_all',
                         thumbnail=get_thumb('cast', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Latino', url=host + 'idioma/latino', action='list_all',
                         thumbnail=get_thumb('lat', auto=True)))

    itemlist.append(Item(channel=item.channel, title='VOSE', url=host + 'idioma/subtituladas', action='list_all',
                         thumbnail=get_thumb('vose', auto=True)))

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item, postprocess=get_lang)


def section(item):
    logger.info()

    item.url = "%s%s" % (host, "pelicula")
    if item.title == "Generos":
        return AlfaChannel.section(item, section="genres")
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
    
    data = httptools.downloadpage(item.url, canonical=canonical).data
    
    post = scrapertools.find_single_match(data, 'data-post=(\d+)')
    url = host + "wp-json/dooplayer/v2/%s/%s/meplayembed" % (post, 'movie' if item.contentType == 'movie' else 'tv')
    data = httptools.downloadpage(url, canonical=canonical).json
    
    url = data["embed_url"].replace("s/tmdb", "/gen")
    data = httptools.downloadpage(url, canonical=canonical).data
    
    matches_languages = scrapertools.find_multiple_matches(data, "this, '(\d+).*?src.*?>([^<]+)")
    srv_list = {"fembed": "fembed", "stp": "streamtape", "stream": "mystream", "goplay": "gounlimited",
                "drive": "gvideo", "meplay": "netutv", "evoplay": "netutv", "uqload": "uqload",
                "playsb": "streamsb", "str" : "doodstream", "voe": "voe"}
    
    for n_lang, idioma in matches_languages:
        bloque = scrapertools.find_single_match(data, '(?is)class="Player%s.*?audio=' %n_lang)
        patron  = """go_to_player\('([^']+).*?"""
        patron += """serverx">([^<]+)"""
        matches = scrapertools.find_multiple_matches(bloque, patron)

        for url, srv in matches:
            if srv == "Descargar": continue
            language=IDIOMAS.get(idioma.lower(), "VOSE")

            server = srv_list.get(srv.lower(), "directo")
            itemlist.append(Item(channel=item.channel, title='%s [' + language + "]", action='play', url=url, server=server,
                                         language=language, infoLabels=item.infoLabels))

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

    if "gcs.megaplay" in item.url:
        api_url = "https://gcs.megaplay.cc/r.php"
        v_id = scrapertools.find_single_match(item.url, r"\?h=([A-z0-9]+)")
        post = {"h": v_id}
        url = httptools.downloadpage(api_url, post=post, ignore_response_code=True).url
    if item.post:
        v_id = httptools.downloadpage(item.url, post=item.post).data
        base_url = "https://players.%s" % host.replace("https://", "")
        data = httptools.downloadpage(base_url + v_id, add_referer=True).data
        url = "%s/%s" % (base_url, scrapertools.find_single_match(data, 'location.href = "([^"]+)'))
        url = httptools.downloadpage(url, add_referer=True).url

    elif item.url.startswith("/playerdir/"):
        url = "%s%s" % (host.replace("https://", "https://play."), item.url.replace("/playerdir", "playdir"))
        url = httptools.downloadpage(url, add_referer=True).url

    itemlist = servertools.get_servers_itemlist([item.clone(url=url, server="")])
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
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    logger.info()

    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'estado/estrenos-hd/'
        elif categoria == 'latino':
            item.url = host + 'idioma/latino'
        elif categoria == 'castellano':
            item.url = host + 'idioma/castellano'
        elif categoria == 'infantiles':
            item.url = host + 'genero/infantil/'
        elif categoria == 'terror':
            item.url = host + 'genero/terror/'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def get_lang(*args):

    langs = list()

    try:
        lang_list = args[1].find("div", class_="audio").find_all("div")
        for lang in lang_list:
            langs.append(lang["class"][0])
    except:
        langs = ""

    args[2].language = langs

    return args[2]
