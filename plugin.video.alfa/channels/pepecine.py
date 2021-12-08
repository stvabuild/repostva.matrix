# -*- coding: utf-8 -*-
# -*- Channel PepeCine -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channelselector import get_thumb
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from channels import filtertools
from channels import autoplay
from platformcode import config, logger

IDIOMAS = {'la': 'LAT', 'es': 'CAST', 'sub': 'VOSE', 'si': 'VOS', 'en': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['rapidvideo', 'verystream', 'streamplay']

host = 'https://verencasa.com/'
referer = 'https://pepecine.to/'
sec_host = host #'https://pepechino.hopto.org/'

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist = []

    itemlist.append(Item(channel=item.channel, title='Peliculas', action='submenu', url='?type=movie',
                         thumbnail=get_thumb('movies', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Series', action='submenu', url='?type=series',
                         thumbnail=get_thumb('tvshows', auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def submenu(item):
    logger.info()

    itemlist = []

    if 'series' in item.url:
        itemlist.append(
            Item(channel=item.channel, title='Nuevos capitulos',
                 url=host + 'last/estrenos-episodios-online.php', action='list_news',
                 thumbnail=get_thumb('new episodes', auto=True), first=0, news_type='series'))
    else:
        itemlist.append(
            Item(channel=item.channel, title='Ultimas', url= host + 'last/estrenos-peliculas-online.php',
                 action='list_news', thumbnail=get_thumb('last', auto=True), first=0, news_type='movies'))

    itemlist.append(
        Item(channel=item.channel, title='Todas', url=host + 'secure/titles%s' % item.url, action='list_all',
             thumbnail=get_thumb('all', auto=True)))

    itemlist.append(Item(channel=item.channel, title='Generos', url='%ssecure/titles%s&genre=' % (host, item.url),
                         action='genres', thumbnail=get_thumb('genres', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url= sec_host + 'secure/search/',
                         thumbnail=get_thumb("search", auto=True), search_type=item.title.lower()))

    return itemlist


def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def get_language(lang_data):
    logger.info()
    language = []
    lang_list = scrapertools.find_multiple_matches(lang_data, '/(.*?).png\)')
    for lang in lang_list:
        if lang not in language:
            language.append(lang)
    return language


def list_news(item):
    logger.info()
    itemlist = []
    listed = []
    next = False

    data = get_source(item.url, referer=referer)
    patron = '<td><a href=([^ ]+) target="_parent"><img src=([^ ]+) class="s8" alt="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)

    first = item.first
    last = first + 19
    if last > len(matches):
        last = len(matches)
        next = True

    for url, thumb, title in matches[first:last]:
        infoLabels = dict()

        id = scrapertools.find_single_match(url, 'titles/([^/]+)')

        if item.news_type == 'movies':
            filter_thumb = thumb.replace("https://image.tmdb.org/t/p/w185_and_h278_bestv2", "")
            filter_list = {"poster_path": filter_thumb.strip()}
            filter_list = list(filter_list.items())
            infoLabels['filtro'] = filter_list
            url = '%ssecure/titles/%s?titleId=%s' % (host, id, id)
        else:
            se_ep = scrapertools.get_season_and_episode(title)
            contentSerieName = title.replace(se_ep.replace('x0', 'x'), '').strip()
            if not config.get_setting('unify'):
                title = '%s - %s' % (se_ep, contentSerieName)
            se_ep = se_ep.split('x')
            url = '%ssecure/titles/%s?titleId=%s&seasonNumber=%s' % (host, id, id, se_ep[0])

        thumb = re.sub("p/(.*?)/", "p/original/", thumb)

        if url not in listed:
            new_item = Item(channel=item.channel, action="findvideos", title=title, url=url, thumbnail=thumb,
                            infoLabels=infoLabels)

            if item.news_type == 'movies':
                new_item.contentTitle = title
                new_item.action = 'findvideos'

            else:
                ep = int(se_ep[1])
                new_item.contentSerieName = contentSerieName
                new_item.url += '&episodeNumber=%s' % ep
                new_item.ep_info = ep
                new_item.infoLabels['season'] = se_ep[0]
                new_item.infoLabels['episode'] = ep

            listed.append(url)

            itemlist.append(new_item)

    tmdb.set_infoLabels(itemlist, True)

    if not next:
        url_next_page = item.url
        first = last

    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, action='list_news', first=first))

    return itemlist


def list_all(item):
    logger.info()

    itemlist = []

    json_data = httptools.downloadpage(item.url, headers={'Referer': referer}).json
    if len(json_data) > 0:
        for elem in json_data['pagination']['data']:
            year = elem['year']
            lang = elem['language']
            url = '%ssecure/titles/%s?titleId=%s' % (host, elem['id'], elem['id'])
            if elem['poster']:
                thumb = elem['poster']
            else:
                thumb = ''
            new_item = Item(channel=item.channel, title=elem['name'], thumbnail=thumb, url=url,
                            infoLabels={'year': year})

            if 'movie' in item.url:
                new_item.contentTitle = elem['name']
                new_item.action = 'findvideos'
                if not config.get_setting('unify') and year != '-':
                    new_item.title += ' [COLOR khaki](%s)[/COLOR]' % year
            else:
                new_item.contentSerieName = elem['name']
                new_item.action = 'seasons'
            itemlist.append(new_item)

        tmdb.set_infoLabels(itemlist, True)

    ## Pagination

    try:
        next_page = '%s%s' % (item.url, json_data['pagination']['next_page_url'].replace('/?', '&'))
        itemlist.append(Item(channel=item.channel, action='list_all', url=next_page, title='Siguiente >>'))
    except:
        pass

    return itemlist


def genres(item):
    logger.info()

    itemlist = []

    genre_list = ["Accion", "Animacion", "Aventura", "Belica", "CienciaFiccion", "Comedia", "Crimen", "Documental",
                  "Drama", "Familia", "Fantasia", "Guerra", "Historia", "Kids", "Misterio", "Musica", "News",
                  "PeliculaDeTV",
                  "Reality", "Romance", "Soap", "Suspense", "Talk", "Terror", "Thriller", "Western"]

    for genre in genre_list:
        url = '%s%s' % (item.url, genre)
        itemlist.append(Item(channel=item.channel, title=genre, url=url, action='list_all'))

    return itemlist


def seasons(item):
    logger.info()

    itemlist = []
    infoLabels = item.infoLabels

    json_data = httptools.downloadpage(item.url, headers={'Referer': referer}).json

    if len(json_data) > 0:
        for elem in json_data['title']['seasons']:
            infoLabels['season'] = elem['number']
            url = '%s&seasonNumber=%s' % (item.url, elem['number'])
            title = 'Temporada %s' % elem['number']
            itemlist.append(Item(channel=item.channel, action='episodesxseason', title=title, url=url,
                                 infoLabels=infoLabels))

    tmdb.set_infoLabels(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(
            Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                 action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = []
    infoLabels = item.infoLabels

    json_data = httptools.downloadpage(item.url, headers={'Referer': referer}).json

    if len(json_data) > 0:
        for elem in json_data['title']['season']['episodes']:

            infoLabels['episode'] = elem['episode_number']
            ep_info = elem['episode_number']
            url = '%s&episodeNumber=%s' % (item.url, elem['episode_number'])
            title = '%s' % elem['name']
            if not config.get_setting('unify'):
                title = '%sx%s %s' % (item.infoLabels['season'], infoLabels['episode'], elem['name'])
            itemlist.append(Item(channel=item.channel, action='findvideos', title=title, ep_info=ep_info, url=url,
                                 infoLabels=infoLabels))
    tmdb.set_infoLabels(itemlist, True)

    return itemlist


def findvideos(item):
    logger.info()

    itemlist = []
    item.url = re.sub(host, sec_host, item.url)
    is_tvshow = False
    json_data = httptools.downloadpage(item.url, headers={'Referer': referer}).json

    if len(json_data) > 0:
        videos_info = json_data['title']['videos']

        if str(item.ep_info) != '':
            is_tvshow = True
            epi = item.ep_info
            season = item.infoLabels["season"]

        for elem in videos_info:
            lang = scrapertools.find_single_match(elem['name'], '/(.*?).png')

            if len(lang) > 2 and not 'sub' in lang:
                lang = lang[-2:]
            elif 'sub' in lang:
                lang = 'sub'
            # else:
            #    lang = 'en'

            url = elem['url']

            lang = IDIOMAS.get(lang, 'VO')

            if not config.get_setting('unify'):
                title = ' [%s]' % lang
            else:
                title = ''
            if not is_tvshow or (elem['season'] == season and elem['episode'] == epi):

                itemlist.append(Item(channel=item.channel, title='%s' + title, action='play', url=url,
                                     language=lang, infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if item.contentType != 'episode':
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
            itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                     url=item.url,
                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

    return itemlist


def search_results(item):
    logger.info()

    itemlist = []
    series_list = []
    movies_list = []

    json_data = httptools.downloadpage(item.url, headers={'Referer': referer}).json

    if json_data.get('results', ''):
        for elem in json_data['results']:
            url = '%ssecure/titles/%s?titleId=%s' % (item.host, elem['id'], elem['id'])
            if not 'videos' in elem:
                continue
            try:
                year = elem['year']
                name = elem['name']
                is_series = elem['is_series']
            except:
                name = elem['popular_credits'][0]['name']
                is_series = elem['popular_credits'][0]['is_series']
                try:
                    year = elem['popular_credits'][0]['year']
                except:
                    year = '-'

            title = name

            if is_series:

                if not config.get_setting('unify') and not item.search_type:
                    title += ' [COLOR khaki](Serie)[/COLOR]'

                series_list.append(Item(channel=item.channel, title=title, url=url, action='seasons',
                                        contentSerieName=name))
            else:

                if not config.get_setting('unify') and year != '-':
                    title += ' [COLOR khaki](%s)[/COLOR]' % year

                movies_list.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                                        contentTitle=name, infoLabels={'year': year}))

        if item.search_type == 'series':
            itemlist = series_list
        elif item.search_type == 'peliculas':
            itemlist = movies_list
        else:
            itemlist = series_list + movies_list
    tmdb.set_infoLabels(itemlist, True)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.host =  sec_host
    #item.url =  item.host + 'secure/search/'
    if not item.url:
        item.url = sec_host + 'secure/search/'

    item.url = '%s%s?type=&limit=30' % (item.url, texto)

    if texto != '':
        return search_results(item)
    else:
        return []


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + 'last/estrenos-peliculas-online.php'
            item.news_type = 'movies'
            item.first = 0
        elif categoria == 'series':
            item.url = host + 'last/estrenos-episodios-online.php'
            item.first = 0
            item.news_type = 'series'
        elif categoria == 'infantiles':
            item.url = host + 'secure/titles?type=movie&genre=Animacion'
        elif categoria == 'terror':
            item.url = host + 'secure/titles?type=movie&genre=Terror'
        elif categoria == 'documentales':
            item.url = host + 'secure/titles?type=movie&genre=Documental'

        if item.first != 0:
            itemlist = list_all(item)
        else:
            itemlist = list_news(item)

        if itemlist[-1].title == 'Siguiente >>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
