# -*- coding: utf-8 -*-
# -*- Channel SonPelisHD -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int


from core import servertools
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb
from lib.AlfaChannelHelper import DooPlay

canonical = {
             'channel': 'sonpelishd', 
             'host': config.get_setting("current_host", 'sonpelishd', default=''), 
             'host_alt': ["https://sonpelishd.net/"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
AlfaChannel = DooPlay(host, tv_path="serie", canonical=canonical)


def mainlist(item):
    logger.info()

    itemlist = list()

    itemlist.append(item.clone(title="Peliculas",
                               action="list_all",
                               thumbnail=get_thumb('movies', auto=True),
                               url=host + 'pelicula'
                               ))

    itemlist.append(item.clone(title="Series",
                               type = 1,
                               action="list_all",
                               thumbnail=get_thumb('movies', auto=True),
                               url=host + 'serie'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host + 'pelicula',
                               thumbnail=get_thumb('genres', auto=True),
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host + 'page/1?s',
                               thumbnail=get_thumb('year', auto=True),
                               seccion='fecha-estreno'
                               ))

    itemlist.append(item.clone(title="Buscar", action="search",
                               thumbnail=get_thumb('search', auto=True),
                               url=host + '?s='
                               ))

    return itemlist


def list_all(item):
    logger.info()

    return AlfaChannel.list_all(item)


def seccion(item):
    logger.info()

    if item.title == 'Generos':
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
    srv_list = {"fcom": "fembed", "embedsb.com": "streamsb", "dood.ws": "doodstream", "jawcloud.co": "jawvcloud",
                "waaw.to": "netutv", "upstream.to": "upstream", "streamto": "streamplay"}

    soup, matches = AlfaChannel.get_video_options(item.url)
    
    for elem in matches:

        lang = elem.find('span', class_='title').text
        srv = elem.find('span', class_='server').text

        post = {"action": "doo_player_ajax", "post": elem["data-post"], "nume": elem["data-nume"],
                "type": elem["data-type"]}

        srv = srv_list.get(srv, "directo")
        itemlist.append(Item(channel=item.channel, title=srv, server=srv, action='play', language=lang, post=post,
                             infoLabels=item.infoLabels))

    if item.contentType != "episode":
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                                 url=item.url, action="add_pelicula_to_library", extra="findvideos",
                                 contentTitle=item.contentTitle))

    return itemlist


def play(item):
    logger.info()

    itemlist = list()

    data = AlfaChannel.get_data_by_post(post=item.post).json
    url = data['embed_url']

    if not url.startswith("http"):
        url = "https:%s" % url
    itemlist.append(item.clone(url=url, server=''))

    itemlist = servertools.get_servers_itemlist(itemlist)

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
        if categoria in ['peliculas', 'latino']:
            item.url = host + 'pelicula/'

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
