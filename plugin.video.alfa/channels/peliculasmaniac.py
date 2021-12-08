# -*- coding: utf-8 -*-
# -*- Channel PeliculasManiac -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

IDIOMAS = {'ES': 'CAST', 'VOS': 'VOS','EN': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['720p', 'HD 1080p', '480p', '360p', '270p']
list_servers = ['directo']

host = "http://peliculasmaniac.com/"


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title="Novedades",
                         action="list_all",
                         url=host + 'canal/novedades/',
                         first=0,
                         thumbnail=get_thumb('newest', auto=True),
                         ))

    itemlist.append(Item(channel=item.channel, title="Destacadas",
                         action="list_all",
                         thumbnail=get_thumb('hot', auto=True),
                         url=host + 'canal/Mejores+Películas/',
                         first=0
                         ))

    itemlist.append(Item(channel=item.channel, title="Castellano",
                         action="list_all",
                         url=host + 'canal/Pel%C3%ADculas%20en%20espa%C3%B1ol/',
                         first=0,
                         thumbnail=get_thumb('cast', auto=True)
                         ))

    itemlist.append(Item(channel=item.channel, title="Subtituladas",
                         action="list_all",
                         url=host + 'canal/Películas%20VO%20subtitulada/',
                         first=0,
                         thumbnail=get_thumb('vose', auto=True)
                         ))

    itemlist.append(Item(channel=item.channel, title="VO",
                         action="list_all",
                         url=host + 'canal/Películas%20en%20VO/',
                         first=0,
                         ))

    itemlist.append(Item(channel=item.channel, title="A-Z",
                         action="list_all",
                         url=host + 'canal/a-z/',
                         first=0,
                         thumbnail=get_thumb('alphabet', auto=True),
                         ))



    itemlist.append(Item(channel=item.channel,title="Buscar",
                    action="search",
                    url=host+'busqueda.php?bus=',
                    thumbnail=get_thumb('search', auto=True),
                    ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def sub_menu(item):
    logger.info()

    itemlist = []



    itemlist.append(Item(channel=item.channel,title="Todas",
                         action="list_all",
                         thumbnail=get_thumb('all', auto=True),
                         url='%s%s' % (host, '/peliculas/'),
                         first=0
                         ))

    itemlist.append(Item(channel=item.channel, title="Mas vistas",
                         action="list_all",
                         thumbnail=get_thumb('more watched', auto=True),
                         url='%s%s' % (host, '/most-viewed/'),
                         first=0
                         ))

    itemlist.append(Item(channel=item.channel,title="Generos",
                         action="seccion",
                         thumbnail=get_thumb('genres', auto=True),
                         fanart='https://s3.postimg.cc/5s9jg2wtf/generos.png',
                         url=host,
                         ))

    return itemlist

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all(item):
    logger.info()

    itemlist = []
    next = False

    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, '<!-- LISTADO -->(.*?)<!-- LISTADO FIN -->')
    pattern = '<div class="bloqueportada_pieza"><a href="([^"]+)">(.*?)<img src="([^"]+)" alt="([^"]+)"'

    matches = re.compile(pattern, re.DOTALL).findall(data)

    first = item.first
    last = first + 19
    if last > len(matches):
        last = len(matches)
        next = True

    for scrapedurl, premium, scrapedthumbnail, scrapedtitle in matches[first:last]:

        if 'PREMIUM' in premium:
            continue
        url = host+scrapedurl
        thumbnail = scrapedthumbnail
        title = scrapedtitle.replace (' - Película Online', '')

        new_item = Item(channel=item.channel,
                        title=title,
                        contentTitle=title,
                        url=url,
                        action='findvideos',
                        thumbnail=thumbnail,
                        infoLabels = {'year': '-'}
                         )

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb = True)

    url_next_page = item.url
    first = last

    if url_next_page:
        itemlist.append(Item(channel=item.channel,title="Siguiente >>", url=url_next_page, action='list_all',
                             first=first))

    return itemlist


def seccion(item):
    logger.info()

    itemlist = []
    duplicado = []
    data = get_source(item.url)

    patron = 'menu-item-object-category menu-item-\d+"><a href="([^"]+)">([^<]+)<\/a><\/li>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = host+scrapedurl
        title = scrapedtitle
        thumbnail = ''
        if url not in duplicado:
            itemlist.append(Item(channel=item.channel,
                                 action='list_all',
                                 title=title,
                                 url=url,
                                 thumbnail=thumbnail,
                                 first=0
                                 ))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto
    item.first = 0

    try:
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []



def findvideos(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    pattern = '<a href="([^"]+)"><div class="boton_version">Idioma:.*?src="([^"]+)"> Subtitulos: ([^<]+)</div>'
    matches = re.compile(pattern, re.DOTALL).findall(data)
    title = ''
    '''if matches:
        for url, lang_data, sub_info in matches:
            lang = name="keywords" content=
            title = set_lang(lang, sub_info)
            new_data = get_source(host+url)
            url_list = scrapertools.find_multiple_matches(new_data, 'label:\s?"([^"]+)",\s?file:\s?"([^"]+)"')
            for quality, url in url_list:
                quality +='p'
                itemlist.append(Item(channel=item.channel,
                                     title='Directo %s[%s]' % (title, quality),
                                     url=url,
                                     action='play',
                                     language=IDIOMAS.get(lang, 'VO'),
                                     quality=quality,
                                     server='directo',
                                     infoLabels=item.infoLabels
                                     ))
    else:
        try:
            lang_data, sub_info = scrapertools.find_single_match(data, '>Idioma:.*?src="([^"]+)"> Subtitulos: ([^<]+)</div>')

            if lang_data:
                lang = languages_from_flags(lang_data, '/img/banderas/', 'jpg')
                title = set_lang(lang, sub_info)
        except:
            lang = 'VO'
            title = ' [%s]' % lang
        '''

    lang = lang_from_keywords(data)
    url_list = scrapertools.find_multiple_matches(data, 'label:\s?"([^"]+)",\s?file:\s?"([^"]+)"')
    for quality, url in url_list:
        quality += 'p'
        if not config.get_setting('unify'):
            title = '[%s]' % lang
        itemlist.append(Item(channel=item.channel,
                                 title='Directo %s [%s]' % (title, quality),
                                 url=url,
                                 action='play',
                                 language=lang,
                                 quality=quality,
                                 server='directo',
                                 infoLabels=item.infoLabels
                                 ))

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    itemlist = sorted(itemlist, key=lambda it: it.language)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle,
                 ))


    return itemlist

def lang_from_keywords(data):
    list_keywords = scrapertools.find_single_match(data, 'name="keywords" content="([^"]+)"')
    if 'español' in list_keywords:
        lang = 'CAST'
    elif 'subtitul' in list_keywords:
        lang = 'VOS'
    else:
        lang = 'VO'
    return lang

def languages_from_flags(lang_data, path, ext):
    logger.info()
    language = []
    """
    Obtiene los idiomas desde banderas en formatos del tipo url imagen por ejemplo "/img/banderas/es.png"
        
    lang_data: string conteniendo los idiomas puede ser 1 o mas
    path: string con la url donde se encuentra la bandera
    ext: string con la extension de la imagen sin el punto por ejemplo png
        
    Retorna una lista de idiomas si hubiese mas de 1 o un string en caso de ser solo 1
        """

    lang_list = scrapertools.find_multiple_matches(lang_data, '%s(.*?).%s' % (path, ext))
    if len(lang_list) == 1:
        return lang_list[0]
    else:
        for lang in lang_list:
                language.append(lang)
    return language

def set_lang(lang, sub_info):
    logger.info()

    if lang.lower() != 'es' and sub_info.lower() != 'no':
        lang = 'VOS'
    title = ''
    if not config.get_setting('unify'):
        title = ' [%s]' % IDIOMAS.get(lang, 'VO')

    return title