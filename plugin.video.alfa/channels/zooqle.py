# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urlparse                                 # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                 # Usamos el nativo de PY2 que es más rápido

import re
import time
import random

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb
from lib import generictools
from channels import filtertools
from channels import autoplay


#IDIOMAS = {'CAST': 'Castellano', 'LAT': 'Latino', 'VO': 'Version Original'}
IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'Version Original': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['torrent']

channel = 'zooqle'
host = 'https://zooqle.com/'
host_alt = ['https://zooqle.unblockninja.com/', 'https://zooqle.torrentbay.to/']
"""
host_alt = ['https://zooqle.unblockit.club', 'https://zooqle.unblockninja.com', 'https://zooqle.nocensor.space']

host_alt = ['https://zooqle.com/', 'https://zooqle1.unblocked.is/', 'https://zooqle.unblocked.win/', 
            'https://zooqle.nocensor.xyz/',  'https://zooqle.unblockproject.xyz/',  
            'https://zooqle.123unblock.pro/',  'https://zooqle.p4y.space/',  
            'https://zooqle.p4y.info/',  'https://zooqle.p4y.xyz/', 'https://zooqle.prox4you.icu/',  
            'https://zooqle-com.prox2.info/', 'https://zooqle.prox4you.icu/']
"""
categoria = channel.capitalize()
__modo_grafico__ = config.get_setting('modo_grafico', channel)
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel)        #Actualización sólo últ. Temporada?
timeout = 20


def mainlist(item):
    logger.info()
    itemlist = []
    
    host = config.get_setting('domain_name', channel)
    
    thumb_cartelera = get_thumb("now_playing.png")
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_pelis_VO = get_thumb("channels_vos.png")
    
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_series_VOD = get_thumb("videolibrary_tvshow.png")
    
    thumb_populares = get_thumb("favorites.png")
    thumb_generos = get_thumb("genres.png")
    thumb_alfabeto = get_thumb("channels_movie_az.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")
    
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Películas", action="listado", 
                url=host + "mov/?pg=1&tg=0&v=t&age=any&s=dt&sd=d", thumbnail=thumb_pelis_VO, 
                extra="peliculas", extra2="/mov/"))
    itemlist.append(Item(channel=item.channel, title="    - Novedades", action="listado", 
                url=host, thumbnail=thumb_cartelera, 
                extra="peliculas", extra2="/mov/", extra3="novedades"))
    itemlist.append(Item(channel=item.channel, title="    - Populares", action="listado", 
                url=host, thumbnail=thumb_cartelera, 
                extra="peliculas", extra2="/mov/", extra3="populares"))
    itemlist.append(Item(channel=item.channel, title="    - Géneros", action="generos", 
                url=host + "mov/?age=wk&s=dt&sd=d&tg=0", thumbnail=thumb_generos, 
                extra="peliculas", extra2="/mov/", extra3="dt"))
    itemlist.append(Item(channel=item.channel, title="    - Más Valoradas", action="generos", 
                url=host + "mov/?age=wk&s=rt&sd=d&tg=0", thumbnail=thumb_populares, 
                extra="peliculas", extra2="/mov/", extra3="rt"))
    

    itemlist.append(Item(channel=item.channel, title="Series", action="listado", 
                url=host + "browse/tv/?pg=1&v=t&s=dt&sd=d", thumbnail=thumb_series_VOD, 
                extra="series", extra2="/browse/tv/"))
    itemlist.append(Item(channel=item.channel, title="    - Novedades", action="listado", 
                url=host, thumbnail=thumb_cartelera, 
                extra="series", extra2="/browse/tv/", extra3="novedades"))
    itemlist.append(Item(channel=item.channel, title="    - Populares", action="listado", 
                url=host, thumbnail=thumb_cartelera, 
                extra="series", extra2="/browse/tv/", extra3="populares"))
    itemlist.append(Item(channel=item.channel, title="    - Géneros", action="generos", 
                url=host + "browse/tv/?pg=1&v=t&s=dt&sd=d", thumbnail=thumb_generos, 
                extra="series", extra2="/browse/tv/", extra3="dt"))
    itemlist.append(Item(channel=item.channel, title="    - Más Valoradas", action="generos", 
                url=host + "browse/tv/?pg=1&v=t&s=rt&sd=d", thumbnail=thumb_populares, 
                extra="series", extra2="/browse/tv/", extra3="rt"))
    itemlist.append(Item(channel=item.channel, title="    - Alfabético", action="alfabeto", 
                url=host + "browse/tv/?pg=1&v=t&s=dt&sd=d&l=%s", thumbnail=thumb_alfabeto, 
                extra="series"))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                url=host + "?s=%s", thumbnail=thumb_buscar, extra="search"))

    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", 
                folder=False, thumbnail=thumb_separador))
    
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", 
                thumbnail=thumb_settings))
    
    autoplay.show_option(item.channel, itemlist)            #Activamos Autoplay

    return itemlist
    
    
def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return


def generos(item):
    logger.info()
    itemlist = []
    
    host = config.get_setting('domain_name', channel)
    extra3 = item.extra3
    del item.extra3

    data = ''
    try:
        response = httptools.downloadpage(item.url, timeout=timeout, ignore_response_code=True)
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data)
        if not PY3:
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    except:
        pass
    if not response.sucess:
        host, data = retry_alt(item.url, timeout)                               # Si hay un error se pasa a la web alternativa
        
    patron = '<ul class="[^"]+" id="catMenu">'
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not data or not scrapertools.find_single_match(data, patron):
        #Comprobamos si la IP ha sido bloqueada, y si es así, lo intentamos con otra url
        status, itemlist, host, data = check_blocked_IP(data, itemlist, item.url, timeout)  
        if status:
            return itemlist                                                     #IP bloqueada
        
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + 
                        clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + 
                        '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " 
                        + item.url + data)
    
    if not data:    #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL. ' + 
                        'Si la Web está activa, reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    patron = '<li role="presentation">\s*<a role="menuitem" class="small" tabindex="-1" '
    patron += 'href="([^"]+)">(?:<i class="[^"]+"><\/i>)?(.*?)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + 
                        " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  '
                        + 'Reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug(patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    item.url = item.url.replace('age=wk', 'age=any')
    itemlist.append(item.clone(action="listado", title="TODOS"))
    
    for scrapedurl, scrapedtitle in matches:
        if item.extra2 not in scrapedurl:
            continue
        
        url = urlparse.urljoin(host, scrapedurl + "?pg=1&tg=0&v=t&age=any&s=%s&sd=d" % extra3)

        itemlist.append(item.clone(action="listado", title=scrapedtitle, url=url))

    return itemlist
    
    
def alfabeto(item):
    logger.info()
    itemlist = []

    for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
                        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 
                        'Z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '#']:
        itemlist.append(item.clone(action="listado", title=letra, url=item.url % letra))

    return itemlist

    
def listado(item):
    logger.info()
    itemlist = []
    item.category = categoria
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")
    
    host = config.get_setting('domain_name', channel)

    #logger.debug(item)
    
    curr_page = 1                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial
    if item.curr_page:
        curr_page = int(item.curr_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                      # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                      # ... y lo borramos
    
    cnt_tot = 20                                                                # Poner el num. máximo de items por página
    cnt_title = 0                                                               # Contador de líneas insertadas en Itemlist
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 3                                                            # Después de este tiempo pintamos (segundos)
    timeout_search = timeout * 2                                                # Timeout para descargas

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                            # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                                    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista.extend(item.title_lista)                                    # Se usa la lista de páginas anteriores en Item
        del item.title_lista                                                    # ... limpiamos
        
    if not item.extra2:                                                         # Si viene de Catálogo o de Alfabeto
        item.extra2 = ''
    
    next_page_url = item.url
    #Máximo num. de líneas permitidas por TMDB. Máx de 3 segundos por Itemlist para no degradar el rendimiento
    while cnt_title <= cnt_tot * 0.50 and curr_page <= last_page and fin > time.time():
    
        # Descarga la página
        data = ''
        try:
            response = httptools.downloadpage(next_page_url, timeout=timeout_search, ignore_response_code=True)
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data)
            if not PY3:
                data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        except:
            pass
        if not response.sucess:
            host, data = retry_alt(next_page_url, timeout_search)               # Si hay un error se pasa a la web alternativa
        
        curr_page += 1                                                          #Apunto ya a la página siguiente
        if not data:                                                            #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " 
                        + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. ' 
                        + 'Si la Web está activa, reportar el error con el log'))
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos
            
        #Comprobamos si la IP ha sido bloqueada, y si es así, lo intentamos con otra url
        status, itemlist, host, data = check_blocked_IP(data, itemlist, next_page_url, timeout_search)
        if status:
            return itemlist                                                     #IP bloqueada

        #Patrón para búsquedas, pelis y series
        if item.extra == 'search':                                              # Búsquedas...
            patron = '<li title="[^"]+"><a class="sug" href="([^"]+)"><img [^>]+'
            patron += 'src="([^"]+)"><div>([^<]+)<\/div><div class="sugInfo">(\d+)'
            patron += '\s*<i class="[^"]+">\s*<\/i>[^<]+<\/div>()<\/a><\/li>'    
        elif item.extra == 'peliculas' and (item.extra3 == 'novedades' or item.extra3 == 'populares'):  # Películas Home
            patron = '<div class="cell text-muted3\s*">\s*<a href="[^"]+"\s*>'
            patron += '<img [^>]+src="([^"]+)"\s*>\s*<\/a>(?:<span class="newStrip">'
            patron += 'NEW<\/span>)?\s*<div class="txt text-trunc">\s*<a class='
            patron += '"txt-title" href="([^"]+)">(.*?)<\/a>()<br\s*\/>.*?'
            patron += '<span class="badge[^>]+>(.*?)<\/span><\/span><\/div><\/div>'
            mat_len = 18
        elif item.extra == 'peliculas':                                         # Película menú
            patron = '<td class="smaller text-muted3">.*?(?:<img.*?src="([^"]+)")?>'
            patron += '<\/a><\/td><td><a href="([^"]+)">(.*?)\s*\(([1|2][9|0]\d{2})?\)'
            patron += '<\/a>.*?<span class="[^"]+">([^<]+)<\/span><\/td>'
        elif item.extra == 'series' and (item.extra3 == 'novedades' or item.extra3 == 'populares'):     # Series Home
            patron = '<div class="cell text-muted3\s*">\s*<div class="imgdiv">\s*'
            patron += '<a href="[^"]+"\s*><img [^>]+src="([^"]+)"\s*>\s*<\/a>'
            patron += '(?:<span class="newStrip">NEW<\/span>)?<\/div>\s*<div class='
            patron += '"txt text-trunc">\s*<a class="txt-title" href="([^"]+)">'
            patron += '(.*?)<\/a>()()<br\s*\/>'
            mat_len = 12
        else:                                                                   # Serie menú
            patron = '<td\s*(?:width="[^"]+")?\s*class="[^"]+">.*?(?:<img.*?src='
            patron += '"([^"]+)")?><\/a><\/td>.*?<div class="mov_head">\s*<a href="'
            patron += '([^"]+)">(.*?)<\/a>\s*<span class="[^"]+">\((\d+)\)<\/span>()'
            
        #logger.debug("PATRON: " + patron)
        #logger.debug(data)
        
        matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches and item.extra != 'search':                              #error
            item = generictools.web_intervenida(item, data)                     #Verificamos que no haya sido clausurada
            if item.intervencion:                                               #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
                return itemlist                                                 #Salimos
            
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " 
                        + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  ' 
                        + 'Reportar el error con el log'))
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos
        if not matches and item.extra == 'search':                              #búsqueda vacía
            return itemlist                                                     #Salimos

        # Ajustamos el número de items a visualizar en función de la opción de Populares o Novedades
        if item.extra3 == 'populares':
            matches = matches[:mat_len]
        elif item.extra3 == 'novedades':
            matches = matches[mat_len:]
        
        #logger.debug(matches)
        
        #Buscamos la próxima y la última página
        if item.extra == 'search' or item.extra3 == 'novedades' or item.extra3 == 'populares': # Si es Search, no hay paginado
            patron_last = ''
            patron_next = ''
        else:
            patron_last = '<ul class="pagination[^"]+".*?<span class="small">(.*?)'
            patron_last += '\s*\w+<\/span><\/a><\/li><\/ul>'
            patron_next = '<ul class="pagination[^"]+".*?<\/a><\/li><li class='
            patron_next += '"active"><a href="[^"]+">(\d+)<\/a><\/li>'

        try:
            next_page = int(scrapertools.find_single_match(data, patron_next)) + 1
            next_page_url = re.sub(r'pg=(\d+)', 'pg=%s' % str(next_page), item.url)
        except:                                                                         #Si no lo encuentra, lo ponemos a 1
            #logger.error('ERROR 03: LISTADO: Al obtener la paginación: ' + patron_next 
            #            + ' / ' + patron_last + ' / ' + scrapertools.find_single_match(data, 
            #            patron_last))
            next_page = 1
            next_page_url = re.sub(r'pg=(\d+)', 'pg=%s' % str(next_page), item.url)
        #logger.debug('curr_page: ' + str(curr_page) + ' / next_page: ' + str(next_page) + ' / last_page: ' + str(last_page))
        
        if last_page == 99999:                                                          #Si es el valor inicial, buscamos
            try:
                last_page = scrapertools.find_single_match(data, patron_last)\
                        .replace(',', '').replace('.', '')
                last_page = int((float(last_page) / 20) + 0.99)
            except:                                                                     #Si no lo encuentra, lo ponemos a 1
                #logger.error('ERROR 03: LISTADO: Al obtener la paginación: ' + patron_next + ' / ' + patron_last + ' / ' + scrapertools.find_single_match(data, "<ul class=\"pagination\">.*?<\/span><\/a><\/li><\/ul><\/nav><\/div><\/div><\/div>"))
                last_page = next_page
            #logger.debug('curr_page: ' + str(curr_page) + ' / next_page: ' + str(next_page) + ' / last_page: ' + str(last_page))
        
        #Empezamos el procesado de matches
        for scrapedthumbnail, scrapedurl, scrapedtitle, scrapedyear, scrapedquality in matches:
            if item.extra == 'search':
                url = scrapedthumbnail
                thumb = scrapedurl
                if url.startswith('/tv/'):
                    item.extra2 = 'series'                          # Serie búsqueda
                else:
                    item.extra2 = 'peliculas'                       # Película búsqueda
            else:
                url = scrapedurl
                thumb = scrapedthumbnail
            
            title_subs = []                                         #creamos una lista para guardar info importante
            # Si viene de Novedades o Populares, pasamos de Episodio a Serie
            if item.extra == 'series' and (item.extra3 == 'novedades' or item.extra3 == 'populares'):
                title_subs += [scrapertools.find_single_match(url, '\/(\d+[x|X]\d+)\.htm.')]
                url = re.sub(r'(\/\d+[x|X]\d+)\.htm.', '.html', url)
            
            title = scrapedtitle
            # Slugify, pero más light
            title = title.replace("á", "a").replace("é", "e").replace("í", "i")\
                    .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                    .replace("ï¿½", "ñ").replace("Ã±", "ñ")
            title = scrapertools.decode_utf8_error(title)

            if url in title_lista:                                   #Si ya hemos procesado el título, lo ignoramos
                continue
            else:
                title_lista += [url]                                 #la añadimos a la lista de títulos
            
            #cnt_title += 1
            item_local = item.clone()                                       #Creamos copia de Item para trabajar
            if item_local.tipo:                                             #... y limpiamos
                del item_local.tipo
            if item_local.totalItems:
                del item_local.totalItems
            if item_local.intervencion:
                del item_local.intervencion
            if item_local.viewmode:
                del item_local.viewmode
            if item_local.extra == 'search':
                item_local.extra = item_local.extra2
            item_local.extra2 = True
            del item_local.extra2
            item_local.extra3 = True
            del item_local.extra3
            item_local.text_bold = True
            del item_local.text_bold
            item_local.text_color = True
            del item_local.text_color
                
            item_local.language = ['VO']                                            #creamos lista para los idiomas
            item_local.quality = scrapedquality                                     #iniciamos calidad
            if item_local.quality == 'ultra':
                item_local.quality = '4K'
            if thumb:
                item_local.thumbnail = urlparse.urljoin(host, thumb)                #iniciamos thumbnail
            elif item_local.extra == 'peliculas':
                item_local.thumbnail = thumb_pelis                                  #iniciamos thumbnail
            else:
                item_local.thumbnail = thumb_series                                 #iniciamos thumbnail

            item_local.url = urlparse.urljoin(host, url)                            #guardamos la url final
            item_local.context = "['buscar_trailer']"

            #Analizamos los formatos de la películas
            if item_local.extra == 'peliculas':
                item_local.contentType = "movie"                                    #por defecto, son películas
                item_local.action = "findvideos"

            #Analizamos los formatos de series, temporadas y episodios
            elif item_local.extra == 'series':
                item_local.contentType = "tvshow"
                item_local.action = "episodios"
                item_local.season_colapse = True                            #Muestra las series agrupadas por temporadas

            #Limpiamos el título de la basura innecesaria
            title = re.sub(r'(?i)TV|Online', '', title).strip()
            item_local.quality = re.sub(r'(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', 
                        '', item_local.quality).strip()

            #Analizamos el año.  Si no está claro ponemos '-'
            try:
                year = int(scrapedyear)
                if year >= 1940 and year_int <= 2050:
                    item_local.infoLabels["year"] = year
                else:
                    year = '-'
                    item_local.infoLabels["year"] = '-'
            except:
                year = '-'
                item_local.infoLabels["year"] = '-'
            
            #Terminamos de limpiar el título
            title = re.sub(r'[\(|\[]\s+[\)|\]]', '', title)
            title = title.replace('()', '').replace('[]', '').strip().lower().title()
            item_local.from_title = title.strip().lower().title()           #Guardamos esta etiqueta para posible desambiguación de título

            #Salvamos el título según el tipo de contenido
            if item_local.contentType == "movie":
                item_local.contentTitle = title
            else:
                item_local.contentSerieName = title.strip().lower().title()

            item_local.title = title.strip().lower().title()
                
            #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
            item_local.title_subs = title_subs
                
            #Salvamos y borramos el número de temporadas porque TMDB a veces hace tonterias.  Lo pasamos como serie completa
            if item_local.contentSeason and (item_local.contentType == "season" \
                        or item_local.contentType == "tvshow"):
                item_local.contentSeason_save = item_local.contentSeason
                del item_local.infoLabels['season']

            #Ahora se filtra por idioma, si procede, y se pinta lo que vale
            """
            if config.get_setting('filter_languages', channel) > 0:     #Si hay idioma seleccionado, se filtra
                itemlist = filtertools.get_link(itemlist, item_local, list_language)
            else:
            """
            itemlist.append(item_local.clone())                         #Si no, pintar pantalla
            
            cnt_title = len(itemlist)                                   #Contador de líneas añadidas
            
            #logger.debug(item_local)

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__, idioma_busqueda='es,en')
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    # Si es necesario añadir paginacion
    if curr_page <= last_page:
        if last_page:
            title = '%s de %s' % (curr_page-1, last_page)
        else:
            title = '%s' % curr_page-1

        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente " 
                        + title, title_lista=title_lista, url=next_page_url, extra=item.extra, 
                        extra2=item.extra2, last_page=str(last_page), curr_page=str(curr_page)))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    matches = []
    item.category = categoria
    max_items_per_quality = config.get_setting('max_items_per_quality', channel)
    if max_items_per_quality == 0: max_items_per_quality = 999999
    max_items_one_quality = config.get_setting('max_items_one_quality', channel)
    if max_items_one_quality == 0: max_items_one_quality = 999999
    
    host = config.get_setting('domain_name', channel)
    
    item.url += '?pg=1&v=t&s=sz&sd=d'                                           # Vista ordenada por tamaños
    next_page_url = item.url
    
    #logger.debug(item)
    
    curr_page = 1                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial

    #Bajamos los datos de las páginas
    data = ''
    patron = '<tr>\s*<td\s*class="text-muted[^>]+>(\d+).<\/td>\s*<td\s*class='
    patron += '"text-nowrap[^>]+>\s*<a[^h]+href="([^"]+)">\s*([^<]+)<\/a>\s*'
    patron += '(?:<div[^<]+)?\s*(?:<span\s*class=[^>]+Audio\s*format">\s*<i\s*class='
    patron += '[^>]+zqf-mi-audio[^>]+>\s*<\/i>([^>]+)<\/span>(?:\s*&nbsp;)?\s*)?\s*'
    patron += '(?:<span\s*class="smaller[^"]+"\s*title="Detected\s*languages">([^<]+)<\/span>'
    patron += '(?:\s*&nbsp;)?\s*)?(?:<span\s*class="text-nowrap[^>]+>\s*<i\s*class='
    patron += '"zqf[^>]+>\s*<\/i>\s*([^<]+)<\/span>(?:\s*&nbsp;)?\s*<\/div>\s*)?\s*'
    patron += '<\/td>\s*<td\s*class="[^<]+<div\s*class="progress[^<]+<div\s*class='
    patron += '"progress-bar[^>]+>\s*([^<]+)<\/div>\s*<\/div>\s*<\/td>\s*(?:<td\s*'
    patron += 'class=[^>]+>[^<]+<\/td>\s*<td\s*class[^>]+>\s*<div\s*class="progress[^"]+"'
    patron += '\s*title="Seeders:\s*(.*?)\s*\|[^>]+>)?'
        
    while curr_page <= last_page:                                               # Leemos todas las páginas
        data = ''
        try:
            response = httptools.downloadpage(next_page_url, timeout=timeout, ignore_response_code=True)
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data)
            if not PY3:
                data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        except:
            pass
        if not response.sucess:
            host, data = retry_alt(next_page_url, timeout=timeout)              # Si hay un error se pasa a la web alternativa
            
        if not data:
            logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                            ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. ' 
                            + 'Si la Web está activa, reportar el error con el log', folder=False))
            return itemlist                             #si no hay más datos, algo no funciona, pintamos lo que tenemos

        #Comprobamos si la IP ha sido bloqueada, y si es así, lo intentamos con otra url
        status, itemlist, host, data = check_blocked_IP(data, itemlist, next_page_url, timeout)
        if status:
            return itemlist                                                     #IP bloqueada
        
        curr_page += 1
        next_page_url = re.sub(r'pg=(\d+)', 'pg=%s' % str(curr_page), item.url)
        #Buscamos la última página
        if last_page == 99999:                                                  #Si es el valor inicial, buscamos
            patron_last = '<ul class="pagination[^"]+".*?<span class="small">(.*?)'
            patron_last += '\s*\w+<\/span><\/a><\/li><\/ul>'
            try:
                last_page = scrapertools.find_single_match(data, patron_last)\
                        .replace(',', '').replace('.', '')
                last_page = int((float(last_page) / 30) + 0.99)
            except:                                                             #Si no lo encuentra, lo ponemos a 1
                last_page = 1
            #logger.debug('curr_page: ' + str(curr_page) + ' / last_page: ' + str(last_page))
        
        matches += re.compile(patron, re.DOTALL).findall(data)
    
    if not matches:                                                             #error
        if "Sorry, we haven't matched torrents for this" in data:               # No hay torrents
            return itemlist
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
        else:
            logger.error("ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web " 
                        + " / PATRON: " + patron + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web.  ' 
                        + 'Verificar en la Web esto último y reportar el error con el log', folder=False))
            return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)

    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)
    
    #Ahora colocamos los enlaces con audio en Español al principio de cada calidad
    x = 0
    matches_alt = []
    for scrapedord, scrapedurl, scrapedtitle, scrapedaudio, scrapedlanguage, \
                        scrapedquality, scrapedsize, scrapedseeds in matches:
        if not scrapedsize:
            continue
            
        seeds = scrapedseeds.replace(',', '')

        try:
            if 'es' in scrapedlanguage:
                matches_alt.append((float(scrapedord) / 1000, scrapedurl, scrapedtitle, \
                        scrapedaudio, scrapedlanguage, scrapedquality, scrapedsize, seeds))
            else:
                matches_alt.append((float(scrapedord), scrapedurl, scrapedtitle, \
                        scrapedaudio, scrapedlanguage, scrapedquality, scrapedsize, seeds))
        except:
            pass
        x += 1
    matches_alt = sorted(matches_alt, key=lambda link: (link[5], float(link[0])))
    
    #Ahora seleccionamos sólo el número de enlaces por calidad que está configurado
    quality_batch = ''
    for scrapedord, scrapedurl, scrapedtitle, scrapedaudio, scrapedlanguage, \
                        scrapedquality, scrapedsize, scrapedseeds in matches_alt:
        if not quality_batch:
            quality_batch = scrapedquality
        if quality_batch != scrapedquality:
            max_items = max_items_per_quality
            break
    else:
        max_items = max_items_one_quality
    
    x = 0
    matches = []
    quality_batch = ''
    for scrapedord, scrapedurl, scrapedtitle, scrapedaudio, scrapedlanguage, \
                        scrapedquality, scrapedsize, scrapedseeds in matches_alt:
        x += 1
        if not quality_batch:
            quality_batch = scrapedquality
        if quality_batch == scrapedquality and x > max_items:
            matches.append((float(-1), scrapedurl, scrapedtitle, scrapedaudio, \
                        scrapedlanguage, scrapedquality, scrapedsize, scrapedseeds))
        elif quality_batch != scrapedquality:
            quality_batch = scrapedquality
            x = 1
            matches.append((scrapedord, scrapedurl, scrapedtitle, scrapedaudio, \
                        scrapedlanguage, scrapedquality, scrapedsize, scrapedseeds))
        else:
            matches.append((scrapedord, scrapedurl, scrapedtitle, scrapedaudio, \
                        scrapedlanguage, scrapedquality, scrapedsize, scrapedseeds))
    matches = sorted(matches, key=lambda link: float(link[0]))

    #Ahora tratamos los enlaces .torrent con las diferentes calidades, verificando el límite de enlaces
    for scrapedord, scrapedurl, scrapedtitle, scrapedaudio, scrapedlanguage, \
                        scrapedquality, scrapedsize, scrapedseeds in matches:
        if scrapedord < 0:
            continue
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()
        title = scrapedtitle

        #Añadimos los idiomas
        item_local.language = []
        if 'es' in scrapedlanguage:
            item_local.language += ['CAST']
        else:
            item_local.language += ['VO']
        
        #Analizamos los formatos de la películas y series
        if item_local.contentType == 'movie':
            patron_title = '(?:\(?[1|2][9|0]\d{2}\)?)\s*(?:\[|\:\s*)?(.*?)(?:-\w+(?:\s*\[.*?\])?)?$'
        else:
            patron_title = '.*?[S|s]\d+[E|e]\d+.*?(?:\[|\:\s*)?(%s.*?)(?:-\w+(?:\s*\[.*?\])?)?$' % scrapedquality
            if not scrapertools.find_single_match(title, patron_title):
                patron_title = '.*?\d+[x|X]\d+.*?(?:\[|\:\s*)?(%s.*?)(?:-\w+(?:\s*\[.*?\])?)?$' % scrapedquality
                if not scrapertools.find_single_match(title, patron_title):
                    patron_title = '.*?[S|s]\d+[E|e]\d+\s*(?:\[|\:\s*)?(.*?)(?:-\w+(?:\s*\[.*?\])?)?$'
                    if not scrapertools.find_single_match(title, patron_title):
                        patron_title = '.*?(?:\(?[1|2][9|0]\d{2}\)(?:\s*\d{2}\s*\d{2})?)\s*'
                        patron_title += '(?:\[|\:\s*)?(.*?)(?:-.*?)?$'
                        if not scrapertools.find_single_match(title, patron_title):
                            patron_title = '.*?\d+[x|X]\d+\s*(?:\[|\:\s*)?(.*?)(?:-\w+(?:\s*\[.*?\])?)?$'
        
        item_local.quality = scrapertools.find_single_match(title, patron_title)
        if not item_local.quality:
            item_local.quality = scrapedquality
        if scrapedquality not in item_local.quality:
            item_local.quality = '%s %s' % (scrapedquality, item_local.quality)
        item_local.quality = re.sub(r'\[.*?\]', '', item_local.quality)
        item_local.quality = re.sub(r'\d+(?:.\d+)?\s*[G|M]B', '', item_local.quality)
        item_local.quality += ' %s' % scrapedaudio
        item_local.quality = re.sub(
        r'(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu|movie|tvshows', 
                        '', item_local.quality).strip()
        
        #Buscamos si ya tiene tamaño, si no, los buscamos en el archivo .torrent
        item_local.torrent_info = ''
        size = scrapedsize
        if size:
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
            item_local.torrent_info = '%s, ' % size                             #Agregamos size

        #Añadimos los seeds en calidad, como información adicional
        if scrapedseeds:
            item_local.torrent_info += 'Seeds: %s' % scrapedseeds               #Agregamos seeds
        item_local.torrent_info = item_local.torrent_info.strip().strip(',')
        if not item.unify:
            item_local.torrent_info = '[%s]' % item_local.torrent_info

        #Ahora pintamos el link del Torrent
        item_local.url = urlparse.urljoin(host, scrapedurl)
        item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (item_local.quality, str(item_local.language), \
                        item_local.torrent_info)
        
        #Preparamos título y calidad, quitamos etiquetas vacías
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
        item_local.title = item_local.title.replace("--", "").replace("[]", "")\
                        .replace("()", "").replace("(/)", "").replace("[/]", "")\
                        .replace("|", "").strip()
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.quality)
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.quality)
        item_local.quality = item_local.quality.replace("--", "").replace("[]", "")\
                        .replace("()", "").replace("(/)", "").replace("[/]", "")\
                        .replace("|", "").strip()
        
        item_local.alive = "??"                                                 #Calidad del link sin verificar
        item_local.action = "play"                                              #Visualizar vídeo
        item_local.server = "torrent"                                           #Seridor Torrent
        
        itemlist_t.append(item_local.clone())                                   #Pintar pantalla, si no se filtran idiomas
        
        # Requerido para FilterTools
        if config.get_setting('filter_languages', channel) > 0:                 #Si hay idioma seleccionado, se filtra
            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío

        #logger.debug("TORRENT: " + scrapedurl + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
        #logger.debug(item_local)

    if len(itemlist_f) > 0:                                                     #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                             #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, 
                        title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", 
                        thumbnail=thumb_separador, folder=False))
        itemlist.extend(itemlist_t)                                             #Pintar pantalla con todo si no hay filtrado
    
    #itemlist = sorted(itemlist, key=lambda it: float(it.ord))
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                              #Lanzamos Autoplay
    
    return itemlist
    
    
def play(item):                                 #Permite preparar la descarga de los .torrents y subtítulos externos
    logger.info()
    itemlist = []
    headers = []
    
    host = config.get_setting('domain_name', channel)

    #buscamos la url del .torrent
    patron = '<a rel="nofollow" href="(magnet:[^"]+)"'
    data = ''
    try:
        response = httptools.downloadpage(item.url, timeout=timeout, ignore_response_code=True)
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data)
        if not PY3:
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    except:
        pass
    if not response.sucess:
        host, data = retry_alt(item.url, timeout)                       # Si hay un error se pasa a la web alternativa
        
    #Comprobamos si la IP ha sido bloqueada, y si es así, lo intentamos con otra url
    status, itemlist, host, data = check_blocked_IP(data, itemlist, item.url, timeout=timeout)
    if status:
        return itemlist                                                 #IP bloqueada
    if not scrapertools.find_single_match(data, patron):
        logger.error('ERROR 02: PLAY: No hay enlaces o ha cambiado la estructura de la Web.  ' 
                        + 'Verificar en la Web esto último y reportar el error con el log: PATRON: ' 
                        + patron + ' / DATA: ' + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 02: PLAY: No hay enlaces o ha cambiado la estructura de la Web.  ' 
                        + 'Verificar en la Web esto último y reportar el error con el log'))
        return itemlist
    item.url_control = item.url
    item.url = urlparse.urljoin(host, scrapertools.find_single_match(data, patron))
    
    #buscamos subtítulos en español     ###     CÓDIGO HEREDADO DE RARBG.  LO DEJAMOS POR SI ES NECESARIO EN EL FUTURO
    patron = '<tr><td align="(?:[^"]+)?"\s*class="(?:[^"]+)?"\s*>\s*Subs.*?<\/td>'
    patron += '<td class="(?:[^"]+)?"\s*>(.*?)(?:<br\/>)?<\/td><\/tr>'
    data_subt = scrapertools.find_single_match(data, patron)
    if data_subt:
        patron = '<a href="([^"]+)"\s*onmouseover="return overlib\('
        patron += "'Download Spanish subtitles'"
        patron += '\)"\s*onmouseout="(?:[^"]+)?"\s*><img src="(?:[^"]+)?"\s*><\/a>'
        subt = scrapertools.find_single_match(data_subt, patron)
        if subt:
            item.subtitle = urlparse.urljoin(host, subt)
    
    if item.subtitle:                                                   #Si hay urls de sub-títulos, se descargan
        from core import filetools
        from core import downloadtools
        from core import ziptools
    
        headers.append(["User-Agent", httptools.get_user_agent()])      #Se busca el User-Agent por defecto
        videolibrary_path = config.get_videolibrary_path()              #Calculamos el path absoluto a partir de la Videoteca
        if videolibrary_path.lower().startswith("smb://"):              #Si es una conexión SMB, usamos userdata local
            videolibrary_path = config.get_data_path()                  #Calculamos el path absoluto a partir de Userdata
        videolibrary_path = filetools.join(videolibrary_path, "subtitles")
        #Primero se borra la carpeta de subtitulos para limpiar y luego se crea
        if filetools.exists(videolibrary_path):   
            filetools.rmtree(videolibrary_path, ignore_errors=True)
            time.sleep(1)
        if not filetools.exists(videolibrary_path):   
            filetools.mkdir(videolibrary_path)
        subtitle_name = 'Rarbg-ES_SUBT.zip'                                     #Nombre del archivo de sub-títulos
        subtitle_folder_path = filetools.join(videolibrary_path, subtitle_name)   #Path de descarga
        ret = downloadtools.downloadfile(item.subtitle, subtitle_folder_path, 
                        headers=headers, continuar=True, silent=True)

        if filetools.exists(subtitle_folder_path):
            # Descomprimir zip dentro del addon
            # ---------------------------------
            try:
                unzipper = ziptools.ziptools()
                unzipper.extract(subtitle_folder_path, videolibrary_path)
            except:
                import xbmc
                xbmc.executebuiltin('Extract("%s", "%s")' % (subtitle_folder_path, videolibrary_path))
                time.sleep(1)
            
            # Borrar el zip descargado
            # ------------------------
            filetools.remove(subtitle_folder_path)
            
            #Tomo el primer archivo de subtítulos como valor por defecto
            for raiz, subcarpetas, ficheros in filetools.walk(videolibrary_path):
                for f in ficheros:
                    if f.endswith(".srt"):
                        #f_es = 'rarbg_subtitle.spa.srt'
                        f_es = scrapertools.find_single_match(item.url, '&f=(.*?).torrent$')\
                                .replace('.', ' ').replace('-', ' ').lower() + '.spa.srt'
                        if not f_es:
                            f_es = item.infoLabels['originaltitle'] + '.spa.srt'
                            f_es = f_es.replace(':', '').lower()
                        filetools.rename(filetools.join(videolibrary_path, f), filetools.join(videolibrary_path, f_es))
                        item.subtitle = filetools.join(videolibrary_path, f_es)   #Archivo de subtitulos
                        break
                break
        
    itemlist.append(item.clone())                                               #Reproducción normal
        
    return itemlist

    
def episodios(item):
    logger.info()
    itemlist = []
    item.category = categoria
    
    host = config.get_setting('domain_name', channel)
    
    #logger.debug(item)

    if item.from_title:
        item.title = item.from_title
    
    #Limpiamos num. Temporada y Episodio que ha podido quedar por Novedades
    season_display = 0
    if item.contentSeason:
        if item.season_colapse:                                                             #Si viene del menú de Temporadas...
            season_display = item.contentSeason                                             #... salvamos el num de sesión a pintar
            item.from_num_season_colapse = season_display
            del item.season_colapse
            item.contentType = "tvshow"
            if item.from_title_season_colapse:
                item.title = item.from_title_season_colapse
                del item.from_title_season_colapse
                if item.infoLabels['title']:
                    del item.infoLabels['title']
        del item.infoLabels['season']
    if item.contentEpisodeNumber:
        del item.infoLabels['episode']
    if season_display == 0 and item.from_num_season_colapse:
        season_display = item.from_num_season_colapse

    # Obtener la información actualizada de la Serie.  TMDB es imprescindible para Videoteca
    try:
        tmdb.set_infoLabels(item, True, idioma_busqueda='es,en')
    except:
        pass
        
    modo_ultima_temp_alt = modo_ultima_temp
    if item.ow_force == "1":                                    #Si hay un traspaso de canal o url, se actualiza todo 
        modo_ultima_temp_alt = False
    
    max_temp = 1
    if item.infoLabels['number_of_seasons']:
        max_temp = item.infoLabels['number_of_seasons']
    y = []
    patron = 'season (\d+)'
    if modo_ultima_temp_alt and item.library_playcounts:        #Averiguar cuantas temporadas hay en Videoteca
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_temp = max(y)

    # Descarga la página
    data = ''
    try:
        response = httptools.downloadpage(item.url, timeout=timeout, ignore_response_code=True)
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data)
        if not PY3:
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    except:
        pass
    if not response.sucess:
        host, data = retry_alt(item.url, timeout)                               # Si hay un error se pasa a la web alternativa
        
    if not data:
        logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea" + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. ' 
                        + 'Si la Web está activa, reportar el error con el log'))
        return itemlist
    
    #Comprobamos si la IP ha sido bloqueada, y si es así, lo intentamos con otra url
    status, itemlist, host, data = check_blocked_IP(data, itemlist, item.url, timeout=timeout)
    if status:
        return itemlist                                                         #IP bloqueada

    #Capturamos las temporadas de episodios dentro de la serie
    patron_temp = '<ul class="list-group eplist" id="eps_(\d+)">(.*?)<\/ul><\/div><\/div><\/div>'
    temp_serie = re.compile(patron_temp, re.DOTALL).findall(data)
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(temp_serie)
    #logger.debug(data)
    
    if not temp_serie:                                                          #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " 
                        + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  ' 
                        + 'Reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    for season_num, temporada in temp_serie:
        
        patron =  '<li\s*class="list-group-item">\s*<div\s*class="[^"]+">\s*<a\s*'
        patron += '(?:class="([^"]*)"\s*)?href="([^"]+)">\s*(?:<span\s*class=[^<]+<\/span>\s*)?'
        patron += '<i[^>]+>\s*<\/i>\s*<\/a>\s*<\/div>\s*<span\s*class="smaller\s*text-muted\s*epnum">'
        patron += '\s*(\d+)\s*<\/span>(?:\s*<span[^<]+)?\s*<(?:a|span)\s*class="[^"]*pad-r2"[^>]*>\s*([^<]*)<'
        matches = re.compile(patron, re.DOTALL).findall(temporada)

        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(temporada)
        
        season = max_temp
        #Comprobamos si realmente sabemos el num. máximo de temporadas
        if item.library_playcounts or (item.infoLabels['number_of_seasons'] and item.tmdb_stat):
            num_temporadas_flag = True
        else:
            num_temporadas_flag = False

        if modo_ultima_temp_alt and item.library_playcounts:    #Si solo se actualiza la última temporada de Videoteca
            if int(season_num) < max_temp:
                break                                           #Sale del bucle actual del FOR
        
        # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
        for muted, epi_url, episode_num, scrapedtitle in matches:
            if 'TBA' in scrapedtitle or 'text-muted' in muted:
                continue
            item_local = item.clone()
            item_local.action = "findvideos"
            item_local.contentType = "episode"
            item_local.extra = "episodios"
            if item_local.library_playcounts:
                del item_local.library_playcounts
            if item_local.library_urls:
                del item_local.library_urls
            if item_local.path:
                del item_local.path
            if item_local.update_last:
                del item_local.update_last
            if item_local.update_next:
                del item_local.update_next
            if item_local.channel_host:
                del item_local.channel_host
            if item_local.active:
                del item_local.active
            if item_local.contentTitle:
                del item_local.infoLabels['title']
            if item_local.season_colapse:
                del item_local.season_colapse

            item_local.title = ''
            item_local.context = "['buscar_trailer']"
            title = scrapedtitle
            item_local.language = []
            if not item_local.infoLabels['poster_path']:
                item_local.thumbnail = item_local.infoLabels['thumbnail']
            epi_rango = False

            try:
                item_local.contentSeason = int(season_num)
                if 'season pack' in title.lower():
                    item_local.contentEpisodeNumber = 1
                    epi_rango = True
                else:
                    item_local.contentEpisodeNumber = int(episode_num)
            except:
                logger.error('ERROR al extraer Temporada/Episodio: ' + title)
                item_local.contentSeason = 1
                item_local.contentEpisodeNumber = 0
            
            #Si son episodios múltiples, lo extraemos
            if epi_rango:
                item_local.infoLabels['episodio_titulo'] = 'al 99'
                item_local.title = '%sx%s al 99 - Season Pack' % (str(item_local.contentSeason), 
                        str(item_local.contentEpisodeNumber).zfill(2))
            else:
                item_local.title = '%sx%s - ' % (str(item_local.contentSeason), 
                        str(item_local.contentEpisodeNumber).zfill(2))

            item_local.url = urlparse.urljoin(host, epi_url)
            item_local.url = re.sub(r'#eps.*?$', '%sx%s.html' % (str(item_local.contentSeason), 
                        str(item_local.contentEpisodeNumber)), item_local.url)
            
            if season_display > 0:
                if item_local.contentSeason > season_display:
                    continue
                elif item_local.contentSeason < season_display:
                    break
            
            itemlist.append(item_local.clone())

            #logger.debug(item_local)
        
        if len(itemlist) == 0 and max_temp > 1:
            max_temp -= 1
            
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))       #clasificamos
        
    if item.season_colapse and not item.add_videolibrary:                       #Si viene de listado, mostramos solo Temporadas
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist)

    if not item.season_colapse:                                                 #Si no es pantalla de Temporadas, pintamos todo
        # Pasada por TMDB y clasificación de lista por temporada y episodio
        tmdb.set_infoLabels(itemlist, True, idioma_busqueda='es,en')

        #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    #logger.debug(item)

    return itemlist
    
    
def check_blocked_IP(data, itemlist, url, timeout=timeout):
    logger.info()
    thumb_separador = get_thumb("next.png")
    
    host = scrapertools.find_single_match(url, '(http.*\:\/\/(?:.*ww[^\.]*\.)?[^\.]+\.[^\/]+)(?:\/|\?|$)')
    
    if 'Please wait while we try to verify your browser...' in data:
        logger.error("ERROR 99: La IP ha sido bloqueada por la Web" + " / URL: " 
                        + url + " / DATA: " + data)
        host, data = retry_alt(url, timeout)                                    # Intentamos con otra web
        if data:
            return (False, itemlist, host, data)                                # Ha habido éxito
        
        itemlist.append(Item(channel=channel, url=host, 
                        title="[COLOR yellow]La IP ha sido bloqueada por la Web.[/COLOR]", 
                        folder=False, thumbnail=thumb_separador))
        itemlist.append(Item(channel=channel, url=host, 
                        title="[COLOR yellow]Fuerce la renovación de la IP en el Router[/COLOR]", 
                        folder=False, thumbnail=thumb_separador))
        from platformcode import platformtools
        platformtools.dialog_notification("IP bloqueada", "ZOOQLE: Reiniciar ROUTER")
    
        return (True, itemlist, host, data)                                     # Webs bloqueadas
    return (False, itemlist, host, data)                                        # No hay bloqueo
    
    
def retry_alt(url, timeout=timeout):                                            # Reintentamos con la web alternativa
    logger.info()
    
    random.shuffle(host_alt)
    host_a = scrapertools.find_single_match(url, '(http.*\:\/\/(?:.*ww[^\.]*\.)?[^\.]+\.[^\/]+)(?:\/|\?|$)')
    
    logger.error("ERROR 98: Web caída, reintentando..." + " / URL: " + url)
    config.set_setting('domain_name', host, channel)                            # Reseteamos el dominio
    
    for host_b in host_alt:
        if host_b in url:
            continue

        url_final = url.replace(host_a, host_b)
        
        data = ''
        try:
            response = httptools.downloadpage(url_final, timeout=timeout, count_retries_tot=1, ignore_response_code=True)
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", response.data)
            if not PY3:
                data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        except:
            pass
            
        if response.sucess and not 'Please wait while we try to verify your browser...' in data:
            break
        logger.error("ERROR 98: Web caída, reintentando..." + " / URL: " + host_b)
    
    else:
        logger.error("ERROR 97: Webs caídas, ninguna Web alternativa encontrada")
        return (host_a, '')

    logger.error("ERROR 96: Web caída encontrada" + " / URL: " + host_b)
    config.set_setting('domain_name', host_b, channel)                          # Cambiamos el dominio por defecto
    
    return (host_b, data)
    
    
def actualizar_titulos(item):
    logger.info()
    
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    item = generictools.update_title(item)
    
    #Volvemos a la siguiente acción en el canal
    return item

    
def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    
    host = config.get_setting('domain_name', channel)
    
    try:
        item.url = host + 'search?q=%s' % texto
        item.extra = 'search'

        if texto != '':
            return listado(item)
    except:
        import sys
        import traceback
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc())
        return []
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    
    host = config.get_setting('domain_name', channel)
    
    item.title = "newest"
    item.category_new = "newest"
    item.channel = channel
    
    try:
        if categoria == 'peliculas':
            item.url = host + 'mov/?age=mon&s=dt&sd=d&tg=0'
            item.extra = "peliculas"
            item.action = "listado"
            itemlist = listado(item)
                
        elif categoria == 'series':
            item.url = host + 'browse/tv/?s=dt&sd=d'
            item.extra = "series"
            item.action = "listado"
            itemlist = listado(item)

        if len(itemlist) > 0 and (">> Página siguiente" in itemlist[-1].title or "Pagina siguiente >>" in itemlist[-1].title):
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
