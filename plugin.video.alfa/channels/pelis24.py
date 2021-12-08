# -*- coding: utf-8 -*-
# -*- Channel CanalPelis -*-
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

__channel__ = "pelis24"

host = "https://www.pelis24.in/"

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


IDIOMAS = {'latino': 'LAT',
           'mexico': 'LAT',
             'spain': 'CAST',
             'castellano': 'CAST',
             'español': 'CAST',
             'sub español': 'VOSE]',
             'subtitulado': 'VOSE',
             'sup espaÑol': 'VOSE',
             'sub': 'VOSE',
             'ingles': 'VOS'}
list_language = list(IDIOMAS.values())
list_quality = ['HD 1080p', 'HDRip', 'TS-Screener']
list_servers = ['upstream', 'uqload', 'clipwatching', 'streamtape', 'aparat', 'steamz']


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = [item.clone(title="Novedades", action="lista", thumbnail=get_thumb('newest', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host + 'movies/', viewmode="movie_with_plot"),
                item.clone(title="Generos", action="genres", thumbnail=get_thumb('genres', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host, viewmode="movie_with_plot"),
                item.clone(title="Años", action="genres", thumbnail=get_thumb('year', auto=True),
                           text_blod=True, page=0, viewcontent='movies',
                           url=host, viewmode="movie_with_plot"),

                # item.clone(title="A-Z", action="alphabet", thumbnail=get_thumb('alphabet', auto=True),
                           # text_blod=True, page=0, viewcontent='movies',
                           # url=host, viewmode="movie_with_plot"),

                item.clone(title="Buscar...", action="search", thumbnail=get_thumb('search', auto=True),
                           text_blod=True, url=host, page=0)]

    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?s={0}".format(texto))

    try:
        return lista(item)

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def genres(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\s{2}|&nbsp;", "", data)
    if 'Generos' in item.title:
        bloq = scrapertools.find_single_match(data, '<section id="categories-3"(.*?)</section>')
    else:
        bloq = scrapertools.find_single_match(data, '<section id="torofilm_movies_annee-2"(.*?)</section>')
    patron = '<li.*?href="([^"]+)">([^<]+)</a>'  # url, title
    matches = re.compile(patron, re.DOTALL).findall(bloq)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(channel=item.channel, action="lista", title=scrapedtitle, page=0,
                                   url=scrapedurl, text_color=color3, viewmode="movie_with_plot"))
    if not 'Generos' in item.title:
        itemlist.reverse()
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|\s{2}", "", data)
    bloq = scrapertools.find_single_match(data, '<section class="section movies">(.*?)</section>')
    patron = '<article.*?'
    patron += '"entry-title">([^<]+)<.*?'
    patron += 'src="([^"]+)".*?'
    patron += '"post-ql">(.*?)</div>.*?'
    patron += 'href="([^"]+)"'
    matches = scrapertools.find_multiple_matches(bloq, patron)
    for scrapedtitle,scrapedthumbnail, prop, scrapedurl  in matches:
        language = []
        quality = ''
        lang = ''
        year = scrapertools.find_single_match(scrapedtitle, '\((\d{4})\)')
        if not year:
            year = '-'
        if 'class="lang"' in prop:
            lang = scrapertools.find_multiple_matches(lang, 'src=".*?/([A-z]+).png"')
            for elem in lang:
                lang = elem.lower().strip()
                language.append(IDIOMAS.get(lang, lang))
        if "Qlty" in prop:
            quality = scrapertools.find_single_match(prop, '"Qlty">([^<]+)<')
        
        scrapedtitle = re.sub(r'\d{4}$', '', scrapedtitle).strip()
        title = '%s [COLOR yellowgreen](%s)[/COLOR]' % (scrapedtitle, quality)
        itemlist.append(Item(channel=__channel__, action="findvideos", language=language, 
                             url=scrapedurl, infoLabels={'year': year}, quality=quality,
                             contentTitle=scrapedtitle, thumbnail=scrapedthumbnail,
                             title=title, context="buscar_trailer"))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)">SIGUIENTE')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="peliculas", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|amp;|#038;|\(.*?\)|\s{2}|&nbsp;", "", data)
    data = data.replace("'",'"')
    data = scrapertools.find_single_match(data, 'class="section player(.*?)</section')
    video_urls = scrapertools.find_multiple_matches(data, '<iframe (?:src|data-src)="([^"]+)"')
    idioma = scrapertools.find_multiple_matches(data, '<span class="server">.*?-([^<]+)<')
    for url, lang in zip(video_urls, idioma):
        lang = lang.lower().strip()
        lang = IDIOMAS.get(lang, lang)
        if 'streamcrypt' in url:
            hoster, id = scrapertools.find_single_match(url, "embed/(\w+.\w+)/([^$]+)")
            url = "https://sc.streamcrypt.net/hoster.%s.embed.php?p=2&id=%s" % (hoster, id)
            #url = url.replace('https://streamcrypt', 'https://www.streamcrypt')
            temp_data = httptools.downloadpage(url, headers={"referer": host}, follow_redirects=False, only_headers=True)
            if 'location' in temp_data.headers:
                url = temp_data.headers['location']
            else:
                continue

        itemlist.append(item.clone(action="play", title= "%s", language=lang, contentTitle = item.title, url=url))


    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    itemlist.sort(key=lambda it: it.language, reverse=False)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(Item(channel=__channel__, url=item.url, action="add_pelicula_to_library", extra="findvideos",
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             contentTitle=item.contentTitle))

    return itemlist
