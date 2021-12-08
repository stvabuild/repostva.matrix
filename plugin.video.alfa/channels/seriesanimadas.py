# -*- coding: utf-8 -*-
# -*- Channel SeriesAnimadas -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import base64

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from lib import jsunpack
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger


IDIOMAS = {'latino': 'LAT', 'audio latino': 'LAT', 'sub español':'VOSE', 'subtitulado':'VOSE'}
list_language = list(IDIOMAS.values())

list_quality = []

list_servers = [
    'directo',
    'openload',
]

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'seriesanimadas')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'seriesanimadas')

host = 'https://www.seriesanimadas.net/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Nuevos Capitulos', url=host, action='new_episodes', type='tvshows',
                         thumbnail=get_thumb('new_episodes', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Ultimas', url=host + 'series/estrenos', action='list_all',
                         type='tvshows',
                         thumbnail=get_thumb('last', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'series', action='list_all', type='tvshows',
                         thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host + 'search?s=',
                         thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

def menu_movies(item):
    logger.info()

    itemlist=[]

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'movies', action='list_all',
                         thumbnail=get_thumb('all', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Por Año', action='section',
                         thumbnail=get_thumb('year', auto=True), type='movies'))

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = '<article class=".*?">.*? href="([^"]+)".*?<img src="([^"]+)".*?<h3 class="card-tvshow__title">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumbnail, scrapedtitle in matches:
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        url = scrapedurl
        action = 'seasons'

        new_item = Item(channel=item.channel,
                        action=action,
                        title=title,
                        url=url,
                        contentSerieName=scrapedtitle,
                        thumbnail=thumbnail,
                        )

        itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    url_next_page = scrapertools.find_single_match(data,'<li><a href="([^"]+)" rel="next">')
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='<div class="season__title">Temporada (\d+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if len(matches) == 0:
        item.type = 'Anime'
        return episodesxseasons(item)
    infoLabels = item.infoLabels
    for season in matches:
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=item.url, action='episodesxseasons',
                             infoLabels=infoLabels))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

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
        itemlist += episodesxseasons(tempitem)

    return itemlist

def episodesxseasons(item):
    logger.info()

    itemlist = []

    data=get_source(item.url)

    infoLabels = item.infoLabels
    if item.type == 'Anime':
        season = '1'
        patron = '<a class="episodie-list" href="([^"]+)" .*?</i> Episodio (\d+).*?</span>'
    else:
        season = item.infoLabels['season']

        patron = 'class="episodie-list" href="([^"]+)" title=".*?Temporada %s .*?pisodio (\d+).*?">' % season
    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        patron = 'class="episodie-list" href="([^"]+)" title=".*?pisodio (\d+).*?">'
        matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, episode in matches:
        infoLabels['episode'] = episode
        url = scrapedurl
        title = '%sx%s - Episodio %s' % (season, episode, episode)

        itemlist.append(Item(channel=item.channel, title= title, url=url,
                             action='findvideos', infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist[::-1]

def new_episodes(item):
    logger.info()

    itemlist = []

    data = get_source(item.url)
    patron = '<div class="card-episodie shadow-sm"><a href="([^"]+)".*?data-src="([^"]+)" alt="([^"]+)">'

    matches = re.compile(patron, re.DOTALL).findall(data)
    
    #logger.debug(matches)

    for scrapedurl, scrapedthumb, scrapedtitle in matches:
        
        pat = r'^(.*?)\s*(?:Episodio)?\s*(\d+)\s*(.*)'
        ctitle, ep, lang = scrapertools.find_single_match(scrapedtitle, pat)
        if len(ep) == 1:
            ep = '0'+ep
        title = '%s: 1x%s' % (ctitle, ep)
        language = IDIOMAS.get(lang.lower(), 'VOSE')

        if not config.get_setting('unify'):
            title += '[COLOR khaki] (%s)[/COLOR]' % language
        
        itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl,
                             thumbnail=scrapedthumb, contentSerieName=ctitle,
                             language=language, action='findvideos'))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = 'video\[(\d+)\] = .*?src="([^"]+)".*?;'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    for option, scrapedurl in matches:
        lang = scrapertools.find_single_match(data, '"#option%s">([^<]+)<' % str(option)).strip()
        language = IDIOMAS.get(lang.lower(), 'VOSE')
        
        quality = ''
        title = '%s (%s)'

        if 'redirect' in scrapedurl:
            url_data = httptools.downloadpage(scrapedurl).data
            url = scrapertools.find_single_match(url_data,'var redir = "([^"]+)";')
            if not url:
                url = scrapertools.find_single_match(url_data,'window.location.href = "([^"]+)";')
                
        else:
            url = scrapedurl
        
        if url != '':
            itemlist.append(
                Item(channel=item.channel, url=url, title=title, action='play', quality=quality,
                     language=language, infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.language))

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
         itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    itemlist = sorted(itemlist, key=lambda it: it.language)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

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
        if categoria in ['peliculas']:
            item.url = host + 'movies/'
        elif categoria == 'infantiles':
            item.url = host + 'genre/animacion/'
        elif categoria == 'terror':
            item.url = host + 'genre/terror/'
        item.type='movies'
        itemlist = list_all(item)
        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
