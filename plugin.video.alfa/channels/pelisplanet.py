# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re

from platformcode import config, logger
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb

host = "http://www.pelisplanet.to/"

__channel__ = "pelisplanet"
parameters = channeltools.get_channel_parameters('pelisplanet')
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
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


def mainlist(item):
    logger.info()
    itemlist = []
    item.url = host
    item.text_color = color1
    item.fanart = fanart_host
    thumbnail = "https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/%s.png"

    itemlist.append(item.clone(title="Novedades", action="peliculas", text_blod=True,
                               viewcontent='movies', thumbnail=thumbnail % 'novedades',
                               viewmode="movie_with_plot"))

    itemlist.append(item.clone(title="Estrenos", action="peliculas", text_blod=True,
                               url=host + 'genero/estrenos/', thumbnail=thumbnail % 'estrenos'))

    itemlist.append(item.clone(title="Géneros", action="generos", text_blod=True,
                               viewcontent='movies', thumbnail=thumbnail % 'generos',
                               viewmode="movie_with_plot", url=host + 'generos/'))

    itemlist.append(Item(channel=item.channel, title="[COLOR yellow][Filtrar por Idiomas][/COLOR]",
                         fanart=fanart_host, folder=False, text_color=color3,
                         text_blod=True, thumbnail=thumbnail % 'idiomas'))

    itemlist.append(item.clone(title="    Castellano", action="peliculas", text_blod=True,
                               viewcontent='movies', thumbnail=thumbnail % 'castellano',
                               viewmode="movie_with_plot", url=host + 'idioma/castellano/'))

    itemlist.append(item.clone(title="    Latino", action="peliculas", text_blod=True,
                               viewcontent='movies', thumbnail=thumbnail % 'latino',
                               viewmode="movie_with_plot", url=host + 'idioma/latino/'))

    itemlist.append(item.clone(title="Buscar por Título o Actor", action="search", text_blod=True,
                               thumbnail=thumbnail % 'busqueda', url=host))
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    # logger.info(data)
    patron = '<div class="img">.*?<a href="([^"]+)" title="([^"]+)".*?'
    patron += r'<img.+?src="([^"]+)".*?\(([^\)]+)\)"> </a></div>.*?'
    patron += r'Ver\s(.*?)\sOnline'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for url, name, img, year, scrapedinfo in matches:
        contentTitle = re.sub(r' / .*| \(.*', '', scrapedinfo)
        plot = item.plot
        itemlist.append(item.clone(title=name, url=url, contentTitle=contentTitle.strip(),
                                   plot=plot, action="findvideos", infoLabels={"year": year},
                                   thumbnail=img, text_color=color3))

    paginacion = scrapertools.find_single_match(
        data, r'<a class="page larger" href="([^"]+)">\d+</a>')

    if paginacion:
        itemlist.append(Item(channel=item.channel, action="sub_search",
                             title="» Siguiente »", url=paginacion,
                             thumbnail='https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/next.png'))

    tmdb.set_infoLabels(itemlist)

    '''for item in itemlist:
        if item.infoLabels['plot'] == '':
            data = httptools.downloadpage(item.url).data
            item.fanart = scrapertools.find_single_match(
                data, 'meta property="og:image" content="([^"]+)" \/>')
            item.plot = scrapertools.find_single_match(data,
                                                       'Castellano</h3>\s*<p>(.+?)<strong>')
            item.plot = scrapertools.htmlclean(item.plot)'''

    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + "genero/animacion-e-infantil/"
        elif categoria == 'terror':
            item.url = host + "genero/terror/"
        elif categoria == 'castellano':
            item.url = host + "idioma/castellano/"

        elif categoria == 'latino':
            item.url = host + "idioma/latino/"
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


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)
    patron_todas = '<div class="home-movies">(.*?)<footer>'
    data = scrapertools.find_single_match(data, patron_todas)
    patron = 'col-sm-5".*?href="([^"]+)".+?'
    patron += 'browse-movie-link-qd.*?>([^<]+)</.+?'
    patron += '<p>([^<]+)</p>.+?'
    patron += 'title one-line">([^<]+)</h2>.+?'
    patron += 'img-responsive" src="([^"]+)".*?'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, quality, year, scrapedtitle, scrapedthumbnail in matches:


        itemlist.append(Item(channel=item.channel,
                             action="findvideos",
                             title=scrapedtitle,
                             url=scrapedurl,
                             quality=quality,
                             thumbnail=scrapedthumbnail,
                             contentTitle=scrapedtitle,
                             infoLabels={"year": year},
                             text_color=color3
                             ))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    paginacion = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)">')
    if paginacion:
        itemlist.append(Item(channel=item.channel, action="peliculas",
                             title="» Siguiente »", url=paginacion, plot="Página Siguiente",
                             thumbnail='https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/next.png'))

    '''for item in itemlist:
        if item.infoLabels['plot'] == '':
            data = httptools.downloadpage(item.url).data
            item.fanart = scrapertools.find_single_match(data, 'meta property="og:image" content="([^"]+)" \/>')
            item.plot = scrapertools.find_single_match(data, 'Castellano</h3>\s*<p>(.+?)<strong>')
            item.plot = scrapertools.htmlclean(item.plot)'''

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = '<div class="todos">.*?'
    patron += 'title="([^"]+)".*?'
    patron += 'href="([^"]+)".*?'
    patron += 'src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedtitle, scrapedurl, scrapedthumbnail in matches:
        itemlist.append(Item(channel=item.channel, action="peliculas", title=scrapedtitle,
                             url=scrapedurl, text_color=color3, thumbnail=scrapedthumbnail,
                             plot="", viewmode="movie_with_plot", folder=True))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    from lib import players_parse
    
    data = httptools.downloadpage(item.url).data
    patron = '<a id="[^"]+" style="cursor:pointer; cursor: hand" rel="([^"]+)".*?'
    patron += '<span class="optxt"><span>(.*?)</span>.*?'
    patron += '<span class="q">([^<]+)</span>'

    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, lang, servidores in matches:
        servidores = servidores.lower().strip()
        scrapedurl = players_parse.player_parse(scrapedurl, servidores, host)
        url_list = []
        lang = lang.replace('Español ', '')
        #No funcionan:
        if 'ultrastream' in servidores or '/meganz' in scrapedurl:
            continue
        if 'streamvips' in servidores:
            data = httptools.downloadpage(scrapedurl, headers={'Referer': host}).data
            data = re.sub(r"\n|\r|\t|\(.*?\)|\s{2}|&nbsp;", "", data)
            new_data = scrapertools.find_single_match(data, 'sources: \[(.+?)</body>')
            if new_data:
                patronr = "'file': '([^']+)','type': '([^']+)','label': '([^']+)'"
                matchesr = re.compile(patronr, re.DOTALL).findall(new_data)
                for surl, _type, label in matchesr:
                    url_list.append([".%s (%s)" % (_type,label), surl])
            elif 'vips/' in scrapedurl:
                scrapedurl = scrapertools.find_single_match(data, '"file": "([^"]+)')


        title = "Ver en: [COLOR yellowgreen][{}][/COLOR] [COLOR yellow][{}][/COLOR]".format(
                    servidores.capitalize(),lang)

        itemlist.append(item.clone(action='play', title=title, url=scrapedurl, quality=item.quality,
                                  language=lang.replace('Español ', ''), password=url_list,
                                  text_color=color3, thumbnail=item.thumbnail))
    itemlist = servertools.get_servers_itemlist(itemlist)
    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel,
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                             url=item.url, action="add_pelicula_to_library",
                             thumbnail='https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/libreria.png',
                             extra="findvideos", contentTitle=item.contentTitle))

    return itemlist

def play(item):
    if item.url.endswith('.m3u8'):
        item.server = 'oprem'
    return [item]
