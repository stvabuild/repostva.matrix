# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# httptools
# --------------------------------------------------------------------------------

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
    import urllib.parse as urllib
    import http.cookiejar as cookielib
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido
    import urlparse
    import cookielib

import inspect
import os
import time
import requests
import json

from core.jsontools import to_utf8
from platformcode import config, logger
from platformcode.logger import WebErrorException
from threading import Lock
from collections import OrderedDict

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# Dominios que necesitan Cloudscraper. AÑADIR dominios de canales sólo si es necesario

global CF_LIST
CF_LIST = list()
CF_LIST_PATH = os.path.join(config.get_runtime_path(), "resources", "CF_Domains.txt")

if os.path.exists(CF_LIST_PATH):
    with open(CF_LIST_PATH, "rb") as CF_File:
       CF_LIST = config.decode_var(CF_File.read().splitlines())

## Obtiene la versión del addon
__version = config.get_addon_version()

cookies_lock = Lock()

cj = cookielib.MozillaCookieJar()
ficherocookies = os.path.join(config.get_data_path(), "cookies.dat")

# Headers por defecto, si no se especifica nada
default_headers = OrderedDict()
# default_headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) Chrome/79.0.3945.117"

ver = config.get_setting("chrome_ua_version")
ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/%s Safari/537.36" % ver

default_headers["User-Agent"] = ua
#default_headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
default_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
default_headers["Accept-Language"] = "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3"
default_headers["Accept-Charset"] = "UTF-8"
default_headers["Accept-Encoding"] = "gzip"

# Tiempo máximo de espera para downloadpage, si no se especifica nada
HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = config.get_setting('httptools_timeout', default=15)
if HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT == 0: HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = None
    
# Uso aleatorio de User-Agents, si no se especifica nada
HTTPTOOLS_DEFAULT_RANDOM_HEADERS = False

def get_user_agent():
    # Devuelve el user agent global para ser utilizado cuando es necesario para la url.
    return default_headers["User-Agent"]


def get_cookie(url, name, follow_redirects=False):
    if follow_redirects:
        try:
            headers = requests.head(url, headers=default_headers).headers
            url = headers['location']
        except Exception:
            pass
        
    domain = urlparse.urlparse(url).netloc
    split_lst = domain.split(".")

    if len(split_lst) > 2:
        domain = domain.replace(split_lst[0], "")
    
    for cookie in cj:
        if cookie.name == name and domain in cookie.domain:
            return cookie.value
    return False


def get_url_headers(url, forced=False, dom=False):
    from . import scrapertools

    domain = urlparse.urlparse(url)[1]
    sub_dom = scrapertools.find_single_match(domain, '\.(.*?\.\w+)')
    if sub_dom and not 'google' in url:
        domain = sub_dom
    if dom:
        domain = dom
    domain_cookies = cj._cookies.get("." + domain, {}).get("/", {})
    domain_cookies.update(cj._cookies.get("www." + domain, {}).get("/", {}))

    if ("|" in url or not "cf_clearance" in domain_cookies) and not forced:
        return url

    headers = dict()
    cf_ua = config.get_setting('cf_assistant_ua', None)
    if cf_ua and cf_ua != 'Default':
        default_headers["User-Agent"] = cf_ua
    headers["User-Agent"] = default_headers["User-Agent"]
    headers["Cookie"] = "; ".join(["%s=%s" % (c.name, c.value) for c in list(domain_cookies.values())])

    return url + "|" + "&".join(["%s=%s" % (h, urllib.quote(headers[h])) for h in headers])


def set_cookies(dict_cookie, clear=True, alfa_s=False):
    """
    Guarda una cookie especifica en cookies.dat
    @param dict_cookie: diccionario de  donde se obtienen los parametros de la cookie
        El dict debe contener:
        name: nombre de la cookie
        value: su valor/contenido
        domain: dominio al que apunta la cookie
        opcional:
        expires: tiempo de vida en segundos, si no se usa agregara 1 dia (86400s)
    @type dict_cookie: dict

    @param clear: True = borra las cookies del dominio, antes de agregar la nueva (necesario para cloudproxy, cp)
                  False = desactivado por defecto, solo actualiza la cookie
    @type clear: bool
    """
    
    #Se le dara a la cookie un dia de vida por defecto
    expires_plus = dict_cookie.get('expires', 86400)
    ts = int(time.time())
    expires = ts + expires_plus

    name = dict_cookie.get('name', '')
    value = dict_cookie.get('value', '')
    domain = dict_cookie.get('domain', '')

    #Borramos las cookies ya existentes en dicho dominio (cp)
    if clear:
        try:
            cj.clear(domain)
        except Exception:
            pass

    ck = cookielib.Cookie(version=0, name=name, value=value, port=None, 
                    port_specified=False, domain=domain, 
                    domain_specified=False, domain_initial_dot=False,
                    path='/', path_specified=True, secure=False, 
                    expires=expires, discard=True, comment=None, comment_url=None, 
                    rest={'HttpOnly': None}, rfc2109=False)
    
    cj.set_cookie(ck)
    save_cookies()


def load_cookies(alfa_s=False):
    cookies_lock.acquire()
    if os.path.isfile(ficherocookies):
        if not alfa_s: logger.info("Leyendo fichero cookies")
        try:
            cj.load(ficherocookies, ignore_discard=True)
        except Exception:
            if not alfa_s: logger.info("El fichero de cookies existe pero es ilegible, se borra")
            os.remove(ficherocookies)
    cookies_lock.release()


def save_cookies(alfa_s=False):
    cookies_lock.acquire()
    if not alfa_s: logger.info("Guardando cookies...")
    cj.save(ficherocookies, ignore_discard=True)
    cookies_lock.release()


load_cookies()


def random_useragent():
    """
    Based on code from https://github.com/theriley106/RandomHeaders
    
    Python Method that generates fake user agents with a locally saved DB (.csv file).

    This is useful for webscraping, and testing programs that identify devices based on the user agent.
    """
    
    import random

    UserAgentPath = os.path.join(config.get_runtime_path(), 'tools', 'UserAgent.csv')
    if os.path.exists(UserAgentPath):
        UserAgentIem = random.choice(list(open(UserAgentPath))).strip()
        if UserAgentIem:
            return UserAgentIem
    
    return default_headers["User-Agent"]


def channel_proxy_list(url, forced_proxy=None):
    import base64
    import ast
    from . import scrapertools

    try:
        proxy_channel_bloqued_str = base64.b64decode(config.get_setting
                ('proxy_channel_bloqued')).decode('utf-8')
        proxy_channel_bloqued = dict()
        proxy_channel_bloqued = ast.literal_eval(proxy_channel_bloqued_str)
    except Exception:
        logger.debug('Proxytools no inicializado correctamente')
        try:
            logger.debug('Bloqued: ' + str(proxy_channel_bloqued_str))
        except Exception:
            pass
        return False

    if not url.endswith('/'):
        url += '/'
    if scrapertools.find_single_match(url, '(?:http.*\:)?\/\/(?:www\.)?([^\?|\/]+)(?:\?|\/)') \
                in proxy_channel_bloqued:
        if forced_proxy and forced_proxy not in ['Total', 'ProxyDirect', 'ProxyCF', 'ProxyWeb']:
            if forced_proxy in proxy_channel_bloqued[scrapertools.find_single_match(url, 
                        '(?:http.*\:)?\/\/(?:www\.)?([^\?|\/]+)(?:\?|\/)')]:
                return True
            else:
                return False
        if forced_proxy:
            return True
        if not 'OFF' in proxy_channel_bloqued[scrapertools.find_single_match(url, 
                '(?:http.*\:)?\/\/(?:www\.)?([^\?|\/]+)(?:\?|\/)')]:
            return True

    return False


def show_infobox(info_dict):
    logger.info()
    from textwrap import wrap

    box_items_kodi = {'r_up_corner': u'\u250c',
                      'l_up_corner': u'\u2510',
                      'center': u'\u2502',
                      'r_center': u'\u251c',
                      'l_center': u'\u2524',
                      'fill': u'\u2500',
                      'r_dn_corner': u'\u2514',
                      'l_dn_corner': u'\u2518',
                      }

    box_items = {'r_up_corner': '+',
                 'l_up_corner': '+',
                 'center': '|',
                 'r_center': '+',
                 'l_center': '+',
                 'fill': '-',
                 'r_dn_corner': '+',
                 'l_dn_corner': '+',
                 }



    width = 60
    version = 'Alfa: %s' % __version
    if config.is_xbmc():
        box = box_items_kodi
    else:
        box = box_items

    logger.info('%s%s%s' % (box['r_up_corner'], box['fill'] * width, box['l_up_corner']))
    logger.info('%s%s%s' % (box['center'], version.center(width), box['center']))
    logger.info('%s%s%s' % (box['r_center'], box['fill'] * width, box['l_center']))

    count = 0
    for key, value in info_dict:
        count += 1
        text = '%s: %s' % (key, value)

        if len(text) > (width - 2):
            text = wrap(text, width)
        else:
            text = text.ljust(width, ' ')
        if isinstance(text, list):
            for line in text:
                if len(line) < width:
                    line = line.ljust(width, ' ')
                logger.info('%s%s%s' % (box['center'], line, box['center']))
        else:
            logger.info('%s%s%s' % (box['center'], text, box['center']))
        if count < len(info_dict):
            logger.info('%s%s%s' % (box['r_center'], box['fill'] * width, box['l_center']))
        else:
            logger.info('%s%s%s' % (box['r_dn_corner'], box['fill'] * width, box['l_dn_corner']))
    return


def check_proxy(url, **opt):
    from . import scrapertools

    proxy_data = dict()
    proxy_data['dict'] = {}
    proxy = opt.get('proxy', True)
    proxy_web = opt.get('proxy_web', False)
    proxy_addr_forced = opt.get('proxy_addr_forced', None)
    forced_proxy = opt.get('forced_proxy', None)
    force_proxy_get = opt.get('force_proxy_get', False)

    try:
        if (proxy or proxy_web) and (forced_proxy or proxy_addr_forced or
                                     channel_proxy_list(url, forced_proxy=forced_proxy)):
            if not PY3: from . import proxytools
            else: from . import proxytools_py3 as proxytools
            proxy_data['addr'], proxy_data['CF_addr'], proxy_data['web_name'], \
            proxy_data['log'] = proxytools.get_proxy_addr(url, forced_proxy_m=forced_proxy, **opt)
            
            if proxy_addr_forced and proxy_data['log']:
                proxy_data['log'] = scrapertools.find_single_match(str(proxy_addr_forced), "{'http.*':\s*'(.*?)'}")

            if proxy and proxy_data['addr']:
                if proxy_addr_forced: proxy_data['addr'] = proxy_addr_forced
                proxy_data['dict'] = proxy_data['addr']
                proxy_data['stat'] = ', Proxy Direct ' + proxy_data['log']
            elif proxy and proxy_data['CF_addr']:
                if proxy_addr_forced: proxy_data['CF_addr'] = proxy_addr_forced
                proxy_data['dict'] = proxy_data['CF_addr']
                proxy_data['stat'] = ', Proxy CF ' + proxy_data['log']
                opt['CF'] = True
            elif proxy and proxy_addr_forced:
                proxy_data['addr'] = proxy_addr_forced
                proxy_data['dict'] = proxy_data['addr']
                proxy_data['stat'] = ', Proxy Direct ' + proxy_data['log']
            elif proxy and not proxy_data['addr'] and not proxy_data['CF_addr'] \
                    and not proxy_addr_forced:
                proxy = False
                if not proxy_data['web_name']:
                    proxy_data['addr'], proxy_data['CF_addr'], proxy_data['web_name'], \
                    proxy_data['log'] = proxytools.get_proxy_addr(url, forced_proxy_m='Total', **opt)
                if proxy_data['web_name']:
                    proxy_web = True
                else:
                    proxy_web = False
                    if proxy_data['addr']:
                        proxy = True
                        proxy_data['dict'] = proxy_data['addr']
                        proxy_data['stat'] = ', Proxy Direct ' + proxy_data['log']

            if proxy_web and proxy_data['web_name']:
                if proxy_data['web_name'] in ['hidester.com']:
                    opt['timeout'] = 40                                         ##### TEMPORAL
                if opt.get('post', None): proxy_data['log'] = '(POST) ' + proxy_data['log']
                url, opt['post'], headers_proxy, proxy_data['web_name'] = \
                    proxytools.set_proxy_web(url, proxy_data, **opt)
                if proxy_data['web_name']:
                    proxy_data['stat'] = ', Proxy Web ' + proxy_data['log']
                    if headers_proxy:
                        opt['headers_proxy'] = dict(headers_proxy)
            if proxy_web and not proxy_data['web_name']:
                proxy_web = False
                proxy_data['addr'], proxy_data['CF_addr'], proxy_data['web_name'], \
                proxy_data['log'] = proxytools.get_proxy_addr(url, forced_proxy_m='Total', **opt)
                if proxy_data['CF_addr']:
                    proxy = True
                    proxy_data['dict'] = proxy_data['CF_addr']
                    proxy_data['stat'] = ', Proxy CF ' + proxy_data['log']
                    opt['CF'] = True
                elif proxy_data['addr']:
                    proxy = True
                    proxy_data['dict'] = proxy_data['addr']
                    proxy_data['stat'] = ', Proxy Direct ' + proxy_data['log']

    except Exception:
        import traceback
        logger.error(traceback.format_exc())
        opt['proxy'] = ''
        opt['proxy_web'] = ''
        proxy_data['stat'] = ''
        proxy_data['addr'] = ''
        proxy_data['CF_addr'] = ''
        proxy_data['dict'] = {}
        proxy_data['web_name'] = ''
        proxy_data['log'] = ''
        url = opt['url_save']
    try:
        if not PY3:
            proxy_data['addr']['https'] = str('https://'+ proxy_data['addr']['https'])
    except Exception:
        pass
    return url, proxy_data, opt


def proxy_post_processing(url, proxy_data, response, opt):
    opt['out_break'] = False
    try:
        if response["code"] in [404, 400]:
            opt['proxy_retries'] = -1
        
        if ', Proxy Web' in proxy_data.get('stat', ''):
            if not PY3: from . import proxytools
            else: from . import proxytools_py3 as proxytools
            
            if not ('application' in response['headers'].get('Content-Type', '') \
                        or 'javascript' in response['headers'].get('Content-Type', '') \
                        or 'image' in response['headers'].get('Content-Type', '')):
                response["data"] = proxytools.restore_after_proxy_web(response["data"],
                                                                  proxy_data['web_name'], opt['url_save'])
            if response["data"] == 'ERROR' or response["code"] == 302:
                if response["code"] == 200: response["code"] = 666
                if not opt.get('post_cookie', False):
                    url_domain = '%s://%s' % (urlparse.urlparse(opt['url_save']).scheme, urlparse.urlparse(opt['url_save']).netloc)
                    forced_proxy_temp = 'ProxyWeb:' + proxy_data['web_name']
                    data_domain = downloadpage(url_domain, alfa_s=True, ignore_response_code=True, \
                                post_cookie=True, forced_proxy=forced_proxy_temp, proxy_retries_counter=0)
                    if data_domain.code == 200:
                        url = opt['url_save']
                        opt['post'] = opt['post_save']
                        opt['forced_proxy'] = forced_proxy_temp
                        return response, url, opt
                if response["data"] == 'ERROR' or response["code"] == 302:
                    proxy_data['stat'] = ', Proxy Direct'
                    opt['forced_proxy'] = 'ProxyDirect'
                    url = opt['url_save']
                    opt['post'] = opt['post_save']
                    response['sucess'] = False
                    response['sucess'] = False
        elif response["code"] == 302:
            response['sucess'] = True

        if proxy_data.get('stat', '') and response['sucess'] == False and \
                opt.get('proxy_retries_counter', 0) <= opt.get('proxy_retries', 1) and \
                opt.get('count_retries_tot', 5) > 1:
            if not PY3: from . import proxytools
            else: from . import proxytools_py3 as proxytools
            
            if ', Proxy Direct' in proxy_data.get('stat', ''):
                proxytools.get_proxy_list_method(proxy_init='ProxyDirect',
                                                 error_skip=proxy_data['addr'], url_test=url, 
                                                 post_test=opt['post_save'])
            elif ', Proxy CF' in proxy_data.get('stat', ''):
                proxytools.get_proxy_list_method(proxy_init='ProxyCF',
                                                 error_skip=proxy_data['CF_addr'])
                url = opt['url_save']
            elif ', Proxy Web' in proxy_data.get('stat', ''):
                if channel_proxy_list(opt['url_save'], forced_proxy=proxy_data['web_name']):
                    opt['forced_proxy'] = 'ProxyCF'
                    url =opt['url_save']
                    opt['post'] = opt['post_save']
                    if opt.get('CF', True):
                        opt['CF'] = True
                    if opt.get('proxy_retries_counter', 0):
                        opt['proxy_retries_counter'] -= 1
                    else:
                        opt['proxy_retries_counter'] = -1
                else:
                    proxytools.get_proxy_list_method(proxy_init='ProxyWeb',
                                                     error_skip=proxy_data['web_name'])
                    url =opt['url_save']
                    opt['post'] = opt['post_save']

        else:
            opt['out_break'] = True
    except Exception:
        import traceback
        logger.error(traceback.format_exc())
        opt['out_break'] = True

    return response, url, opt


def downloadpage(url, **opt):
    """
        Abre una url y retorna los datos obtenidos

        @param url: url que abrir.
        @type url: str
        @param post: Si contiene algun valor este es enviado mediante POST.
        @type post: str (datos json), dict
        @param headers: Headers para la petición, si no contiene nada se usara los headers por defecto.
        @type headers: dict, list
        @param timeout: Timeout para la petición.
        @type timeout: int
        @param follow_redirects: Indica si se han de seguir las redirecciones.
        @type follow_redirects: bool
        @param cookies: Indica si se han de usar las cookies.
        @type cookies: bool
        @param replace_headers: Si True, los headers pasados por el parametro "headers" sustituiran por completo los headers por defecto.
                                Si False, los headers pasados por el parametro "headers" modificaran los headers por defecto.
        @type replace_headers: bool
        @param add_host: Indica si añadir el header Host al principio, como si fuese navegador común.
                         Desactivado por defecto, solo utilizarse con webs problemáticas (da problemas con proxies).
        @type add_host: bool
        @param add_referer: Indica si se ha de añadir el header "Referer" usando el dominio de la url como valor.
        @type add_referer: bool
        @param referer: Si se establece, agrega el header "Referer" usando el parámetro proporcionado como valor.
        @type referer: str
        @param only_headers: Si True, solo se descargarán los headers, omitiendo el contenido de la url.
        @type only_headers: bool
        @param random_headers: Si True, utiliza el método de seleccionar headers aleatorios.
        @type random_headers: bool
        @param ignore_response_code: Si es True, ignora el método para WebErrorException para error como el error 404 en veseriesonline, pero es un data funcional
        @type ignore_response_code: bool
        @param hide_infobox: Si es True, no muestra la ventana de información en el log cuando hay una petición exitosa (no hay un response_code de error).
        @type hide_infobox: bool
        @param soup: Si es True, establece un elemento BeautifulSoup en el atributo soup de HTTPResponse
        @type soup: bool
        @return: Resultado de la petición
        @rtype: HTTPResponse

                Parametro             | Tipo     | Descripción
                ----------------------|----------|-------------------------------------------------------------------------------
                HTTPResponse.sucess:  | bool     | True: Peticion realizada correctamente | False: Error al realizar la petición
                HTTPResponse.code:    | int      | Código de respuesta del servidor o código de error en caso de producirse un error
                HTTPResponse.error:   | str      | Descripción del error en caso de producirse un error
                HTTPResponse.headers: | dict     | Diccionario con los headers de respuesta del servidor
                HTTPResponse.data:    | str      | Respuesta obtenida del servidor
                HTTPResponse.json:    | dict     | Respuesta obtenida del servidor en formato json
                HTTPResponse.soup:    | bs4/None | Objeto BeautifulSoup, si se solicita. None de otra forma
                HTTPResponse.time:    | float    | Tiempo empleado para realizar la petición
    """
    global CF_LIST
    if not opt.get('alfa_s', False):
        logger.info()
    from . import scrapertools

    load_cookies(opt.get('alfa_s', False))

    cf_ua = config.get_setting('cf_assistant_ua', None)
    url = url.strip()

    # Headers por defecto, si no se especifica nada
    req_headers = OrderedDict()
    if opt.get('add_host', False):
        req_headers['Host'] = urlparse.urlparse(url).netloc
    req_headers.update(default_headers.copy())

    if opt.get('add_referer', False):
        req_headers['Referer'] = "/".join(url.split("/")[:3])

    if isinstance(opt.get('referer'), str) and '://' in opt.get('referer'):
        req_headers['Referer'] = opt.get('referer')

    # Headers pasados como parametros
    if opt.get('headers', None) is not None:
        if not opt.get('replace_headers', False):
            req_headers.update(dict(opt['headers']))
        else:
            req_headers = dict(opt('headers'))

    if opt.get('random_headers', False) or HTTPTOOLS_DEFAULT_RANDOM_HEADERS:
        req_headers['User-Agent'] = random_useragent()
    if not PY3:
        url = urllib.quote(url.encode('utf-8'), safe="%/:=&?~#+!$,;'@()*[]")
    else:
        url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    opt['proxy_retries_counter'] = 0
    opt['url_save'] = url
    opt['post_save'] = opt.get('post', None)
    if opt.get('forced_proxy_opt', None) and channel_proxy_list(url):
        if opt['forced_proxy_opt'] in ['ProxyCF', 'ProxyDirect']:
            if '/' not in url:                                                  ### TEMPORAL
                opt['forced_proxy_opt'] = 'ProxyJSON'
            else:
                opt['forced_proxy'] = opt['forced_proxy_opt']
        else:
            opt['forced_proxy'] = opt['forced_proxy_opt']

    while opt['proxy_retries_counter'] <= opt.get('proxy_retries', 1):
        response = {}
        info_dict = []
        payload = dict()
        files = {}
        file_name = ''
        opt['proxy_retries_counter'] += 1

        domain = urlparse.urlparse(url)[1]
        global CS_stat
        if (domain in CF_LIST or opt.get('CF', False)) and opt.get('CF_test', True):    #Está en la lista de CF o viene en la llamada
            from lib import cloudscraper
            session = cloudscraper.create_scraper()                             #El dominio necesita CloudScraper
            session.verify = True
            CS_stat = True
            if cf_ua and cf_ua != 'Default' and get_cookie(url, 'cf_clearance'):
                req_headers['User-Agent'] = cf_ua
        else:
            session = requests.session()
            session.verify = False
            CS_stat = False

        if opt.get('cookies', True):
            session.cookies = cj
        
        if not opt.get('keep_alive', True):
            #session.keep_alive =  opt['keep_alive']
            req_headers['Connection'] = "close"

        # Prepara la url en caso de necesitar proxy, o si se envía "proxy_addr_forced" desde el canal
        url, proxy_data, opt = check_proxy(url, **opt)
        if opt.get('proxy_addr_forced', {}):
            session.proxies = opt['proxy_addr_forced']
        elif proxy_data.get('dict', {}):
            session.proxies = proxy_data['dict']
        if opt.get('headers_proxy', {}):
            req_headers.update(dict(opt['headers_proxy']))
            
        session.headers = req_headers.copy()

        inicio = time.time()
        
        if opt.get('timeout', None) is None and HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT is not None: 
            opt['timeout'] = HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT
        if opt['timeout'] == 0:
            opt['timeout'] = None

        if len(url) > 0:
            try:
                if opt.get('post', None) is not None or opt.get('file', None) is not None or opt.get('files', {}):
                    if opt.get('post', None) is not None:
                        ### Convert string post in dict
                        try:
                            json.loads(opt['post'])
                            payload = opt['post']
                        except Exception:
                            if not isinstance(opt['post'], dict):
                                post = urlparse.parse_qs(opt['post'], keep_blank_values=1)
                                payload = dict()

                                for key, value in list(post.items()):
                                    try:
                                        payload[key] = value[0]
                                    except Exception:
                                        payload[key] = ''
                            else:
                                payload = opt['post']

                    ### Verifies 'file' and 'file_name' options to upload a buffer or a file
                    if opt.get('files', {}):
                        files = opt['files']
                        file_name = opt.get('file_name', 'File Object')
                    elif opt.get('file', None) is not None:
                        if len(opt['file']) < 256 and os.path.isfile(opt['file']):
                            if opt.get('file_name', None) is None:
                                path_file, opt['file_name'] = os.path.split(opt['file'])
                            files = {'file': (opt['file_name'], open(opt['file'], 'rb'))}
                            file_name = opt['file']
                        else:
                            files = {'file': (opt.get('file_name', 'Default'), opt['file'])}
                            file_name = opt.get('file_name', 'Default') + ', Buffer de memoria'

                    info_dict = fill_fields_pre(url, opt, proxy_data, file_name)
                    if opt.get('only_headers', False):
                        ### Makes the request with HEAD method
                        req = session.head(url, allow_redirects=opt.get('follow_redirects', True),
                                          timeout=opt.get('timeout', None), params=opt.get('params', {}))
                    else:
                        ### Makes the request with POST method
                        req = session.post(url, data=payload, allow_redirects=opt.get('follow_redirects', True),
                                          files=files, timeout=opt.get('timeout', None), params=opt.get('params', {}))
                
                elif opt.get('only_headers', False):
                    info_dict = fill_fields_pre(url, opt, proxy_data, file_name)
                    ### Makes the request with HEAD method
                    req = session.head(url, allow_redirects=opt.get('follow_redirects', True),
                                      timeout=opt.get('timeout', None), params=opt.get('params', {}))
                else:
                    info_dict = fill_fields_pre(url, opt, proxy_data, file_name)
                    ### Makes the request with GET method
                    req = session.get(url, allow_redirects=opt.get('follow_redirects', True),
                                      timeout=opt.get('timeout', None), params=opt.get('params', {}))

            except Exception as e:
                if not opt.get('ignore_response_code', False) and not proxy_data.get('stat', ''):
                    req = requests.Response()
                    response['data'] = ''
                    response['sucess'] = False
                    info_dict.append(('Success', 'False'))
                    response['code'] = str(e)
                    info_dict.append(('Response code', str(e)))
                    info_dict.append(('Finalizado en', time.time() - inicio))
                    if not opt.get('alfa_s', False):
                        show_infobox(info_dict)
                        import traceback
                        logger.error(traceback.format_exc(1))
                    return type('HTTPResponse', (), response)
                else:
                    req = requests.Response()
                    req.status_code = str(e)
        
        else:
            response['data'] = ''
            response['sucess'] = False
            response['code'] = ''
            response['soup'] = None
            return type('HTTPResponse', (), response)
        
        response_code = req.status_code

        if req.headers.get('Server', '').startswith('cloudflare') and response_code in [429, 503, 403] \
                        and not opt.get('CF', False) and opt.get('CF_test', True):
            domain = urlparse.urlparse(url)[1]
            if domain not in CF_LIST:
                CF_LIST += [domain]
                opt["CF"] = True
                with open(CF_LIST_PATH, "a") as CF_File:
                    CF_File.write("%s\n" % domain)
                logger.debug("CF retry... for domain: %s" % domain)
                return downloadpage(url, **opt)
        
        if req.headers.get('Server', '') == 'Alfa' and response_code in [429, 503, 403] \
                        and not opt.get('cf_v2', False) and opt.get('CF_test', True):
            opt["cf_v2"] = True
            logger.debug("CF Assistant retry... for domain: %s" % urlparse.urlparse(url)[1])
            return downloadpage(url, **opt)

        response['data'] = req.content

        try:
            response['encoding'] = str(req.encoding).lower() if req.encoding and req.encoding is not None else None

            if opt.get('encoding') and opt.get('encoding') is not None:
                encoding = opt["encoding"]
            else:
                encoding = response['encoding']

            if not encoding:
                encoding = 'utf-8'

            if PY3 and isinstance(response['data'], bytes) and encoding is not None \
                    and ('text/' in req.headers.get('Content-Type', '') \
                        or 'json' in req.headers.get('Content-Type', '') \
                        or 'xml' in req.headers.get('Content-Type', '')):
                response['data'] = response['data'].decode(encoding)

        except Exception:
            import traceback
            logger.error(traceback.format_exc(1))

        try:
            if PY3 and isinstance(response['data'], bytes) \
                    and not ('application' in req.headers.get('Content-Type', '') \
                    or 'javascript' in req.headers.get('Content-Type', '') \
                    or 'image' in req.headers.get('Content-Type', '')):
                response['data'] = "".join(chr(x) for x in bytes(response['data']))

        except Exception:
            import traceback
            logger.error(traceback.format_exc(1))

        try:
            if 'text/' in req.headers.get('Content-Type', '') \
                        or 'json' in req.headers.get('Content-Type', '') \
                        or 'xml' in req.headers.get('Content-Type', ''):
                response['data'] = response['data'].replace('&Aacute;', 'Á').replace('&Eacute;', 'É')\
                      .replace('&Iacute;', 'Í').replace('&Oacute;', 'Ó').replace('&Uacute;', 'Ú')\
                      .replace('&Uuml;', 'Ü').replace('&iexcl;', '¡').replace('&iquest;', '¿')\
                      .replace('&Ntilde;', 'Ñ').replace('&ntilde;', 'n').replace('&uuml;', 'ü')\
                      .replace('&aacute;', 'á').replace('&eacute;', 'é').replace('&iacute;', 'í')\
                      .replace('&oacute;', 'ó').replace('&uacute;', 'ú').replace('&ordf;', 'ª')\
                      .replace('&ordm;', 'º')

        except Exception:
            import traceback
            logger.error(traceback.format_exc(1))

        response['url'] = req.url

        if not response['data']:
            response['data'] = ''

        response['soup'] = None

        if opt.get("soup", False):
            try:
                from bs4 import BeautifulSoup
                response["soup"] = BeautifulSoup(req.content, "html5lib", from_encoding=opt.get('encoding', response['encoding']))

            except Exception:
                import traceback
                logger.error("Error creando sopa")
                logger.error(traceback.format_exc())

        try:
            if 'bittorrent' not in req.headers.get('Content-Type', '') \
                        and 'octet-stream' not in req.headers.get('Content-Type', '') \
                        and 'zip' not in req.headers.get('Content-Type', '') \
                        and opt.get('json_to_utf8', True):
                response['json'] = to_utf8(req.json())

            else:
                response['json'] = dict()

        except Exception:
            response['json'] = dict()
        response['code'] = response_code
        response['headers'] = req.headers
        response['cookies'] = req.cookies

        if response['code'] == 200:
            response['sucess'] = True

        else:
            response['sucess'] = False

        if opt.get('cookies', True):
            save_cookies(alfa_s=opt.get('alfa_s', False))

        is_channel = inspect.getmodule(inspect.currentframe().f_back)
        is_channel = scrapertools.find_single_match(str(is_channel), "<module '(channels).*?'")
        if is_channel and isinstance(response_code, int):
            if not opt.get('ignore_response_code', False) and not proxy_data.get('stat', ''):
                if response_code > 399:
                    info_dict, response = fill_fields_post(info_dict, req, response, req_headers, inicio)
                    show_infobox(info_dict)
                    raise WebErrorException(urlparse.urlparse(url)[1])

        info_dict, response = fill_fields_post(info_dict, req, response, req_headers, inicio)
        if not 'api.themoviedb' in url and not 'api.trakt' in url and not opt.get('alfa_s', False) and not opt.get("hide_infobox"):
            show_infobox(info_dict)

        # Si hay error del proxy, refresca la lista y reintenta el numero indicada en proxy_retries
        response, url, opt = proxy_post_processing(url, proxy_data, response, opt)

        # Si proxy ordena salir del loop, se sale
        if opt.get('out_break', False):
            break

    return type('HTTPResponse', (), response)


def fill_fields_pre(url, opt, proxy_data, file_name):
    info_dict = []
    
    try:
        info_dict.append(('Timeout', opt['timeout']))
        info_dict.append(('URL', url))
        info_dict.append(('Dominio', urlparse.urlparse(url)[1]))
        if CS_stat:
            info_dict.append(('Dominio_CF', True))
        if not opt.get('CF_test', True):
            info_dict.append(('CF_test', False))
        if not opt.get('keep_alive', True):
            info_dict.append(('Keep Alive', opt.get('keep_alive', True)))
        if opt.get('cf_v2', False):
            info_dict.append(('CF v2 Assistant', opt.get('cf_v2', False)))
        if opt.get('post', None) is not None or opt.get('files', None):
            info_dict.append(('Peticion', 'POST' + proxy_data.get('stat', '')))
        elif opt.get('only_headers', False):
            info_dict.append(('Peticion', 'HEAD' + proxy_data.get('stat', '')))
        else:
            info_dict.append(('Peticion', 'GET' + proxy_data.get('stat', '')))
        info_dict.append(('Descargar Pagina', not opt.get('only_headers', False)))
        info_dict.append(('BeautifulSoup', opt.get("soup", False)))
        if opt.get('files', {}) and not isinstance(opt.get('files'), (tuple, dict)):
            info_dict.append(('Objeto fichero', opt.get('files', {})))
        elif file_name: 
            info_dict.append(('Fichero para Upload', file_name))
        if opt.get('params', {}): info_dict.append(('Params', opt.get('params', {})))
        info_dict.append(('Usar cookies', opt.get('cookies', True)))
        info_dict.append(('Fichero de cookies', ficherocookies))

    except Exception:
        import traceback
        logger.error(traceback.format_exc(1))
    
    return info_dict
    
    
def fill_fields_post(info_dict, req, response, req_headers, inicio):
    try:
        if isinstance(response["data"], str) and \
                        ('Hotlinking directly to proxied pages is not permitted.' in response["data"] \
                        or '<h3>Something is wrong</h3>' in response["data"]):
            response["code"] = 666
        
        info_dict.append(('Cookies', req.cookies))
        info_dict.append(('Data Encoding', req.encoding))
        info_dict.append(('Response code', response['code']))

        if response['code'] == 200:
            info_dict.append(('Success', 'True'))
            response['sucess'] = True
        else:
            info_dict.append(('Success', 'False'))
            response['sucess'] = False

        info_dict.append(('Response data length', len(response['data'])))

        info_dict.append(('Request Headers', ''))
        for header in req_headers:
            info_dict.append(('- %s' % header, req_headers[header]))

        info_dict.append(('Response Headers', ''))
        for header in response['headers']:
            info_dict.append(('- %s' % header, response['headers'][header]))
        info_dict.append(('Finalizado en', time.time() - inicio))
    except Exception:
        import traceback
        logger.error(traceback.format_exc(1))
    
    return info_dict, response