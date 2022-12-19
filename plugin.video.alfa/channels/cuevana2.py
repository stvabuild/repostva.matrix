# -*- coding: utf-8 -*-

from builtins import range
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib                                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                                               # Usamos el nativo de PY2 que es más rápido

import re
import base64

from channelselector import get_thumb
from core.item import Item
from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools, tmdb
from platformcode import config, logger
from channels import autoplay

list_quality = []
list_servers = ['rapidvideo', 'streamango', 'directo', 'yourupload', 'openload', 'dostream']

canonical = {
             'channel': 'cuevana2', 
             'host': config.get_setting("current_host", 'cuevana2', default=''), 
             'host_alt': ["https://www.cuevana2.info/"], 
             'host_black_list': ["https://www.cuevana2.biz/", "https://cuevana2.io/"], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
patron_domain = '(?:http.*\:)?\/\/(?:.*ww[^\.]*)?\.?(?:[^\.]+\.)?([\w|\-]+\.\w+)(?:\/|\?|$)'
domain = scrapertools.find_single_match(host, patron_domain)


### MENUS ###

def mainlist(item):
    logger.info()
    
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)
    
    # PELICULAS
    plot = "Películas en Versión Original Subtitulada en Español (VOSE)"
    itemlist.append(Item(channel = item.channel, title = "--- Peliculas ---", plot=plot,
        folder=False, thumbnail = get_thumb("movies", auto = True)))

    itemlist.append(Item(channel = item.channel, title = "Novedades", action = "movies", plot=plot,
        url = host + "pelicula/", thumbnail = get_thumb("newest", auto = True)))
    
    itemlist.append(Item(channel = item.channel, title = "Destacadas", action = "movies", plot=plot,
        url = host + "peliculas-destacadas/", thumbnail = get_thumb("hot", auto = True) ))
    
    itemlist.append(Item(channel = item.channel, title = "Por Género", action = "genre", plot=plot,
        url = host + "pelicula/", thumbnail = get_thumb("genres", auto = True) ))
    
    itemlist.append(Item(channel = item.channel, title = "Por Año", action = "age", plot=plot,
        url = host + "pelicula/", thumbnail = get_thumb("year", auto = True)))
    
    itemlist.append(Item(channel = item.channel, title = "Buscar...", action = "search", plot=plot,
        url = host + "pelicula/?s=", thumbnail = get_thumb("search", auto = True)))

    # SERIES
    plot = "Series en Versión Original Subtitulada en Español (VOSE)"
    itemlist.append(Item(channel = item.channel, title = "--- Series ---", plot=plot,
        folder=False, thumbnail = get_thumb("tvshows", auto = True)))

    itemlist.append(Item(channel = item.channel, title = "Todas", action = "shows", plot=plot,
        url = host + "listar-series/", thumbnail = get_thumb("all", auto = True)))
    
    itemlist.append(Item(channel = item.channel, title = "Buscar...", action = "search", extra='1', 
        url = host + "listar-series/", thumbnail = get_thumb("search", auto = True), plot=plot))

    autoplay.show_option(item.channel, itemlist)

    return itemlist

### FIN MENUS ###


def inArray(arr, arr2):
    for word in arr:
        if word not in arr2:
            return False

    return True


def load_data(url):
    
    data = httptools.downloadpage(url, canonical=canonical).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)

    return data


def redirect_url(url, parameters=None, scr=False):

    try:
        url = url.replace("/irgo", "/go").replace('gotoolp', 'm3u8player')
        data = httptools.downloadpage(url, post=parameters, timeout=4)
    except:
        return

   
    if not data.data:
        return
    
    link = data.url
    data = data.data
    
    if scr:
        host = 'https://' + link.split("/")[2]
        vid = scrapertools.find_single_match(link, "\?id=(\w+)")
        if vid:
            link = host + 'hls/' + vid + '/' + vid + '.playlist.m3u8'
    elif 'm3u8' in link:
        link = scrapertools.find_single_match(data, '"file": "([^"]+)"')

    return link


def put_movies(item, data, pattern, paginacion):
    itemlist = []
    
    matches = scrapertools.find_multiple_matches(data, pattern)
    cnt = len(matches)
    
    if paginacion:
        matches = matches[item.page:item.page + paginacion]
    
    for link, img, title, rating, year, plot in matches:
        if 'pelicula' in link:
            itemTitle = "%s [COLOR darkgrey](%s)[/COLOR] [COLOR yellow](%s)[/COLOR]" % (title, year, rating)
            itemlist.append(Item(channel = item.channel, title=itemTitle, contentTitle=title, thumbnail=img, 
                url=link, plot=plot, action="findvideos", infoLabels={'year': year or '-'}, language="VOSE", contentType='movie'))
            #logger.info(link)

    return cnt, itemlist


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
    infoLabels = item.infoLabels

    data = load_data(item.url)
    bloq = scrapertools.find_single_match(data, 'Temporada %s</a>(.*?)</ul>' % item.contentSeason)
    pattern = '<li><a href="([^"]+)">.*?</i>(.*?)</a>'

    matches = scrapertools.find_multiple_matches(bloq, pattern)
    for link, title in matches:
        
        try:
            ses, ep = scrapertools.find_single_match(title.strip(), r"(\d{1,2})[x|X](\d{1,3})")
            ses = int(ses)
            ep = int(ep)
        except:
            ses = item.infoLabels['season']
            ep = 1
        infoLabels['episode'] = ep
        title = title.replace('%s.%s' % (ses, ep), '%sx%s' % (ses, ep))
        
        itemlist.append(item.clone(title=title, url=link, action='findvideos', extra=1, contentType='episode'))

    tmdb.set_infoLabels(itemlist, True)

    return itemlist


def seasons(item):
    logger.info()
    
    itemlist = []
    infoLabels = item.infoLabels

    data = load_data(item.url)

    seasonsPattern = '"collapse" href="#servico1.*?">(.*?)</a>'
    episodePattern = '%s</a>.*?<li><a href="([^"]+)">'

    matches = scrapertools.find_multiple_matches(data, seasonsPattern)
    for title in matches:
        
        #check primer episodio de cada season, necesario ya que mienten en las temporadas listadas
        episode_link = scrapertools.find_single_match(data, episodePattern % title)
        new_data = load_data(episode_link)
        
        if new_data and not '<div id="reproductor' in new_data:
            continue
        season = int(scrapertools.find_single_match(title, '(\d+)'))
        infoLabels['season'] = season

        itemlist.append(Item(channel=item.channel, title=title, contentSeason=season,
                             contentSerieName=item.contentSerieName, action="episodesxseasons",
                             infoLabels=infoLabels, url=item.url, contentType='season'))
        #episodeMatches = scrapertools.find_single_match(data, episodesPattern % season)
        #put_episodes(itemlist, item, episodeMatches)
    tmdb.set_infoLabels(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'episodios':
        itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]',
                     url=item.url, action="add_serie_to_library", extra="episodios",
                     contentSerieName=item.contentSerieName))
    
    return itemlist


def shows(item):
    logger.info()
    
    itemlist = []
    
    #Falsa paginacion
    paginacion = 32
    if not item.page:
        item.page = 0
    next_page2 = item.page + paginacion

    #descarga la pagina html
    data = load_data(item.url)
    
    pattern = '"in"><a href="([^"]+)">(.*?)</a>'

    matches = scrapertools.find_multiple_matches(data, pattern)
    cnt = len(matches)
    
    for link, title in matches[item.page:item.page + paginacion]:
        itemlist.append(Item(channel = item.channel, title=title, contentSerieName=title,
                             url=urllib.urljoin(host, link), action="seasons", contentType='tvshow'))

    if next_page2 < cnt:
        itemlist.append(Item(channel = item.channel, title='Siguiente >>', 
                        url=item.url, action="shows", page=next_page2))
    
    tmdb.set_infoLabels(itemlist, True)

    return itemlist


def movies(item):
    logger.info()
    
    itemlist = []
    
    #Falsa paginacion
    paginacion = 32
    if not item.page:
        item.page = 0
    next_page2 = item.page + paginacion

    #descarga la pagina html
    data = load_data(item.url)
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)">')
    if next_page:
        paginacion = False
    #patron para buscar las peliculas
    pattern = 'ml-item"><a href="([^"]+)".*?src="([^"]+)".*?' #link, img
    pattern += 'alt="([^"]+)".*?info jt-imdb">IMDb: (.*?)<.*?' #title, rating
    pattern += 'jt-info">(\d{4})</div>.*?' #year
    pattern += '<p class="f-desc">(.*?)</p>' # plot

    cnt, itemlist = put_movies(item, data, pattern, paginacion)

    tmdb.set_infoLabels(itemlist, True)

    if next_page:
        itemlist.append(Item(channel = item.channel, title='Siguiente >>', url=next_page, action="movies"))
    
    elif next_page2 < cnt:
        itemlist.append(Item(channel = item.channel, title='Siguiente >>', 
                        url=item.url, action="movies", page=next_page2))

    #coloca las peliculas encontradas en la lista
    return itemlist


def searchShows2(itemlist, item, texto):
    
    data = load_data(item.url)

    pattern = '"in"><a href="([^"]+)">(.*?)</a>'
    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, title in matches:

        if texto.lower() in title.lower():
            itemlist.append(Item(channel = item.channel, title=title, contentSerieName=title,
                                 url=urllib.urljoin(host, link), action="seasons", contentType='tvshow'))


def searchShows(itemlist, item, texto):
    
    texto = texto.lower().split()
    
    data = load_data(item.url)

    pattern = '"in"><a href="([^"]+)">(.*?)</a>'
    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, title in matches:
        keywords = title.lower().split()

        if inArray(texto, keywords):
            itemlist.append(Item(channel = item.channel, title=title, contentSerieName=title,
                                url=urllib.urljoin(host, link), action="seasons", contentType='tvshow'))


def searchMovies(itemlist, item, texto):
    
    data = load_data(item.url + texto)
    
    #patron para buscar las peliculas
    pattern = '<a href="([^"]+)"><div class="img">' #link
    pattern += '<img width="120" height="160" src="([^"]+)" class="attachment-thumbnail wp-post-image" alt="([^"]+)".*?' #img and title
    pattern += '<span style="width:([0-9]+)%">.*?'
    pattern += '"txt">(.*?)</div>' # text

    #ahora ya no se necesita el do while
    put_movies(itemlist, item, data, pattern)
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)">')

    if next_page:
        itemlist.append(Item(channel = item.channel, title='Siguiente Pagina', url=next_page, action="movies"))


def search(item, texto):
    itemlist = []

    if item.extra:
        searchShows2(itemlist, item, texto)
    else:
        #searchMovies(itemlist, item, texto)
        texto = texto.replace(" ", "+")
        item.url = item.url + texto
        if texto != '':
            return movies(item)

    tmdb.set_infoLabels(itemlist, True)
    
    return itemlist


def by(item, pattern):
    logger.info()
    
    itemlist = []

    #descarga la pagina html
    data = load_data(item.url)

    #patron para buscar en la pagina
    pattern = '<li class="cat-item cat-item-\d+"><a href="([^"]+)">&&</a>'.replace('&&', pattern)

    matches = scrapertools.find_multiple_matches(data, pattern)
    for link, genre in matches:
        
        itemlist.append(Item(channel = item.channel, title=genre, url=link, action="movies"))
    
    itemlist.reverse()
    
    return itemlist


def genre(item):
    return by(item, '(\w+)')


def age(item):
    #return by(item, '(\d+)')
    logger.info()
    
    itemlist = []

    #No hay lista de años, creamos una
    try:
        import datetime
        now = datetime.datetime.now()
        c_year = now.year + 1
    except:
        c_year = 2020

    year_list = list(range(1980, c_year))

    for year in year_list:
        year = str(year)
        url = '%sfecha-de-estreno/%s/' % (host, year)
        plot = 'Películas del año %s' % year
        
        itemlist.append(Item(channel=item.channel, title=year, url=url, action="movies", plot=plot))

    itemlist.reverse()
    
    return itemlist


def GKPluginLink(hash):
    
    hashdata = urllib.urlencode({r'link':hash})
    url = 'https://player.%s/plugins/gkpluginsphp.php' % domain
    try:
        json = httptools.downloadpage(url, post=hashdata).json
        return json['link']
    except:
        return None


def RedirectLink(hash_):
    
    hashdata = urllib.urlencode({r'h':hash_})
    url = 'https://player.%s/sc/r.php' % domain
    
    return redirect_url(url, hashdata)


def OpenloadLink(hash):
    
    hashdata = urllib.urlencode({r'h':hash})
    url = 'https://api.%s/openload/api.php' % domain
    try:
        json = httptools.downloadpage(url, post=hashdata, timeout=4).json
        return json['url'].replace('\\', '') if json['status'] == 1 else None
    except:
        return None


#el pattern esta raro para eliminar los duplicados, de todas formas asi es un lenguaje de programacion verificando su sintaxis
def getContentMovie(data, item):
    
    item.infoLabels["year"] = scrapertools.find_single_match(data, 'rel="tag">(\d+)</a>')
    
    genre = ''
    for found_genre in scrapertools.find_multiple_matches(data, 'genero/.*?">(.*?)</a>(?=.*?</p>)'):
        genre += found_genre + ', '
    item.infoLabels["genre"] = genre.strip(', ')

    director = ''
    for found_director in scrapertools.find_multiple_matches(data, 'director/.*?">(.*?)</a>(?=.*?</p>)'):
        director += found_director + ', '
    item.infoLabels["director"] = director.strip(', ')

    item.infoLabels["cast"] = tuple(found_cast for found_cast in scrapertools.find_multiple_matches(
        data, 'reparto/.*?">(.*?)</a>(?=.*?</p>)'))


def getContentShow(data, item):
    
    item.thumbnail = scrapertools.find_single_match(data, 'width="120" height="160" src="([^"]+)"')
    item.infoLabels['genre'] = scrapertools.find_single_match(data, '-4px;">(.*?)</div>')


def findvideos(item):
    logger.info()
    
    itemlist = []

    data = load_data(item.url)

    #TODO revisar patrones de esta parte
    '''if item.extra:
        getContentShow(data, item)
    else:
        getContentMovie(data, item)'''
    
    pattern = '<div id="reproductor(\d+)".*?src="([^"]+)"'
    subtitles = ""

    title = "[COLOR yellowgreen]Servidor [%s][/COLOR]"
    server = ""
    #itemlist.append(Item(channel = item.channel, title=item.url))
    for rep, link in scrapertools.find_multiple_matches(data, pattern):

        if not subtitles:
            subtitles = scrapertools.find_single_match(link, '&sub=(.*)')

        if 'player' in link:
            # Por si acaso están los dos metodos, de todas maneras esto es corto circuito
            if r'ir.php' in link:
                link = scrapertools.find_single_match(link, 'php\?url=(.*?)&').replace('%3A', ':').replace('%2F', '/')
                #logger.info("CUEVANA IR %s" % link)
                server = servertools.get_server_from_url(link)
            # otros links convencionales (fembed, rapidvideo, etc)
            elif r'irgoto.php' in link or 'sc/?h=' in link:
                if r'irgoto.php' in link:
                    link = scrapertools.find_single_match(link, 'php\?url=(.*?)&').replace('%3A', ':').replace('%2F', '/')
                else:
                    link = scrapertools.find_single_match(link, 'sc/\?h=(\w+)')

                if link.startswith('aHR0'):
                    try:
                        link = base64.b64decode(link.strip()+'==')
                    except:
                        link = RedirectLink(link)
                else:
                    link = RedirectLink(link)
                
                if link:
                    server = servertools.get_server_from_url(link)
                #logger.info("CUEVANA IRGOTO %s" % link)
            # vanlong (google drive)
            elif r'irgotogd.php' in link:
                link = redirect_url('https:'+link, scr=True)
                server = "directo"
            #openloadpremium no les va en la web, se hace un fix aqui
            elif r'irgotogp.php' in link:
                link = scrapertools.find_single_match(data, r'irgotogd.php\?url=(\w+)')
                #link = redirect_url('https:'+link, "", True)
                link = GKPluginLink(link)
                server = "directo"
            elif r'gdv.php' in link:
                # google drive hace lento la busqueda de links, ademas no es tan buena opcion y es el primero que eliminan
                continue
           
            elif r'irgotoolp.php' in link:
                link = redirect_url('https:'+link)
                server = 'oprem'
            
            elif '/?id=' in link:
                link = link.replace('/?id=', '/showcase.php?id=')
                data = httptools.downloadpage(link, post={'load': 'yes'}, timeout=4).data
                data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
                data = scrapertools.find_single_match(data, '<script>\s*let\s*player\s*=\s*\[([^\]]+\})\];')
                data = scrapertools.find_multiple_matches(data, '({[^\}]+\})')
                for elem in data:
                    json = jsontools.load(elem)
                    server = json.get('cyberlocker', '')
                    if server in ['streamsb']: continue
                    link = json.get('link', '')
                    language = json.get('language', '').replace('latin_spanish', 'LAT').replace('spanish', 'CAST').replace('english', 'VO')
                    itemlist.append(item.clone(action='play', title=title % json.get('cyberlocker', '').capitalize(), 
                                    url=link, server=server, subtitle=subtitles, language=language, quality=json.get('quality', '')))
            
            else:
                link = scrapertools.find_single_match(link, 'php.*?=(\w+)&')
                link = GKPluginLink(link)
                server = "directo"
            
        elif 'openload' in link:
            link = scrapertools.find_single_match(link, '\?h=(\w+)')
            #logger.info("CUEVANA OL HASH %s" % link)
            link = OpenloadLink(link) 
            #logger.info("CUEVANA OL %s" % link)
            server = "openload"

        elif 'youtube' in link:
            title = "[COLOR yellow]Ver Trailer (%s)[/COLOR]"
            server = "youtube"
        else: # En caso de que exista otra cosa no implementada, reportar si no aparece pelicula
            continue

        if not link or 'waaw' in link:
            continue

        if not itemlist:
            # GKplugin puede devolver multiples links con diferentes calidades, si se pudiera colocar una lista de opciones
            # personalizadas para Directo, se agradece, por ahora solo devuelve el primero que encuentre
            if type(link) is list:
                link = link[0]['link']
            if r'chomikuj.pl' in link:
                # En algunas personas la opcion CH les da error 401
                link += "|Referer=https://player.%s/plugins/gkpluginsphp.php" % domain
            elif r'vidcache.net' in link:
                # Para que no salga error 500
                link += '|Referer=https://player.%s/yourupload.com.php' % domain

            itemlist.append(
                item.clone(
                    channel = item.channel, 
                    title=title % server.capitalize(), 
                    url=link, action='play', 
                    subtitle=subtitles,
                    server=server))

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) and not item.contentSerieName:
                itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                     action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                     contentTitle = item.contentTitle
                                     ))
    return itemlist
