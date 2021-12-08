# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# cloudscaper+alfa_assistant
# ------------------------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse
    from lib import alfaresolver_py3 as alfaresolver
else:
    import urlparse
    from lib import alfaresolver

import traceback
import xbmc
import time

from .exceptions import CloudflareChallengeError

from lib import alfa_assistant
from core import httptools, scrapertools, filetools, jsontools
from core.item import Item
from platformcode import logger, config, help_window

PATH_BL = filetools.join(config.get_runtime_path(), 'resources', 'cf_assistant_bl.json')


def get_cl(resp, timeout=20, debug=False, extraPostDelay=15, retry=False, blacklist=True, retryIfTimeout=True, **kwargs):
    blacklist_clear = True
    if 'hideproxy' in resp.url or 'webproxy' in resp.url or kwargs.get('proxies'):
        blacklist_clear = False
        blacklist = False
    
    if timeout < 15: timeout = 20
    if timeout + extraPostDelay > 35: timeout = 20

    domain_full = urlparse.urlparse(resp.url).netloc
    domain = domain_full
    if blacklist and not retry: 
        blacklist_clear = check_blacklist(domain_full)
    
    if blacklist_clear:
        host = config.get_system_platform()[:1]
        
        freequent_data = [domain, 'CF2,0.0.0,0,%s0,NoApp' % host]
        
        check_assistant = alfa_assistant.open_alfa_assistant(getWebViewInfo=True, retry=retry)
        if not isinstance(check_assistant, dict) and retry:
            alfa_assistant.close_alfa_assistant()
            time.sleep(2)
            check_assistant = alfa_assistant.open_alfa_assistant(getWebViewInfo=True, retry=True)
            if not check_assistant:
                time.sleep(10)
                check_assistant = alfa_assistant.get_generic_call('getWebViewInfo', timeout=2, alfa_s=True)
            
        if check_assistant and isinstance(check_assistant, dict):

            if check_assistant.get('assistantLatestVersion') and check_assistant.get('assistantVersion'):
                installed_version = check_assistant['assistantVersion'].split('.')
                available_version = check_assistant['assistantLatestVersion'].split('.')
                newer = False
                for i, ver in enumerate(available_version):
                    if int(ver) > int(installed_version[i]):
                        newer = True
                        break
                    if int(ver) < int(installed_version[i]):
                        break
                if newer:
                    help_window.show_info('cf_2_02', wait=False)

            ua = get_ua(check_assistant)
            
            try:
                vers = int(scrapertools.find_single_match(ua, r"Android\s*(\d+)"))
            except:
                vers = 0

            wvbVersion = check_assistant.get('wvbVersion', '0.0.0').split('.')[0]
            if len(wvbVersion) > 3: wvbVersion = wvbVersion[:2]
            freequent_data[1] = 'CF2,%s,%s,%s%s,' % (check_assistant.get('assistantVersion', '0.0.0'), wvbVersion, host, vers)

            if vers:
                dan = {'User-Agent': ua}
                resp.headers.update(dict(dan))
                ua = None
            else:
                ua = httptools.get_user_agent()

            logger.debug("UserAgent: %s || Android Vrs: %s" % (ua, vers))

            jscode = get_jscode(1, 'KEYCODE_ENTER', 1)

            url_cf = scrapertools.find_single_match(resp.url, '(http.*\:\/\/(?:www\S*.)?\w+\.\w+(?:\.\w+)?)(?:\/)?') + '|cf_clearance'

            data_assistant = alfa_assistant.get_urls_by_page_finished(resp.url, timeout=timeout, getCookies=True, userAgent=ua,
                                                                        disableCache=True, debug=debug, jsCode=jscode,
                                                                        extraPostDelay=extraPostDelay, clearWebCache=True, 
                                                                        removeAllCookies=True, returnWhenCookieNameFound=url_cf,
                                                                        retryIfTimeout=retryIfTimeout
                                                                        )
            logger.debug("data assistant: %s" % data_assistant)

            domain_ = domain
            split_lst = domain.split(".")

            if len(split_lst) > 2:
                domain = domain.replace(split_lst[0], "")
            
            if not domain.startswith('.'):
                domain = "."+domain
            
            get_ua(data_assistant)

            if isinstance(data_assistant, dict) and data_assistant.get("cookies", None):

                logger.debug("Lista cookies: %s" % data_assistant.get("cookies", []))
                for cookie in data_assistant["cookies"]:
                    cookieslist = cookie.get("cookiesList", None)
                    val = scrapertools.find_single_match(cookieslist, 'cf_clearance=([A-z0-9_\-\.]+)')
                    #val = scrapertools.find_single_match(cookieslist, 'cf_clearance=([^;]+)')
                    dom = cookie.get("urls", None)
                    logger.debug("dominios: %s" % dom[0])

                    if 'cf_clearance' in cookieslist and val:
                        
                        dict_cookie = {'domain': domain,
                                       'name': 'cf_clearance',
                                       'value': val}
                        if domain_ in dom[0]:
                            httptools.set_cookies(dict_cookie)
                            rin = {'Server': 'Alfa'}

                            resp.headers.update(dict(rin))
                            logger.debug("cf_clearence=%s" % val)
                            
                            if not retry:
                                freequent_data[1] += 'OK'
                            else:
                                freequent_data[1] += 'OK_R'
                            freequency(freequent_data)

                            return resp

                    else:
                        logger.error("No cf_clearance")
                else:
                    freequent_data[1] += 'NO-CFC'
            else:
                freequent_data[1] += 'ERR'
                logger.error("No Cookies o Error en conexión con Alfa Assistant")

            if not retry:
                config.set_setting('cf_assistant_ua', '')
                logger.debug("No se obtuvieron resultados, reintentando...")
                return get_cl(resp, timeout=timeout-5, extraPostDelay=extraPostDelay, \
                            retry=True, blacklist=True, retryIfTimeout=False, **kwargs)
        elif host == 'a':
            help_window.show_info('cf_2_01')
        
        freequency(freequent_data)
        
        if filetools.exists(PATH_BL):
            bl_data = jsontools.load(filetools.read(PATH_BL))
        else:
            bl_data = {}
        bl_data[domain_full] = time.time()
        filetools.write(PATH_BL, jsontools.dump(bl_data))

    msg = 'Detected a Cloudflare version 2 Captcha challenge,\
        This feature is not available in the opensource (free) version.'
    resp.status_code = msg
    
    raise CloudflareChallengeError(msg)


def get_ua(data_assistant):
    
    if not data_assistant or not isinstance(data_assistant, dict):
        return 'Default'
    
    UA = data_assistant.get("userAgent", 'Default')
    
    if UA == httptools.get_user_agent():
        UA = 'Default'

    config.set_setting('cf_assistant_ua', UA)

    return UA


def get_jscode(count, key, n_iframe, timeout=3):
    
    count = str(count)
    focus = str(n_iframe)
    timeout = str(timeout * 1000)

    js = '''((() => {

    const KEYCODE_ENTER = 'KEYCODE_ENTER';
    const KEYCODE_TAB = 'KEYCODE_TAB';

    function sendKeyAfterNTabs(count, key) {
        try {
            for (var i = 0; i <= count; i++) {
                if (i > 0) {
                    alfaAssistantAndroidPI.sendKey(KEYCODE_TAB);
                }
                if (i == count) {
                    alfaAssistantAndroidPI.sendKey(key);
                    break;
                }
            }
        } catch (e) {
            console.error('##Error sending key ' + key, e);
        };
    };

   function setFocusToIframeNumber(nmb) {
    document.querySelectorAll('iframe')[nmb - 1].focus();
   }
    try {

        setFocusToIframeNumber('''+ focus +''');

        sendKeyAfterNTabs('''+ count +''', '''+ key +''');

        setTimeout(function() { 
            window.location.href = alfaAssistantAndroidPI.getMainURL();
            }, '''+ timeout +''');
    }
    catch(e){
            console.error('##Error focus ', e);
        };
}))();
'''
    return js


def freequency(freequent_data):
    import threading

    try:
        threading.Thread(target=alfaresolver.frequency_count, args=(Item(), [], freequent_data)).start()
        ret = True
    except:
        logger.error(traceback.format_exc())


def check_blacklist(domain):
    res = True
    if not filetools.exists(PATH_BL):
        return res
    
    try:
        bl_data = jsontools.load(filetools.read(PATH_BL))
        bl_data_clean = bl_data.copy()
        expiration = config.get_setting('cf_assistant_bl_expiration', default=30) * 60
        if not expiration:
            config.set_setting('cf_assistant_bl_expiration', 30)
            expiration = 30 * 60
        time_today = time.time()
        
        if bl_data:
            for domain_reg, time_rec in list(bl_data_clean.items()):
                if time_today > time_rec + expiration:
                    del bl_data[domain_reg]
            filetools.write(PATH_BL, jsontools.dump(bl_data))
            for domain_reg, time_rec in list(bl_data.items()):
                if domain in domain_reg:
                    res = False
                    break
            else:
                res = True
    except:
        logger.error(traceback.format_exc())
        filetools.remove(PATH_BL)
        res = True

    return res
