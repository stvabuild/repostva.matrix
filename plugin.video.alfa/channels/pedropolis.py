# -*- coding: utf-8 -*-
# -*- Channel PedroPolis -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re

from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger
from channelselector import get_thumb

__channel__ = "pedropolis"

host = "https://pedropolis.tv/"

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE', '0xFFFE2E2E', '0xFFFFD700']]
if __perfil__ < 3:
    color1, color2, color3, color4, color5 = perfil[__perfil__]
else:
    color1 = color2 = color3 = color4 = color5 = ""

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']

IDIOMAS = {'Latino': 'LAT'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['rapidvideo', 'streamango', 'fastplay', 'openload']



def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [item.clone(title="Peliculas", action="menumovies", text_blod=True,
                           viewcontent='movies', viewmode="movie_with_plot", thumbnail=get_thumb("channels_movie.png")),

                item.clone(title="Series", action="menuseries", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshows', url=host + 'tvshows/', viewmode="movie_with_plot",
                           thumbnail=get_thumb("channels_tvshow.png")),

                item.clone(title="Buscar", action="search", text_blod=True, extra='buscar',
                           thumbnail=get_thumb('search.png'), url=host)]
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def menumovies(item):
    logger.info()
    itemlist = [item.clone(title="Todas", action="peliculas", text_blod=True, url=host + 'pelicula/',
                           viewcontent='movies', viewmode="movie_with_plot"),
                item.clone(title="Más Vistas", action="peliculas", text_blod=True,
                           viewcontent='movies', url=host + 'tendencias/?get=movies', viewmode="movie_with_plot"),
                item.clone(title="Mejor Valoradas", action="peliculas", text_blod=True,
                           viewcontent='movies', url=host + 'tendencias/?get=movies', viewmode="movie_with_plot"),
                item.clone(title="Por año", action="p_portipo", text_blod=True, extra="Películas Por año",
                           viewcontent='movies', url=host, viewmode="movie_with_plot"),
                item.clone(title="Por género", action="p_portipo", text_blod=True, extra="Categorías",
                           viewcontent='movies', url=host, viewmode="movie_with_plot")]
    return itemlist


def menuseries(item):
    logger.info()
    itemlist = [item.clone(title="Todas", action="series", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshows', url=host + 'serie/', viewmode="movie_with_plot"),

                item.clone(title="Más Vistas", action="series", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshows', url=host + 'tendencias/?get=tv', viewmode="movie_with_plot"),

                item.clone(title="Mejor Valoradas", action="series", text_blod=True, extra='serie', mediatype="tvshow",
                           viewcontent='tvshows', url=host + 'calificaciones/?get=tv', viewmode="movie_with_plot")]

    return itemlist


def p_portipo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, '(?is)%s.*?</ul>' %item.extra)
    patron  = 'href="([^"]+).*?'
    patron += '>([^"<]+)'
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action = "peliculas",
                                   title = scrapedtitle,
                                   url = scrapedurl
                                   ))
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="poster">[^<]+<img src="([^"]+)" alt="([^"]+)">[^<]+'    		# img, title
    patron += '<div class="rating"><span class="[^"]+"></span>([^<]+)'  			# rating
    patron += '.*?<span class="quality">([^<]+)</span> </div>.*?<a href="([^"]+)">.*?'    # calidad, url
    patron += '<span>([^<]+)</span>.*?'                                             # year

    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedthumbnail, scrapedtitle, rating, quality, scrapedurl, year in matches:
        scrapedtitle = scrapedtitle.replace('Ver ', '').partition(' /')[0].partition(':')[0].replace(
            'Español Latino', '').strip()
        title = "%s [COLOR green][%s][/COLOR] [COLOR yellow][%s][/COLOR]" % (scrapedtitle, year, quality)

        itemlist.append(Item(channel=item.channel, action="findvideos", contentTitle=scrapedtitle,
	                         infoLabels={"year":year, "rating":rating}, thumbnail=scrapedthumbnail,
	                         url=scrapedurl, quality=quality, title=title))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    pagination = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')

    if pagination:
        itemlist.append(Item(channel=__channel__, action="peliculas", title="» Siguiente »",
                             url=pagination, folder=True, text_blod=True, thumbnail=get_thumb("next.png")))


    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?s={0}".format(texto))
    try:
        return sub_search(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    bloque = scrapertools.find_single_match(data, 'Resultados encontrados.*?class="widget widget_fbw_id')
    patron  = '(?is)<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += 'alt="([^"]+)" />.*?'  # url, img, title
    patron += '<span class="[^"]+">([^<]+)</span>.*?'  # tipo
    patron += '<span class="year">([^"]+)'  # year
    matches = scrapertools.find_multiple_matches(bloque, patron)
    for scrapedurl, scrapedthumbnail, scrapedtitle, tipo, year in matches:
        title = scrapedtitle
        if tipo == ' Serie ':
            contentType = 'tvshow'
            action = 'temporadas'
            title += ' [COLOR red](' + tipo + ')[/COLOR]'
        else:
            contentType = 'movie'
            action = 'findvideos'
            title += ' [COLOR green](' + tipo + ')[/COLOR]'
        itemlist.append(item.clone(title=title, url=scrapedurl, contentTitle=scrapedtitle, extra='buscar',
                                   action=action, infoLabels={"year": year}, contentType=contentType,
                                   thumbnail=scrapedthumbnail, text_color=color1, contentSerieName=scrapedtitle))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    pagination = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')
    if pagination:
        itemlist.append(Item(channel=item.channel, action="sub_search",
                             title="» Siguiente »", url=pagination, thumbnail=get_thumb("next.png")))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host + 'movies/'
        elif categoria == 'infantiles':
            item.url = host + "genre/animacion/"
        elif categoria == 'terror':
            item.url = host + "genre/terror/"
        else:
            return []

        itemlist = peliculas(item)
        if itemlist[-1].title == "» Siguiente »":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def series(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<div class="poster"> <img src="([^"]+)"'
    patron += ' alt="([^"]+)">.*?'
    patron += '<a href="([^"]+)">'
    matches = scrapertools.find_multiple_matches(data, patron)

    for scrapedthumbnail, scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapedtitle.replace('&#8217;', "'")
        itemlist.append(Item(channel=__channel__, title=scrapedtitle, extra='serie',
                             url=scrapedurl, thumbnail=scrapedthumbnail,
                             contentSerieName=scrapedtitle, show=scrapedtitle,
                             action="temporadas", contentType='tvshow'))
    tmdb.set_infoLabels(itemlist, __modo_grafico__)

    pagination = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)" />')

    if pagination:
        itemlist.append(Item(channel=__channel__, action="series", title="» Siguiente »", url=pagination,
                             thumbnail=get_thumb("next.png")))
    return itemlist


def temporadas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<span class="title">([^<]+)<i>.*?'  # season
    patron += '<img src="([^"]+)"></a></div>'     # img
    matches = scrapertools.find_multiple_matches(data, patron)
    if len(matches) > 1:
        for scrapedseason, scrapedthumbnail in matches:
            scrapedseason = " ".join(scrapedseason.split())
            temporada = scrapertools.find_single_match(scrapedseason, '(\d+)')
            new_item = item.clone(action="episodios", season=temporada, thumbnail=scrapedthumbnail, extra='serie')
            new_item.infoLabels['season'] = temporada
            new_item.extra = ""
            itemlist.append(new_item)
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
        for i in itemlist:
            i.title = "%s. %s" % (i.infoLabels['season'], i.infoLabels['tvshowtitle'])
            if i.infoLabels['title']:
                # Si la temporada tiene nombre propio añadírselo al titulo del item
                i.title += " - %s" % (i.infoLabels['title'])
            if 'poster_path' in i.infoLabels:
                # Si la temporada tiene poster propio remplazar al de la serie
                i.thumbnail = i.infoLabels['poster_path']
        itemlist.sort(key=lambda it: it.title)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series",
                             text_color=color1, thumbnail=get_thumb("videolibrary_tvshow.png"), fanart=fanart_host))
        return itemlist
    else:
        return episodios(item)


def episodios(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="imagen"><a href="([^"]+)">.*?'  # url
    patron += '<div class="numerando">(.*?)</div>.*?'     # numerando cap
    patron += '<a href="[^"]+">([^<]+)</a>'               # title de episodios
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedname in matches:
        scrapedtitle = scrapedtitle.replace('--', '0')
        patron = '(\d+) - (\d+)'
        match = re.compile(patron, re.DOTALL).findall(scrapedtitle)
        season, episode = match[0]
        if 'season' in item.infoLabels and int(item.infoLabels['season']) != int(season):
            continue
        title = "%sx%s: %s" % (season, episode.zfill(2), scrapertools.unescape(scrapedname))
        new_item = item.clone(title=title, url=scrapedurl, action="findvideos", text_color=color3, contentTitle=title,
                              contentType="episode", extra='serie')
        if 'infoLabels' not in new_item:
            new_item.infoLabels = {}
        new_item.infoLabels['season'] = season
        new_item.infoLabels['episode'] = episode.zfill(2)
        itemlist.append(new_item)
    # TODO no hacer esto si estamos añadiendo a la videoteca
    if not item.extra:
        # Obtenemos los datos de todos los capítulos de la temporada mediante multihilos
        tmdb.set_infoLabels(itemlist, __modo_grafico__)
        for i in itemlist:
            if i.infoLabels['title']:
                # Si el capitulo tiene nombre propio añadírselo al titulo del item
                i.title = "%sx%s: %s" % (i.infoLabels['season'], i.infoLabels['episode'], i.infoLabels['title'])
            if 'poster_path' in i.infoLabels:
                # Si el capitulo tiene imagen propia remplazar al poster
                i.thumbnail = i.infoLabels['poster_path']
    itemlist.sort(key=lambda it: int(it.infoLabels['episode']),
                  reverse=config.get_setting('orden_episodios', __channel__))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    # Opción "Añadir esta serie a la videoteca"
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=__channel__, title="Añadir esta serie a la videoteca", url=item.url,
                             action="add_serie_to_library", extra="episodios", show=item.show, category="Series",
                             text_color=color1, thumbnail=get_thumb("videolibrary_tvshow.png"), fanart=fanart_host))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div id="option-(\d+)".*?<iframe.*?src="([^"]+)".*?</iframe>'  # lang, url
    matches = re.compile(patron, re.DOTALL).findall(data)
    for option, url in matches:

        lang = scrapertools.find_single_match(data, '<li><a class="options" href="#option-%s">.*?</b>(.*?)<span' % option)
        lang = lang.lower().strip()
        idioma = {'latino': '[COLOR cornflowerblue](LAT)[/COLOR]',
                  'drive': '[COLOR cornflowerblue](LAT)[/COLOR]',
                  'castellano': '[COLOR green](CAST)[/COLOR]',
                  'español': '[COLOR green](CAST)[/COLOR]',
                  'subtitulado': '[COLOR red](VOS)[/COLOR]',
                  'ingles': '[COLOR red](VOS)[/COLOR]'}
        if lang in idioma:
            lang = idioma[lang]
        #  obtenemos los redirecionamiento de shorturl en caso de coincidencia
        if "bit.ly" in url:
            url = httptools.downloadpage(url, follow_redirects=False, only_headers=True).headers.get("location", "")
        itemlist.append(item.clone(channel=__channel__, url=url, title=item.contentTitle,
                                   action='play', language=lang))
    itemlist = servertools.get_servers_itemlist(itemlist)
    itemlist.sort(key=lambda it: it.language, reverse=False)
    for x in itemlist:
        if x.extra != 'directo':
            x.thumbnail = item.thumbnail
            x.title = "Ver en: [COLOR yellow](%s)[/COLOR] %s" % (x.server.title(), x.language)
            if item.extra != 'serie' and item.extra != 'buscar':
                x.title = "Ver en: [COLOR yellowgreen](%s)[/COLOR] [COLOR yellow](%s)[/COLOR] %s" % (
                    x.server.title(), x.quality, x.language)
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'serie':
        itemlist.append(Item(channel=__channel__, url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             thumbnail=get_thumb("videolibrary_movie.png"), contentTitle=item.contentTitle))
    return itemlist
