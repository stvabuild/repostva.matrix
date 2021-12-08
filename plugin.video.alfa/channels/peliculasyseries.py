# -*- coding: utf-8 -*-
# -*- Channel PeliculasySeries -*-
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


IDIOMAS = {'la': 'Latino', 'lat':'Latino', 'cas':'Castellano','es': 'Castellano', 'vs': 'VOSE', 'vos':'VOSE', 'vo':'VO',
           'ori':'VO', 'so':'VOS', 'sor':'VOS'}
list_language = list(IDIOMAS.values())

list_quality = ['TS','Screener','DVDRip','HDRip', 'HDTV', 'micro720', 'micro1080']

list_servers = ['openload', 'rapidvideo', 'powvideo', 'gamovideo', 'streamplay', 'flashx', 'clipwatching', 'vidoza',
                'thevideome']

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', 'peliculasyseries')
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', 'peliculasyseries')

host = 'https://peliculasyseries.me/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='menu_movies',
                         thumbnail= get_thumb('movies', auto=True)))
    itemlist.append(Item(channel=item.channel, title='Series', url=host+'series', action='list_all', type='tvshows',
                         thumbnail= get_thumb('tvshows', auto=True)))
    itemlist.append(
        item.clone(title="Buscar", action="search", url=host + 'buscar/q/', thumbnail=get_thumb("search", auto=True),
                   extra='movie'))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)
    autoplay.show_option(item.channel, itemlist)

    return itemlist

def menu_movies(item):
    logger.info()

    itemlist=[]

    itemlist.append(Item(channel=item.channel, title='Todas', url=host + 'movies', action='list_all',
                         thumbnail=get_thumb('all', auto=True), type='movies'))
    itemlist.append(Item(channel=item.channel, title='Genero', action='section',
                         thumbnail=get_thumb('genres', auto=True), type='movies'))

    return itemlist

def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def get_language(lang_data):
    logger.info()
    language = []
    lang_data = lang_data.replace('language-ES', '').replace('medium', '').replace('serie', '').replace('-','')
    if 'class' in lang_data:
        lang_list = scrapertools.find_multiple_matches(lang_data, 'class=" ([^"]+)"')
    else:
        return lang_data.strip()

    for lang in lang_list:
       if lang not in IDIOMAS:
           lang = 'VOS'
       if lang not in language:
            language.append(IDIOMAS[lang])
    return language

def section(item):
    logger.info()
    itemlist=[]
    duplicados=[]
    data = get_source(host)
    data = scrapertools.find_single_match(data, 'data-toggle="dropdown">Géneros.*?multi-column-dropdown">.*?"clearfix"')
    if 'Genero' in item.title:
        patron = '<li><a href="([^"]+)">([^<]+)</a>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        if title not in duplicados:
            itemlist.append(Item(channel=item.channel, url=scrapedurl, title=title, action='list_all',
                                 type=item.type))
            duplicados.append(title)

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    if item.type ==  'movies':
        patron = '<div class="col-md-2 w3l-movie-gride-agile"><a href="([^"]+)" class=".*?">'
        patron += '<img src="([^"]+)" title="([^"]+)" class="img-responsive".*?'
        patron += '<div class="calidad" >([^<]+)</div> <div class="audio-info">'
        patron += '(.*?)<div class="w3l-action-icon">.*?<p>([^<]+)</p>'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedurl, scrapedthumbnail, scrapedtitle, quality, lang_data, year in matches:

            title = '%s [%s] [%s]' % (scrapedtitle, year, quality)
            if 'screener' in quality.lower():
                quality = 'Screener'
            contentTitle = scrapedtitle
            thumbnail = scrapedthumbnail
            url = scrapedurl
            language = get_language(lang_data)
            itemlist.append(item.clone(action='findvideos',
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            contentTitle=contentTitle,
                            language=language,
                            quality=quality,
                            infoLabels={'year':year}))

    elif item.type ==  'tvshows':
        patron = '<div class="col-md-2 w3l-movie-gride-agile"><a href="([^"]+)" class=".*?">'
        patron += '<img src="([^"]+)" title="([^"]+)" class="img-responsive".*?<p>([^<]+)</p>'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedurl, scrapedthumbnail, scrapedtitle, year in matches:
            title = scrapedtitle
            contentSerieName = scrapedtitle
            thumbnail = scrapedthumbnail
            url = scrapedurl

            itemlist.append(item.clone(action='seasons',
                            title=title,
                            url=url,
                            thumbnail=thumbnail,
                            contentSerieName=contentSerieName,
                            context=filtertools.context(item, list_language, list_quality),
                            infoLabels={'year':year}))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    #  Paginación

    url_next_page = scrapertools.find_single_match(data,"<a class='last' href='([^']+)'>»</a>")
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_all'))

    return itemlist

def seasons(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron='<a href="([^"]+)"><img class="thumb-item" src="([^"]+)" alt="[^"]+" >'
    patron += '<div class="season-item">Temporada (\d+)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels
    for scrapedurl, scrapedthumbnail, season in matches:
        infoLabels['season']=season
        title = 'Temporada %s' % season
        itemlist.append(Item(channel=item.channel, title=title, url=scrapedurl, action='episodesxseasons',
                             thumbnail=scrapedthumbnail, infoLabels=infoLabels))
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
    patron ='class="row-serie-item"><a href="([^"]+)">.*?<img class="episode-thumb-item" src="([^"]+)" alt="([^"]+)" >'
    patron += '<divclass="audio-info-series">(.*?)<div class="episode-item">%s+x(\d+)</div>' % item.infoLabels['season']
    matches = re.compile(patron, re.DOTALL).findall(data)

    infoLabels = item.infoLabels

    for scrapedurl, scrapedthumbnail, scrapedtitle, lang_data, scrapedepisode in matches:

        infoLabels['episode'] = scrapedepisode
        url = scrapedurl
        language = get_language(lang_data)
        title = '%sx%s - %s %s' % (infoLabels['season'], infoLabels['episode'], scrapedtitle, language)

        itemlist.append(Item(channel=item.channel, title= title, url=url, action='findvideos',
                             thumbnail=scrapedthumbnail, language=language, infoLabels=infoLabels))

    itemlist = filtertools.get_links(itemlist, item, list_language)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def findvideos(item):
    logger.info()
    from lib import generictools
    itemlist = []
    data = get_source(item.url)
    patron = '<div class="available-source" ><div class="([^"]+)">.*?'
    patron += 'data-data="([^"]+)".*?<span class="quality-text">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for lang_data, scrapedurl, quality in matches:
        lang = get_language(lang_data)
        if 'screener' in quality.lower():
            quality = 'Screener'

        quality = quality
        title = '%s [%s] [%s]'
        url = base64.b64decode(scrapedurl[1:])

        itemlist.append(
            Item(channel=item.channel, url=url, title=title, action='play', quality=quality, language=IDIOMAS[lang],
                 infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % (x.server.capitalize(), x.quality, x.language))

    # Requerido para Filtrar enlaces

    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)

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
        return search_results(item)
    else:
        return []

def search_results(item):
    logger.info()

    itemlist=[]

    data=get_source(item.url)
    patron = '<li class="search-results-item media-item" .*?<a href="([^"]+)" title="([^"]+)">.*?'
    patron += '<img class="content" src="([^"]+)" .*?>(Pelicula|Serie) del año([^<]+)</p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumb, content_type, year in matches:

        title = scrapedtitle
        if len(year)==0:
             year = '-'
        url = scrapedurl
        thumbnail = scrapedthumb
        if not '/serie' in url:
            action = 'findvideos'
        else:
            action = 'seasons'

        new_item=Item(channel=item.channel, title=title, url=url, thumbnail=thumbnail, action=action,
                      infoLabels={'year':year})
        if new_item.action == 'findvideos':
            new_item.contentTitle = new_item.title
        else:
            new_item.contentSerieName = new_item.title

        itemlist.append(new_item)

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas']:
            item.url = host + 'movies'
        elif categoria == 'infantiles':
            item.url = host + 'genero/animation/'
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
