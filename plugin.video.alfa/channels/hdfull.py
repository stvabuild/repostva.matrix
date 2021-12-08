# -*- coding: utf-8 -*-

#from builtins import str
from builtins import chr
from builtins import range
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
    import urllib.parse as urlparse
    from lib import alfaresolver_py3 as alfaresolver
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido
    import urlparse
    from lib import alfaresolver

import base64
import re

from core import httptools
from core import jsontools
from core import scrapertools
from core import servertools, tmdb
from core import channeltools
from core.item import Item
from platformcode import config, logger, help_window
from channels import autoplay
from channels import filtertools
from platformcode import platformtools
from channelselector import get_thumb

host = config.get_setting("current_host", channel="hdfull")
host_blacklist = ['https://www2.hdfull.cx/', 'https://hdfull.sh/', 'https://hdfull.ch/', 
                  'https://hdfull.im/', 'https://hdfull.in/', 'https://hdfull.pro/', 
                  'https://hdfull.one/']


_silence = config.get_setting('silence_mode', channel='hdfull')
show_langs = config.get_setting('show_langs', channel='hdfull')
unify = config.get_setting('unify')
__modo_grafico__ = config.get_setting('modo_grafico', channel='hdfull')
account = config.get_setting("logged", channel="hdfull")
credentials_req = True

IDIOMAS = {'lat': 'LAT', 'spa': 'CAST', 'esp': 'CAST', 'sub': 'VOSE', 'espsub': 'VOSE', 'engsub': 'VOS', 'eng': 'VO'}
list_language = list(set(IDIOMAS.values()))
list_quality = ['HD1080', 'HD720', 'HDTV', 'DVDRIP', 'RHDTV', 'DVDSCR']
list_servers = ['clipwatching', 'gamovideo', 'vidoza', 'vidtodo', 'openload', 'uptobox']


def verify_login(force_check=False, force_login=True):
    global account, credentials_req
    
    credentials = config.get_setting('hdfulluser', channel='hdfull')
    if account and credentials and not force_check:
        return account
    
    else:
        if credentials:
            account = login()
        else:
            account = False
        if not account:
            logger.info('NO LOGIN credentials', force=True)
            if force_login:
                if credentials_req:
                    help_window.show_info('hdfull_login', wait=False)
                    settingCanal(Item)
                    credentials = config.get_setting('hdfulluser', channel='hdfull')
                    if credentials:
                        account = login()
                    else:
                        credentials_req = False
        return account

def login():
    logger.info()

    data = agrupa_datos(host, referer=False, force_check=False, force_login=False)
    _logged = 'id="header-signout" href="/logout"'
    if _logged in data:
        config.set_setting("logged", True, channel="hdfull")
        logger.info('LOGGED', force=True)
        return True
    else:
        patron = "<input type='hidden' name='__csrf_magic' value=\"([^\"]+)\" />"
        sid = urllib.quote(scrapertools.find_single_match(data, patron))
        user_ = urllib.quote(config.get_setting('hdfulluser', channel='hdfull', default=''))
        pass_ = config.get_setting('hdfullpassword', channel='hdfull', default='')
        if pass_:
            pass_ = urllib.quote(pass_)
        if not pass_:
            if not _silence:
                platformtools.dialog_notification("Falta la contraseña", 
                                              "Revise sus datos en la configuración del canal",
                                              sound=False)
            config.set_setting("logged", False, channel="hdfull")
            logger.info('NO password for LOGIN', force=True)
            return False
        post = '__csrf_magic=%s&username=%s&password=%s&action=login' % (sid, user_, pass_)

        new_data = agrupa_datos(host, post=post, referer=False, force_check=False, force_login=False)

        if _logged in new_data:
            config.set_setting("logged", True, channel="hdfull")
            logger.info('Just LOGGED', force=True)
            return True
        
        elif _silence:
            config.set_setting("logged", False, channel="hdfull")
            logger.info('Error on LOGIN', force=True)
            return False
        
        else:
            platformtools.dialog_notification("No se pudo realizar el login",
                                             "Revise sus datos en la configuración del canal",
                                             sound=False)
            config.set_setting("logged", False, channel="hdfull")
            logger.info('Error on LOGIN', force=True)
            return False


def settingCanal(item):
    platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return 
    
def logout(item):
    global account
    logger.info()
    domain = urlparse.urlparse(host).netloc
    dict_cookie = {"domain": domain, 'expires': 0}
    #borramos cookies de hdfull
    httptools.set_cookies(dict_cookie)

    #borramos el login
    config.set_setting("hdfulluser", "", channel="hdfull")
    config.set_setting("hdfullpassword", "", channel="hdfull")
    config.set_setting("logged", False, channel="hdfull")
    account = False
    
    #avisamos, si nos dejan
    if not _silence:
        platformtools.dialog_notification("Deslogueo completo", 
                                          "Reconfigure su cuenta",
                                          sound=False,)
    platformtools.itemlist_refresh()
    return item

def agrupa_datos(url, post=None, referer=True, json=False, proxy=True, forced_proxy=None, 
                 proxy_retries=1, force_check=False, force_login=True):
    global host, account
    
    if force_check or force_login:
        verify_login(force_check=force_check, force_login=force_login)
    
    headers = {'Referer': host}
    if 'episodes' in url or 'buscar' in url:
        headers['Referer'] += 'episodios'
    
    if not referer:
        headers.pop('Referer')
    # if cookie:
    #     headers.update('Cookie:' 'language=es')
    if isinstance(referer, str):
        headers.update({'Referer': referer})
    
    if host in host_blacklist:
        list_controls, dict_settings = channeltools.get_channel_controls_settings("hdfull")
        config.set_setting("current_host", dict_settings['current_host'], channel="hdfull")
        host = dict_settings['current_host']
    
    parsed = urlparse.urlparse(host)
    
    if len(parsed.path) > 1:
        parse_url = "https://%s/" % parsed.netloc
        config.set_setting("current_host", parse_url, channel="hdfull")
    
    url = re.sub(r'http(?:s|)://[^/]+/', host, url)
    page = httptools.downloadpage(url, post=post, headers=headers, ignore_response_code=True, 
                        proxy=proxy, forced_proxy=forced_proxy, proxy_retries=proxy_retries)
    
    if not page.sucess:
        list_controls, dict_settings = channeltools.get_channel_controls_settings("hdfull")
        if dict_settings['current_host'] != config.get_setting("current_host", channel="hdfull", default=""):
            config.set_setting("current_host", dict_settings['current_host'], channel="hdfull")
            host = dict_settings['current_host']
            return agrupa_datos(url, post=post, referer=referer, json=json, proxy=True, forced_proxy='ProxyWeb', proxy_retries=0)
    if not page.sucess and not proxy:
        return agrupa_datos(url, post=post, referer=referer, json=json, proxy=True, forced_proxy='ProxyWeb', proxy_retries=0)
    if not page.sucess:
        account = False
        config.set_setting("logged", False, channel="hdfull")
    
    new_host = scrapertools.find_single_match(page.data,
                    r'location.replace\("(http(?:s|)://\w+.hdfull.\w{2,4})')

    backup =  scrapertools.find_single_match(page.data,
                    r'onclick="redirect\(\)"><strong>(http[^<]+)')
    if not new_host and backup and 'dominio temporalmente' in page.data:
        new_host = backup
    if new_host:
        
        if not new_host.endswith('/'):
            new_host += '/'
        config.set_setting("current_host", new_host, channel="hdfull")
        url = re.sub(host, new_host, url)

        host = config.get_setting("current_host", channel="hdfull")
        
        return agrupa_datos(url, post=post, referer=referer, json=json)
    
    if json:
        return page.json
    # if raw:
    #     return page.data
    
    data = page.data
    if PY3 and isinstance(data, bytes):
        data = "".join(chr(x) for x in bytes(data))
    ## Agrupa los datos
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|<!--.*?-->', '', data)
    data = re.sub(r'\s+', ' ', data)
    data = re.sub(r'>\s<', '><', data)
    return data


def mainlist(item):
    logger.info()
    itemlist = []
    
    verify_login(force_check=True, force_login=False)

    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, action="menupeliculas", title="Películas", url=host,
                         thumbnail=get_thumb('movies', auto=True), text_bold=True))
    itemlist.append(Item(channel=item.channel, action="menuseries", title="Series", url=host,
                         thumbnail=get_thumb('tvshows', auto=True), text_bold=True))
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar...",
                         thumbnail=get_thumb('search', auto=True), text_bold=True))

    itemlist = filtertools.show_option(itemlist, item.channel, list_language, list_quality)

    autoplay.show_option(item.channel, itemlist)
    
    if not account:
        itemlist.append(Item(channel=item.channel,  action="", url="", text_bold=True,
                        title="[COLOR gold]Registrate en %s y luego habilita tu cuenta[/COLOR]" % host,
                        thumbnail=get_thumb("setting_0.png")))
        itemlist.append(Item(channel=item.channel,  action="settingCanal", url="", text_bold=True,
                        title="[COLOR dodgerblue]Habilita tu cuenta para activar los items de usuario...[/COLOR]",
                        thumbnail=get_thumb("setting_0.png")))
    else:
        itemlist.append(Item(channel=item.channel, action="",  url="",
                             title="", folder=False,
                             thumbnail=get_thumb("setting_0.png")))
        
        itemlist.append(Item(channel=item.channel, action="settingCanal",  url="",
                             title="[COLOR greenyellow][B]Configurar Canal[/B][/COLOR]",
                             thumbnail=get_thumb("setting_0.png"), folder=False))

        itemlist.append(Item(channel=item.channel, action="logout", url="", folder=False,
                             title="[COLOR steelblue][B]Desloguearse[/B][/COLOR]",
                             plot="Para cambiar de usuario", thumbnail=get_thumb("back.png")))
    return itemlist


def menupeliculas(item):
    logger.info()
    itemlist = []

    
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Películas Estreno",
             url=urlparse.urljoin(host, "/peliculas-estreno"),
             text_bold=True, thumbnail=get_thumb('premieres', auto=True)))
    
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Últimas Películas",
             url=urlparse.urljoin(host, "/peliculas"), text_bold=True,
             thumbnail=get_thumb('last', auto=True)))
    
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Películas Actualizadas",
             url=urlparse.urljoin(host, "/peliculas-actualizadas"), text_bold=True,
             thumbnail=get_thumb('updated', auto=True)))
   
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Rating IMDB",
             url=urlparse.urljoin(host, "/peliculas/imdb_rating"),
             text_bold=True, thumbnail=get_thumb('recomended', auto=True)))
    
    itemlist.append(
        Item(channel=item.channel, action="generos", title="Películas por Género",
             url=host, text_bold=True, type='peliculas',
             thumbnail=get_thumb('genres', auto=True)))
    
    # itemlist.append(
    #     Item(channel=item.channel, action="fichas", title="ABC",
    #          url=urlparse.urljoin(host, "/peliculas/abc"), text_bold=True,
    #          thumbnail=get_thumb('alphabet', auto=True)))
    
    if account:
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR dodgerblue][B]Vistas[/B][/COLOR]",
                             url=urlparse.urljoin(host, "/a/my?target=movies&action=seen&start=-28&limit=28"),
                             thumbnail=item.thumbnail))

        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange][B]Favoritos[/B][/COLOR]",
                             url=urlparse.urljoin(host, "/a/my?target=movies&action=favorite&start=-28&limit=28"),
                             thumbnail=item.thumbnail))
        
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR dodgerblue][B]Pendientes[/B][/COLOR]",
                             url=urlparse.urljoin(host, "/a/my?target=movies&action=pending&start=-28&limit=28"),
                             thumbnail=item.thumbnail))
    return itemlist


def menuseries(item):
    logger.info()
    itemlist = []

    
    itemlist.append(
        Item(channel=item.channel, action="novedades_episodios", title="Episodios Estreno",
             url=urlparse.urljoin(host, "/a/episodes?action=premiere&start=-24&limit=24&elang=ALL"), text_bold=True,
             thumbnail=get_thumb('newest', auto=True)))
    itemlist.append(
        Item(channel=item.channel, action="novedades_episodios", title="Últimos Emitidos",
             url=urlparse.urljoin(host, "/a/episodes?action=latest&start=-24&limit=24&elang=ALL"), text_bold=True,
             thumbnail=get_thumb('new episodes', auto=True)))

    itemlist.append(
        Item(channel=item.channel, action="novedades_episodios", title="Episodios Anime",
             url=urlparse.urljoin(host, "/a/episodes?action=anime&start=-24&limit=24&elang=ALL"), text_bold=True,
             thumbnail=get_thumb('anime', auto=True)))
    itemlist.append(
        Item(channel=item.channel, action="novedades_episodios", title="Episodios Actualizados",
             url=urlparse.urljoin(host, "/a/episodes?action=updated&start=-24&limit=24&elang=ALL"), text_bold=True,
             thumbnail=get_thumb('updated', auto=True)))
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Últimas series",
             url=urlparse.urljoin(host, "/series"), text_bold=True,
             thumbnail=get_thumb('last', auto=True)))
    itemlist.append(
        Item(channel=item.channel, action="fichas", title="Rating IMDB", 
             url=urlparse.urljoin(host, "/series/imdb_rating"), text_bold=True,
             thumbnail=get_thumb('recomended', auto=True)))
    itemlist.append(
        Item(channel=item.channel, action="generos", title="Series por Género",
             url=host, text_bold=True, type='series',
             thumbnail=get_thumb('genres', auto=True)))
    
    itemlist.append(
        Item(channel=item.channel, action="series_abc", title="A-Z",
             text_bold=True, thumbnail=get_thumb('alphabet', auto=True)))

    #Teniendo el listado alfabetico esto sobra y necesita paginación
    #itemlist.append(Item(channel=item.channel, action="listado_series", title="Listado de todas las series",
    #                     url=host + "/series/list", text_bold=True))

    if account:
        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR dodgerblue]Siguiendo[/COLOR]",
                             url=urlparse.urljoin(host, "/a/my?target=shows&action=following&start=-28&limit=28"), text_bold=True,
                             thumbnail=item.thumbnail))

        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR dodgerblue]Para Ver[/COLOR]",
                             url=urlparse.urljoin(host, "/a/my?target=shows&action=watch&start=-28&limit=28"), text_bold=True,
                             thumbnail=item.thumbnail))

        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR orange]Favoritas[/COLOR]",
                             url=urlparse.urljoin(host, "/a/my?target=shows&action=favorite&start=-28&limit=28"), text_bold=True,
                             thumbnail=item.thumbnail))

        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR dodgerblue]Pendientes[/COLOR]",
                             url=urlparse.urljoin(host, "/a/my?target=shows&action=pending&start=-28&limit=28"), text_bold=True,
                             thumbnail=item.thumbnail))

        itemlist.append(Item(channel=item.channel, action="items_usuario",
                             title="[COLOR dodgerblue]Vistas[/COLOR]",
                             url=urlparse.urljoin(host, "/a/my?target=shows&action=seen&start=-28&limit=28"), text_bold=True,
                             thumbnail=item.thumbnail))
    
    return itemlist


def search(item, texto):
    logger.info()
    
    try:
        verify_login(force_check=True, force_login=False)
        
        data = agrupa_datos(host, referer=False)
        sid = scrapertools.find_single_match(data, '.__csrf_magic. value="(sid:[^"]+)"')
        item.extra = urllib.urlencode({'__csrf_magic': sid}) + '&menu=search&query=' + texto
        item.title = "Buscar..."
        item.url = urlparse.urljoin(host,  "/buscar")
        item.texto = texto
        return fichas(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def series_abc(item):
    logger.info()
    itemlist = []
    page = config.get_setting('pagination_abc', channel='hdfull')
    page = 0 if page else ''
    az = "#ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for l in az:
        itemlist.append(
            Item(channel=item.channel, action='fichas', title=l, 
                 url= urlparse.urljoin(host, "/series/abc/%s" %  l.replace('#', '9')),
                 thumbnail=item.thumbnail, page=page, text_bold=True))
    return itemlist


def items_usuario(item):
    logger.info()
    itemlist = []
    ## Carga estados
    status = check_status()
    ## Fichas usuario
    url = item.url.split("?")[0]
    post = item.url.split("?")[1]
    old_start = scrapertools.find_single_match(post, 'start=([^&]+)&')
    limit = scrapertools.find_single_match(post, 'limit=(\d+)')
    start = "%s" % (int(old_start) + int(limit))
    post = post.replace("start=" + old_start, "start=" + start)
    next_page = url + "?" + post
    ## Carga las fichas de usuario
    fichas_usuario = agrupa_datos(url, post=post, json=True)
    for ficha in fichas_usuario:
        try:
            title = ficha['title']['es'].strip()
        except:
            title = ficha['title']['en'].strip()
        try:
            if not PY3: title = title.encode('utf-8')
        except:
            pass
        show = title
        try:
            thumbnail = urlparse.urljoin(host, "/thumbs/" + ficha['thumbnail'])
        except:
            thumbnail = urlparse.urljoin(host,  "/thumbs/" + ficha['thumb'])
        thumbnail += '|User-Agent=%s' % httptools.get_user_agent()
        try:
            url = urlparse.urljoin(host, '/serie/' + ficha['permalink']) + "###" + ficha['id'] + ";1"
            action = "seasons"
            str = get_status(status, 'shows', ficha['id'])
            if "show_title" in ficha:
                action = "findvideos"
                try:
                    serie = ficha['show_title']['es'].strip()
                except:
                    serie = ficha['show_title']['en'].strip()
                temporada = ficha['season']
                episodio = ficha['episode']
                serie = "[COLOR whitesmoke]" + serie + "[/COLOR]"
                if len(episodio) == 1: episodio = '0' + episodio
                try:
                    title = temporada + "x" + episodio + " - " + serie + ": " + title
                except:
                    title = temporada + "x" + episodio + " - " + serie.decode('iso-8859-1') + ": " + title.decode(
                        'iso-8859-1')
                url = urlparse.urljoin(host, '/serie/' + ficha[
                    'permalink'] + '/temporada-' + temporada + '/episodio-' + episodio) + "###" + ficha['id'] + ";3"
                if str != "": title += str
            itemlist.append(
                    Item(channel=item.channel, action=action, title=title,
                        url=url, thumbnail=thumbnail,
                        contentSerieName=show, text_bold=True))
        except:
            url = urlparse.urljoin(host, '/pelicula/' + ficha['perma']) + "###" + ficha['id'] + ";2"
            str = get_status(status, 'movies', ficha['id'])
            if str != "": title += str
            itemlist.append(
                Item(channel=item.channel, action="findvideos", title=title, 
                     contentTitle=show, url=url, thumbnail=thumbnail,
                     text_bold=True, infoLabels={'year': '-'}))
    if len(itemlist) == int(limit):
        itemlist.append(
            Item(channel=item.channel, action="items_usuario", title=">> Página siguiente", url=next_page, text_bold=True))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    
    return itemlist


'''def listado_series(item):
    logger.info()
    itemlist = []
    data = agrupa_datos(item.url)
    patron = '<div class="list-item"><a href="([^"]+)"[^>]+>([^<]+)</a></div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl + "###0;1"
        itemlist.append(
            Item(channel=item.channel, action="seasons", title=scrapedtitle, contentTitle=scrapedtitle, url=url,
                 contentSerieName=scrapedtitle, contentType="tvshow"))
    return itemlist'''


def fichas(item):
    logger.info()
    itemlist = []
    or_matches = ""
    textoidiomas=''
    infoLabels=dict()
    ## Carga estados
    status = check_status()

    if item.title == "Buscar...":
        data = agrupa_datos(item.url, post=item.extra)
        s_p = scrapertools.find_single_match(data, '<h3 class="section-title">(.*?)<div id="footer-wrapper">').split(
            '<h3 class="section-title">')
        if len(s_p) == 1:
            data = s_p[0]
            if 'Lo sentimos</h3>' in s_p[0]:
                return [Item(channel=item.channel, title="[COLOR gold][B]HDFull:[/B][/COLOR] [COLOR steelblue]" + item.texto.replace('%20',
                                                                                       ' ') + "[/COLOR] sin resultados")]
        else:
            data = s_p[0] + s_p[1]
    elif 'series/abc' in item.url:
        data = agrupa_datos(item.url, referer=item.url)
    else:
        data = agrupa_datos(item.url)

    data = re.sub(
        r'<div class="span-6[^<]+<div class="item"[^<]+' + \
        '<a href="([^"]+)"[^<]+' + \
        '<img.*?src="([^"]+)".*?' + \
        '<div class="left"(.*?)</div>' + \
        '<div class="right"(.*?)</div>.*?' + \
        'title="([^"]+)".*?' + \
        'onclick="setFavorite.\d, (\d+),',
        r"'url':'\1';'image':'\2';'langs':'\3';'rating':'\4';'title':\5;'id':'\6';",
        data
    )
    patron = "'url':'([^']+)';'image':'([^']+)';'langs':'([^']+)';'rating':'([^']+)';'title':([^;]+);'id':'([^']+)';"
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    if item.page != '':
        or_matches = matches
        matches = matches[item.page:item.page + 40]
    
    for scrapedurl, scrapedthumbnail, scrapedlangs, scrapedrating, scrapedtitle, scrapedid in matches:

        thumbnail = scrapedthumbnail.replace('tthumb/130x190', 'thumbs')
        thumbnail += '|User-Agent=%s' % httptools.get_user_agent()
        language = ''
        title = scrapedtitle.strip()
        show = title

        #Valoración
        if scrapedrating != ">" and not unify:
            valoracion = re.sub(r'><[^>]+>(\d+)<b class="dec">(\d+)</b>', r'\1,\2', scrapedrating)
            title += " [COLOR greenyellow](%s)[/COLOR]" % valoracion
        
        #Idiomas
        if scrapedlangs != ">":
            textoidiomas, language = extrae_idiomas(scrapedlangs)

            if show_langs:
                title += " [COLOR darkgrey]%s[/COLOR]" % textoidiomas
        
        url = urlparse.urljoin(item.url, scrapedurl)
        #Acción para series/peliculas
        if "/serie" in url or "/tags-tv" in url:
            action = "seasons"
            url += "###" + scrapedid + ";1"
            type = "shows"
            contentType = "tvshow"
        else:
            action = "findvideos"
            url += "###" + scrapedid + ";2"
            type = "movies"
            contentType = "movie"
            infoLabels['year']= '-'
        #items usuario en titulo (visto, pendiente, etc)
        if account:
            str = get_status(status, type, scrapedid)
            if str != "": title += str
        #Muesta tipo contenido tras busqueda
        if item.title == "Buscar...":
            bus = host[-4:]
            #Cuestiones estéticas (TODO probar unify)
            c_t = "darkgrey" 
            
            tag_type = scrapertools.find_single_match(url, '%s([^/]+)/' %bus)
            if tag_type == 'pelicula':
                c_t = "steelblue"
            title += " [COLOR %s](%s)[/COLOR]" % (c_t, tag_type.capitalize())
            

        if "/serie" in url or "/tags-tv" in url:
            itemlist.append(
                Item(channel=item.channel, action=action, title=title, url=url,
                     contentSerieName=show, text_bold=True, contentType=contentType,
                     language=language, infoLabels=infoLabels, thumbnail=thumbnail,
                     context=filtertools.context(item, list_language, list_quality)))
        else:
            itemlist.append(
                Item(channel=item.channel, action=action, title=title, url=url,
                     text_bold=True, contentTitle=show, language=language, 
                     infoLabels=infoLabels, thumbnail=thumbnail))
    ## Paginación
    next_page_url = scrapertools.find_single_match(data, '<a href="([^"]+)">.raquo;</a>')
    if next_page_url != "":
        itemlist.append(Item(channel=item.channel, action="fichas", title=">> Página siguiente",
                             url=urlparse.urljoin(item.url, next_page_url), text_bold=True))
        
        itemlist.append(Item(channel=item.channel, action="get_page", title=">> Ir a Página...",
                             url=urlparse.urljoin(item.url, next_page_url), text_bold=True,
                             thumbnail=get_thumb('add.png'), text_color='turquoise'))

    elif item.page != '':
        if item.page + 40 < len(or_matches):
            itemlist.append(item.clone(page=item.page + 40, title=">> Página siguiente",
                                       text_bold=True, text_color="blue"))
    
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    
    return itemlist

def seasons(item):
    logger.info()
    id = "0"
    itemlist = []
    infoLabels = item.infoLabels
    
    ## Carga estados
    status = check_status()
    
    url_targets = item.url
    if "###" in item.url:
        id = item.url.split("###")[1].split(";")[0]
        type = item.url.split("###")[1].split(";")[1]
        item.url = item.url.split("###")[0]
    
    data = agrupa_datos(item.url, force_check=False, force_login=False)
    
    if account:
        str = get_status(status, "shows", id)
        #TODO desenredar todo el lio este
        if str != "" and item.category != "Series" and "XBMC" not in item.title:
            platformtools.itemlist_refresh()
            title = str.replace('steelblue', 'darkgrey').replace('Siguiendo', 'Abandonar')
            itemlist.append(Item(channel=item.channel, action="set_status", title=title, url=url_targets,
                                 thumbnail=item.thumbnail, contentSerieName=item.contentSerieName, folder=True))
        elif item.category != "Series" and "XBMC" not in item.title:
            
            title = " [COLOR steelblue][B]( Seguir )[/B][/COLOR]"
            itemlist.append(Item(channel=item.channel, action="set_status", title=title, url=url_targets,
                                 thumbnail=item.thumbnail, contentSerieName=item.contentSerieName, folder=True))
        
    sid = scrapertools.find_single_match(data, "<script>var sid = '(\d+)'")
    
    patron = 'itemprop="season".*?<a href=\'.*?/temporada-(\d+).*?'
    patron += 'alt="([^"]+)" src="([^"]+)"'
    
    matches = re.compile(patron, re.DOTALL).findall(data)

    
    for ssid, scrapedtitle, scrapedthumbnail in matches:
        if ssid == '0':
            scrapedtitle = "Especiales"
        infoLabels['season'] = ssid
        thumbnail = scrapedthumbnail.replace('tthumb/130x190', 'thumbs')
        thumbnail += '|User-Agent=%s' % httptools.get_user_agent()
        
        itemlist.append(
                Item(channel=item.channel, action="episodesxseason", title=scrapedtitle,
                     url=item.url, thumbnail=thumbnail, sid=sid, text_bold=True,
                     contentSerieName=item.contentSerieName,
                     contentSeasonNumber=ssid, infoLabels=infoLabels))

    if config.get_videolibrary_support() and len(itemlist) > 0:
        itemlist.append(Item(channel=item.channel, title="[COLOR greenyellow]Añadir esta serie a la videoteca[/COLOR]",
                             action="add_serie_to_library", url=item.url, text_bold=True, extra="episodios",
                             contentSerieName=item.contentSerieName,
                             ))

    return itemlist


def episodios(item):
    logger.info(item)
    itemlist = []
    
    if item.library_playcounts and item.action == 'get_seasons':    # Es actualización background de videoteca
        verify_login(force_check=True, force_login=False)
    else:
        verify_login(force_check=True, force_login=True)
    
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)

    return itemlist


def episodesxseason(item):
    logger.info()
    itemlist = []
    
    url = urlparse.urljoin(host, "/a/episodes")
    infoLabels = item.infoLabels
    sid = item.sid
    ssid = item.contentSeasonNumber

    #si hay cuenta
    status = check_status()
    
    post = "action=season&start=0&limit=0&show=%s&season=%s" % (sid, ssid)
    #episodes = httptools.downloadpage(url, post=post).json
    episodes = agrupa_datos(url, post=post, json=True, force_check=False, force_login=False)
    
    for episode in episodes:

        language = episode['languages']
        temporada = episode['season']
        episodio = episode['episode']

        #Fix para thumbs
        thumb = episode.get('thumbnail', '')
        if not thumb:
            thumb = episode['show'].get('thumbnail', '')
        ua = httptools.get_user_agent()
        thumbnail = urlparse.urljoin(host, "/thumbs/%s|User-Agent=%s" % (thumb, ua))
        
        infoLabels['episode'] = episodio
        
        if len(episodio) == 1: episodio = '0' + episodio
        
        #Idiomas
        texto_idiomas, langs = extrae_idiomas(language, list_language=True)

        if language != "[]" and show_langs and not unify:
            idiomas = "[COLOR darkgrey]%s[/COLOR]" % texto_idiomas
        
        else:
            idiomas = ""
        
        if episode['title']:
            
            title = episode['title'].get('es', '')
            if not title:
                title = episode['title'].get('en', '')

        if len(title) == 0: title = "Episodio " + episodio
        
        serie = item.contentSerieName
        
        title = '%sx%s: [COLOR greenyellow]%s[/COLOR] %s' % (temporada, episodio, title.strip(), idiomas)
        if account:
            str = get_status(status, 'episodes', episode['id'])
            if str != "": title += str
        
        url = urlparse.urljoin(host, '/serie/' + episode[
            'permalink'] + '/temporada-' + temporada + '/episodio-' + episodio) + "###" + episode['id'] + ";3"
        itemlist.append(item.clone(action="findvideos", title=title, url=url,
                             contentType="episode", language=langs, text_bold=True,
                             infoLabels=infoLabels, thumbnail=thumbnail))

    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)

    return itemlist


def novedades_episodios(item):
    logger.info()
    itemlist = []
    ## Carga estados
    status = check_status()
    
    ## Episodios
    url = item.url.split("?")[0]
    post = item.url.split("?")[1]
    old_start = scrapertools.find_single_match(post, 'start=([^&]+)&')
    start = "%s" % (int(old_start) + 24)
    post = post.replace("start=" + old_start, "start=" + start)
    next_page = url + "?" + post
    episodes = agrupa_datos(url, post=post, json=True)

    for episode in episodes:
        #Fix para thumbs
        thumb = episode['show'].get('thumbnail', '')
        if not thumb:
            thumb = episode.get('thumbnail', '')
        ua = httptools.get_user_agent()
        thumbnail = urlparse.urljoin(host, "/thumbs/%s|User-Agent=%s" % (thumb, ua))
        
        temporada = episode['season']
        episodio = episode['episode']
        #if len(episodio) == 1: episodio = '0' + episodio
        
        #Idiomas
        language = episode.get('languages', '[]')
        texto_idiomas, langs = extrae_idiomas(language, list_language=True)
        
        if language != "[]" and show_langs and not unify:
            idiomas = "[COLOR darkgrey]%s[/COLOR]" % texto_idiomas
        
        else:
            idiomas = ""

        #Titulo serie en español, si no hay, en inglés
        cont_en = episode['show']['title'].get('en', '').strip()
        contentSerieName = episode['show'].get('es', cont_en).strip()


        if episode['title']:
            try:
                title = episode['title']['es'].strip()
            except:
                try:
                    title = episode['title']['en'].strip()
                except:
                    title = ''
        if len(title) == 0: title = "Episodio " + episodio
        
        title = '%s %sx%s: [COLOR greenyellow]%s[/COLOR] %s' % (contentSerieName,
                 temporada, episodio, title, idiomas)

        if account:
            str = get_status(status, 'episodes', episode['id'])
            if str != "": title += str
        
        url = urlparse.urljoin(host, '/serie/' + episode[
            'permalink'] + '/temporada-' + temporada + '/episodio-' + episodio) + "###" + episode['id'] + ";3"
        itemlist.append(
            Item(channel=item.channel, action="findvideos", title=title,
                 contentSerieName=contentSerieName, url=url, thumbnail=thumbnail,
                 contentType="episode", language=langs, text_bold=True))
    
    if len(itemlist) == 24:
        itemlist.append(
            Item(channel=item.channel, action="novedades_episodios", title=">> Página siguiente", 
                url=next_page, text_bold=True))

    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    
    data = agrupa_datos(item.url)
    tipo = '(?:series|tv-shows)'
    if item.type == 'peliculas':
        tipo = '(?:peliculas|movies)'

    data = scrapertools.find_single_match(data, 
        '<li class="dropdown"><a href="/%s"(.*?)</ul>' % tipo)
    patron = '<li><a href="([^"]+)">([^<]+)</a></li>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = urlparse.urljoin(item.url, scrapedurl)
        thumbnail = item.thumbnail
        plot = ""
        itemlist.append(Item(channel=item.channel, action="fichas", title=title,
                             url=url, text_bold=True, thumbnail=thumbnail))
    return itemlist

def findvideos(item):
    logger.info()
    itemlist = []
    it1 = []
    it2 = []

    ## Carga estados
    status = check_status()
    
    url_targets = item.url

    ## Vídeos
    id = ""
    type = ""
    calidad = ""
    if "###" in item.url:
        id = item.url.split("###")[1].split(";")[0]
        type = item.url.split("###")[1].split(";")[1]
        item.url = item.url.split("###")[0]

    if type == "2" and account and item.category != "Cine":
        title = " [COLOR orange][B]( Agregar a Favoritos )[/B][/COLOR]"
        if "Favorito" in item.title:
            title = " [COLOR darkgrey][B]( Quitar de Favoritos )[/B][/COLOR]"

        it1.append(Item(channel=item.channel, action="set_status", title=title, url=url_targets,
                        thumbnail=item.thumbnail, contentTitle=item.contentTitle, language=item.language, folder=True))
    js_url =  urlparse.urljoin(host, "/templates/hdfull/js/jquery.hdfull.view.min.js")
    js_data = agrupa_datos(js_url)
    
    data_js_url = urlparse.urljoin(host, "/js/providers.js")
    data_js = agrupa_datos(data_js_url)
    
    decoded = alfaresolver.jhexdecode(data_js)
    
    providers_pattern = 'p\[(\d+)\]= {"t":"([^"]+)","d":".*?","e":.function.*?,"l":.function.*?return "([^"]+)".*?};'
    providers = scrapertools.find_multiple_matches (decoded, providers_pattern)
    provs = {}
    for provider, e, l in providers:
        provs[provider]=[e,l]

    data = agrupa_datos(item.url, force_check=True, force_login=True)
    try:
        data_decrypt = jsontools.load(alfaresolver.obfs(data, js_data))
    except:
        return []
    
    infolabels = item.infoLabels
    year = scrapertools.find_single_match(data, '<span>Año:\s*</span>.*?(\d{4})')
    infolabels["year"] = year
    matches = []
    for match in data_decrypt:
        if match['provider'] in provs:
            try:
                embed = provs[match['provider']][0]
                url = provs[match['provider']][1]+match['code']
                matches.append([match['lang'], match['quality'], url, embed])
            except:
                pass

    for idioma, calidad, url, embed in matches:
        if embed == 'd':
            option = "Descargar"
            option1 = 2
        else:
            option = "Ver"
            option1 = 1

        idioma = IDIOMAS.get(idioma.lower(), idioma)
        if not PY3:
            calidad = unicode(calidad, "utf8").upper().encode("utf8")
        title = option + ": %s [COLOR greenyellow](" + calidad + ")[/COLOR] [COLOR darkgrey](" + idioma + ")[/COLOR]"
        plot = item.plot
        if not item.plot:
            plot = scrapertools.find_single_match(data,
                                            '<meta property="og:description" content="([^"]+)"')
            plot = scrapertools.htmlclean(plot)
            plot = re.sub('^.*?y latino', '', plot)
        fanart = scrapertools.find_single_match(data, '<div style="background-image.url. ([^\s]+)')
        if account:
            url += "###" + id + ";" + type
        it2.append(
            Item(channel=item.channel, action="play", title=title, url=url,
                 plot=plot, fanart=fanart, contentSerieName=item.contentSerieName, 
                 infoLabels=item.infoLabels, language=idioma,
                 contentType=item.contentType, tipo=option, tipo1=option1,
                 quality=calidad))

    it2 = servertools.get_servers_itemlist(it2, lambda i: i.title % i.server.capitalize())
    it2.sort(key=lambda it: (it.tipo1, it.language, it.server))
    for item in it2:
        if "###" not in item.url:
            item.url += "###" + id + ";" + type
    itemlist.extend(it1)
    itemlist.extend(it2)

    ## 2 = película
    if type == "2" and item.category != "Cine":
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="greenyellow",
                                 action="add_pelicula_to_library", url=url_targets, thumbnail = item.thumbnail,
                                 contentTitle = item.contentTitle, infoLabels=item.infoLabels, quality=calidad,
                                 ))
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    return itemlist


def play(item):
    if "###" in item.url:
        id = item.url.split("###")[1].split(";")[0]
        type = item.url.split("###")[1].split(";")[1]
        item.url = item.url.split("###")[0]
        post = "target_id=%s&target_type=%s&target_status=1" % (id, type)
        data = agrupa_datos(urlparse.urljoin(host, "/a/status"), post=post)
    devuelve = servertools.findvideosbyserver(item.url, item.server)
    if devuelve:
        item.url = devuelve[0][1]
    else:
        devuelve = servertools.findvideos(item.url, True)
        if devuelve:
            item.url = devuelve[0][1]
            item.server = devuelve[0][2]
    item.thumbnail = item.contentThumbnail
    item.contentTitle = item.contentTitle
    return [item]





def extrae_idiomas(bloqueidiomas, list_language=False):
    logger.info()
    language=[]
    textoidiomas = ''
    orden_idiomas = {'CAST': 0, 'LAT': 1, 'VOSE': 2, 'VOS': 3, 'VO': 4}
    if not list_language:
        patronidiomas = '([a-z0-9]+).png"'
        idiomas = re.compile(patronidiomas, re.DOTALL).findall(bloqueidiomas)
    else:
        idiomas = bloqueidiomas
    #Orden y diccionario
    for w in idiomas:
        i = IDIOMAS.get(w.lower(), w)
        language.insert(orden_idiomas.get(i, 0), i)
    
    for idioma in language:
        textoidiomas += "[%s] " % idioma
    
    return textoidiomas, language

## --------------------------------------------------------------------------------

def set_status(item):
    if item.contentTitle:
        agreg = "Pelicula %s" % item.contentTitle
    else:
        agreg = "Serie %s" % item.contentSerieName
    if "###" in item.url:
        id = item.url.split("###")[1].split(";")[0]
        type = item.url.split("###")[1].split(";")[1]
        # item.url = item.url.split("###")[0]
    if "Abandonar" in item.title:
        title = "[COLOR darkgrey][B]Abandonando %s[/B][/COLOR]"
        path = "/a/status"
        post = "target_id=" + id + "&target_type=" + type + "&target_status=0"
    elif "Seguir" in item.title:
        title = "[COLOR orange][B]Siguiendo %s[/B][/COLOR]"
        path = "/a/status"
        post = "target_id=" + id + "&target_type=" + type + "&target_status=3"
    elif "Agregar a Favoritos" in item.title:
        title = "[COLOR orange][B]%s agregada a Favoritos[/B][/COLOR]"
        path = "/a/favorite"
        post = "like_id=" + id + "&like_type=" + type + "&like_comment=&vote=1"
    elif "Quitar de Favoritos" in item.title:
        title = "[COLOR darkgrey][B]%s eliminada de Favoritos[/B][/COLOR]"
        path = "/a/favorite"
        post = "like_id=" + id + "&like_type=" + type + "&like_comment=&vote=-1"
    data = agrupa_datos(urlparse.urljoin(host, path), post=post)
    title = title % item.contentTitle
    platformtools.dialog_ok(item.contentTitle, title)
    
    return

def check_status():
    status = ""
    if account:
        try:
            status = agrupa_datos(urlparse.urljoin(host, '/a/status/all'), json=True)
        except:
            pass
            
    return status

def get_status(status, type, id):
    if not status:
        return ""
    if type == 'shows':
        state = {'0': '', '1': 'Finalizada', '2': 'Pendiente', '3': 'Siguiendo'}
    else:
        state = {'0': '', '1': 'Visto', '2': 'Pendiente'}
    str = "";
    str1 = "";
    str2 = ""
    try:
        if id in status['favorites'][type]:
            str1 = "[COLOR orange](Favorito)[/COLOR]"
    except:
        str1 = ""
    try:
        if id in status['status'][type]:
            str2 = state[status['status'][type][id]]
            if str2 != "": str2 = "[COLOR blue](" + state[status['status'][type][id]] + ")[/COLOR]"
    except:
        str2 = ""
    if str1 != "" or str2 != "":
        str = ' '+ str1 + str2
    return str

def get_page(item):
    from platformcode import platformtools
    heading = 'Introduzca nº de la Página'
    page_num = platformtools.dialog_numeric(0, heading, default="")
    item.url = re.sub(r'\d+$', page_num, item.url)
    if page_num:
        return fichas(item)
