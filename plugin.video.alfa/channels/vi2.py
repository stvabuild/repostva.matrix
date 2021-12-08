# -*- coding: utf-8 -*-
# -*- Channel Vi2.co -*-
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


IDIOMAS = {'Latino': 'LAT', 'Español':'CAST', 'Subtitulado': 'VOSE', 'VO': 'VO'}
list_language = list(IDIOMAS.values())

list_quality = ['Full HD 1080p',
                'HDRip',
                'DVDScreener',
                '720p',
                'Ts Screener hq',
                'HD Real 720p',
                'DVDRip',
                'BluRay-1080p',
                'BDremux-1080p']

list_servers = [
    'directo',
    'openload',
    'rapidvideo',
    'jawcloud',
    'cloudvideo',
    'upvid',
    'vevio',
    'gamovideo'
]

host = 'http://vi2.co'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='select_menu', type='peliculas',
                         thumbnail= get_thumb('movies', auto=True)))
    # itemlist.append(Item(channel=item.channel, title='Series', url=host+'serie', action='select_menu', type='series',
    #                      thumbnail= get_thumb('tvshows', auto=True)))


    autoplay.show_option(item.channel, itemlist)

    return itemlist

def select_menu(item):
    logger.info()

    itemlist=[]
    url = host + '/%s/es/' % item.type
    itemlist.append(Item(channel=item.channel, title='Streaming', action='sub_menu',
                         thumbnail=get_thumb('all', auto=True), type=item.type))

    itemlist.append(Item(channel=item.channel, title='Torrent', action='sub_menu',
                         thumbnail=get_thumb('all', auto=True), type=item.type))

    itemlist.append(Item(channel=item.channel, title='Generos', action='section', url=url,
                         thumbnail=get_thumb('genres', auto=True), type='all'))

    itemlist.append(Item(channel=item.channel, title='Por Año', action='section', url=url,
                         thumbnail=get_thumb('year', auto=True), type='all'))

    return itemlist

def sub_menu(item):
    logger.info()

    itemlist = []
    url = host + '/%s/es/ajax/1/' % item.type
    link_type = item.title.lower()
    if link_type == 'streaming':
        link_type = 'flash'
    movies_options = ['Todas', 'Castellano', 'Latino', 'VOSE']
    tv_options = ['Ultimas', 'Ultimas Castellano', 'Ultimas Latino', 'Ultimas VOSE']

    if item.type == 'peliculas':
        title = movies_options
        thumb_1 = 'all'
    else:
        thumb_1 = 'last'
        title = tv_options

    itemlist.append(Item(channel=item.channel, title=title[0], url=url+'?q=%s' % link_type,
                         action='list_all', thumbnail=get_thumb(thumb_1, auto=True), type=item.type,
                         link_type=link_type))

    itemlist.append(Item(channel=item.channel, title=title[1],
                         url=url + '?q=%s+espanol' % link_type, action='list_all',
                         thumbnail=get_thumb('cast', auto=True), type=item.type, send_lang='Español',
                         link_type=link_type))

    itemlist.append(Item(channel=item.channel, title=title[2],
                         url=url + '?q=%s+latino' % link_type, action='list_all',
                         thumbnail=get_thumb('lat', auto=True), type=item.type, send_lang='Latino',
                         link_type=link_type))

    itemlist.append(Item(channel=item.channel, title=title[3],
                         url=url + '?q=%s+subtitulado' % link_type, action='list_all',
                         thumbnail=get_thumb('vose', auto=True), type=item.type, send_lang='VOSE',
                         link_type=link_type))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=url + '?q=',
                         thumbnail=get_thumb("search", auto=True), type=item.type, link_type=link_type))

    return itemlist

def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data

def section(item):
    logger.info()
    itemlist=[]
    excluded = ['latino', 'español', 'subtitulado', 'v.o.', 'streaming', 'torrent']
    full_data = get_source(item.url)
    data = scrapertools.find_single_match(full_data, 'toptags-container(.*?)<div class="android-more-section">')

    patron = 'href="([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = host+scrapedurl.replace('/?','/ajax/1/?')
        if (item.title=='Generos' and title.lower() not in excluded and not title.isdigit()) or (item.title=='Por Año' and title.isdigit()):
            itemlist.append(Item(channel=item.channel, url=url, title=title, action='list_all',  type=item.type))

    return itemlist


def list_all(item):
    from core import jsontools
    logger.info()
    itemlist = []
    listed =[]
    quality=''
    infoLabels = {}
    json_data= jsontools.load(get_source(item.url))
    data = json_data['render']
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    #if item.type ==  'peliculas':
    patron = '<img\s*class="cover"[^>]+src="([^"]+)"\s*data-id="\d+"\s*'
    patron +='alt="Ver\s*([^\(]+)(.*?)">\s*'
    patron += '<div\s*class="mdl-card__menu">\s*<a\s*class="clean-link"\s*href="([^"]+)">'
    patron += '.*?<span\s*class="link-size">([^<]*)<'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, extra_info, scrapedurl , size in matches:
        if item.send_lang != '':
            lang = item.send_lang
        else:
            lang = ''
        year='-'
        extra_info = extra_info.replace('(', '|').replace('[','|').replace(')','').replace(']','')
        extra_info = extra_info.split('|')
        for info in extra_info:
            info = info.strip()
            if 'Rip' in info or '1080' in info or '720' in info or 'Screener' in info:
                quality = info
            if 'ingl' in info.lower():
                info = 'VO'
            if info in IDIOMAS:
                lang = info
            elif info.isdigit():
                year = info

        if lang in IDIOMAS:
            lang = IDIOMAS[lang]

        title = '%s' % scrapedtitle.strip()
        if not config.get_setting('unify'):
            if year.isdigit():
                title = '%s [%s]' % (title, year)
            if quality != '':
                title = '%s [%s]' % (title, quality)
            if lang != '':
                title = '%s [%s]' % (title, lang)

        thumbnail = host+scrapedthumbnail
        url = host+scrapedurl
        if item.type == 'series':
            season, episode = scrapertools.find_single_match(scrapedtitle, '(\d+)x(\d+)')
            infoLabels['season'] = season
            infoLabels['episode'] = episode
        else:
            infoLabels['year'] = year

        if title not in listed:
            new_item = Item(channel=item.channel,
                            title=title,
                            url=url,
                            action='findvideos',
                            thumbnail=thumbnail,
                            type=item.type,
                            language = lang,
                            quality=quality,
                            link_type=item.link_type,
                            torrent_data= size,
                            infoLabels = infoLabels
                            )

            if item.type == 'peliculas' or item.type == 'all':
                new_item.contentTitle = scrapedtitle
            else:
                scrapedtitle = scrapedtitle.split(' - ')
                new_item.contentSerieName = scrapedtitle[0]

            itemlist.append(new_item)
            listed.append(title)

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    itemlist.sort(key=lambda it: it.title)
    #  Paginación

    if json_data['next']:
        actual_page = scrapertools.find_single_match(item.url, 'ajax/(\d+)/')
        next_page =int(actual_page) + 1
        url_next_page = item.url.replace('ajax/%s' % actual_page, 'ajax/%s' % next_page)
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, type=item.type,
                                   action='list_all', send_lang=item.send_lang))

    return itemlist


def findvideos(item):
    logger.info()
    import base64
    itemlist = []
    server = ''
    data = get_source(item.url)
    pre_url = scrapertools.find_single_match(data, 'class="inside-link" href="([^"]+)".*?<button type="button"')
    data = get_source(host+pre_url)
    patron = 'data-video="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    lang = item.language
    quality = item.quality

    for url in matches:
        title = ''
        link_type = ''
        server = ''
        url = base64.b64decode(url.encode('utf8')).decode('utf8')

        if 'torrent' in url:
            if item.link_type == 'torrent' or item.type == 'all':
                server = 'torrent'
                link_type = 'torrent'
                title = ' [%s]' % item.torrent_data
        elif 'torrent' not in url:
            link_type = 'flash'


        if link_type == item.link_type.lower() or item.type == 'all':
            itemlist.append(Item(channel=item.channel, url=url, title='%s'+title, action='play', server=server,
                                 language=lang, quality=quality, infoLabels=item.infoLabels))


    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())


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
    url = '%spelicula+%s+%s&o=2' % (item.url, texto, item.link_type)
    #Parche busqueda global (solo vale para peliculas en streaming)
    if not item.url:
        item.type = 'peliculas'
        item.link_type = 'flash'
        ajax = '%s/%s/es/ajax/1/' % (host, item.type)
        url = '%s?q=%s+%s+%s&o=2' % (ajax, item.type, texto, item.link_type)

    item.url = url

    try:
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
