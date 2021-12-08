# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Updater (kodi)
# --------------------------------------------------------------------------------
import sys

PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import os
import time
import threading
import traceback
import base64
import xbmc

from platformcode import config
from platformcode import logger
from platformcode.platformtools import dialog_notification
from core import httptools
from core import jsontools
from core import downloadtools
from core import scrapertools
from core import ziptools


def check_addon_init():
    logger.info()

    # Subtarea de monitor.  Se activa cada X horas para comprobar si hay FIXES al addon
    def check_addon_monitor():
        logger.info()

        # Obtiene el íntervalo entre actualizaciones y si se quieren mensajes
        try:
            timer = int(config.get_setting('addon_update_timer',
                                           default=12))  # Intervalo entre actualizaciones, en Ajustes de Alfa
            if timer <= 0:
                try:
                    user_type = base64.b64decode(config.get_setting('proxy_dev')).decode('utf-8')
                except:
                    user_type = 'user'
                if user_type == 'user':
                    config.set_setting('addon_update_timer', 12)  # Si es usuario se fuerza a 12 horas
                    timer = 12
                else:
                    return  # 0.  No se quieren actualizaciones
            verbose = config.get_setting('addon_update_message', default=False)
        except:
            logger.error(traceback.format_exc())
            timer = 12  # Por defecto cada 12 horas
            verbose = False  # Por defecto, sin mensajes
        timer = timer * 3600  # Lo pasamos a segundos

        if config.get_platform(True)['num_version'] >= 14:  # Si es Kodi, lanzamos el monitor
            monitor = xbmc.Monitor()
        else:  # Lanzamos solo una actualización y salimos
            check_addon_updates(verbose)  # Lanza la actualización
            return

        while not monitor.abortRequested():  # Loop infinito hasta cancelar Kodi

            check_addon_updates(verbose)  # Lanza la actualización

            if monitor.waitForAbort(timer):  # Espera el tiempo programado o hasta que cancele Kodi
                break  # Cancelación de Kodi, salimos

        check_update_to_others(verbose=False,
                               app=False)  # Actualizamos otros add-ons antes de irnos, para el siguiente inicio
        # Borra el .zip de instalación de Alfa de la carpeta Packages, por si está corrupto, y que así se pueda descargar de nuevo
        version = 'plugin.video.alfa-%s.zip' % config.get_addon_version(with_fix=False, from_xml=True)
        packages_path = os.path.join(config.translatePath('special://home'), 'addons', 'packages', version)
        if os.path.exists(packages_path):
            os.remove(packages_path)
        return

    # Lanzamos en Servicio de actualización de FIXES
    try:
        threading.Thread(target=check_addon_monitor).start()  # Creamos un Thread independiente, hasta el fin de Kodi
        time.sleep(5)  # Dejamos terminar la primera verificación...
    except:  # Si hay problemas de threading, se llama una sola vez
        try:
            timer = int(config.get_setting('addon_update_timer',
                                           default=12))  # Intervalo entre actualizaciones, en Ajustes de Alfa
            if timer <= 0:
                try:
                    user_type = base64.b64decode(config.get_setting('proxy_dev')).decode('utf-8')
                except:
                    user_type = 'user'
                if user_type == 'user':
                    config.set_setting('addon_update_timer', 12)  # Si es usuario se fuerza a 12 horas
                    timer = 12
                else:
                    return  # 0.  No se quieren actualizaciones
            verbose = config.get_setting('addon_update_message', default=False)
        except:
            verbose = False  # Por defecto, sin mensajes
            pass
        check_addon_updates(verbose)  # Lanza la actualización, en Ajustes de Alfa
        time.sleep(5)  # Dejamos terminar la primera verificación...

    return


def check_addon_updates(verbose=False):
    logger.info()

    # Forzamos la actualización de los repos para facilitar la actualización del addon Alfa
    xbmc.executebuiltin('UpdateAddonRepos')

    ADDON_UPDATES_JSON = 'https://extra.alfa-addon.com/addon_updates/updates.json'
    ADDON_UPDATES_ZIP = 'https://extra.alfa-addon.com/addon_updates/updates.zip'

    try:
        get_ua_list()
    except:
        pass

    try:
        last_fix_json = os.path.join(config.get_runtime_path(),
                                     'last_fix.json')  # información de la versión fixeada del usuario
        # Se guarda en get_runtime_path en lugar de get_data_path para que se elimine al cambiar de versión

        try:
            localfilename = os.path.join(config.get_data_path(), 'temp_updates.zip')
            if os.path.exists(localfilename): os.remove(localfilename)
        except:
            pass

        # Descargar json con las posibles actualizaciones
        # -----------------------------------------------
        resp = httptools.downloadpage(ADDON_UPDATES_JSON, timeout=5, ignore_response_code=True)
        if not resp.sucess and resp.code != 404:
            logger.info('ERROR en la descarga de actualizaciones: %s' % resp.code)
            if verbose:
                dialog_notification('Alfa: error en la actualización', 'Hay un error al descargar la actualización')
            return False
        if not resp.data:
            logger.info('No se encuentran actualizaciones del addon')
            if verbose:
                dialog_notification('Alfa ya está actualizado', 'No hay ninguna actualización urgente')
            check_update_to_others(verbose=verbose)  # Comprueba las actualuzaciones de otros productos
            return False

        data = jsontools.load(resp.data)
        if 'addon_version' not in data or 'fix_version' not in data:
            logger.info('No hay actualizaciones del addon')
            if verbose:
                dialog_notification('Alfa ya está actualizado', 'No hay ninguna actualización urgente')
            check_update_to_others(verbose=verbose)  # Comprueba las actualuzaciones de otros productos
            return False

        # Comprobar versión que tiene instalada el usuario con versión de la actualización
        # --------------------------------------------------------------------------------
        current_version = config.get_addon_version(with_fix=False, from_xml=True)
        if current_version != data['addon_version']:
            logger.info('No hay actualizaciones para la versión %s del addon' % current_version)
            if verbose:
                dialog_notification('Alfa ya está actualizado', 'No hay ninguna actualización urgente')
            check_update_to_others(verbose=verbose)  # Comprueba las actualuzaciones de otros productos
            return False

        if os.path.exists(last_fix_json):
            try:
                lastfix = {}
                lastfix = jsontools.load(open(last_fix_json, "r").read())
                if lastfix['addon_version'] == data['addon_version'] and lastfix['fix_version'] == data['fix_version']:
                    logger.info('Ya está actualizado con los últimos cambios. Versión %s.fix%d' % (
                    data['addon_version'], data['fix_version']))
                    if verbose:
                        dialog_notification('Alfa ya está actualizado',
                                            'Versión %s.fix%d' % (data['addon_version'], data['fix_version']))
                    check_update_to_others(verbose=verbose)  # Comprueba las actualuzaciones de otros productos
                    return False
            except:
                if lastfix:
                    logger.error('last_fix.json: ERROR en: ' + str(lastfix))
                else:
                    logger.error('last_fix.json: ERROR desconocido')
                lastfix = {}

        # Descargar zip con las actualizaciones
        # -------------------------------------

        if downloadtools.downloadfile(ADDON_UPDATES_ZIP, localfilename, silent=True) < 0:
            raise

        # Descomprimir zip dentro del addon
        # ---------------------------------
        try:
            unzipper = ziptools.ziptools()
            unzipper.extract(localfilename, config.get_runtime_path())
        except:
            xbmc.executebuiltin('Extract("%s", "%s")' % (localfilename, config.get_runtime_path()))
            time.sleep(1)

        # Borrar el zip descargado
        # ------------------------
        try:
            os.remove(localfilename)
        except:
            pass

        # Si es PY3 se actualizan los módulos marshal
        # Se reinicia Proxytools
        try:
            if PY3:
                from platformcode.custom_code import marshal_check
                marshal_check()
            if not PY3:
                from core.proxytools import get_proxy_list
            else:
                from core.proxytools_py3 import get_proxy_list
            get_proxy_list(monitor_start=False)
        except:
            logger.error('Error Marshalizando e iniciando Proxytools')
            logger.error(traceback.format_exc())

        # Guardar información de la versión fixeada
        # -----------------------------------------
        try:
            show_update_info(data)
        except:
            pass
        last_id = 0
        if isinstance(data["files"], list):
            last_id = len(data["files"])
        elif isinstance(data["files"], dict):
            for k in data["files"].keys():
                if int(k) > last_id:
                    last_id = int(k)

        if 'files' in data: data.pop('files', None)
        data["last_id"] = last_id
        open(last_fix_json, "w").write(jsontools.dump(data))
        # Actualiza la versión del addon en las cabeceras
        try:
            httptools.__version = '%s.fix%d' % (data['addon_version'], data['fix_version'])
        except:
            pass

        logger.info('Addon actualizado correctamente a %s.fix%d' % (data['addon_version'], data['fix_version']))

        if verbose and not config.get_setting("show_fixes", default=True):
            dialog_notification('Alfa actualizado a', 'Versión %s.fix%d' % (data['addon_version'], data['fix_version']))

        check_update_to_others(verbose=verbose)  # Comprueba las actualuzaciones de otros productos
        return True

    except:
        logger.error('Error al comprobar actualizaciones del addon!')
        logger.error(traceback.format_exc())
        if verbose:
            dialog_notification('Alfa actualizaciones', 'Error al comprobar actualizaciones')
        check_update_to_others(verbose=verbose)  # Comprueba las actualuzaciones de otros productos
        return False


def check_update_to_others(verbose=False, app=True):
    logger.info()

    try:
        list_folder = os.listdir(os.path.join(config.get_runtime_path(), 'tools'))
        for folder in list_folder:
            in_folder = os.path.join(config.get_runtime_path(), 'tools', folder)
            if not os.path.isdir(in_folder):
                continue

            out_folder = os.path.join(config.translatePath('special://home/addons'), folder)
            if os.path.exists(out_folder):
                copytree(in_folder, out_folder)

                logger.info('%s updated' % folder)
    except:
        logger.error('Error al actualizar OTROS paquetes')
        logger.error(traceback.format_exc())

    if app:
        try:
            from lib import alfa_assistant
            res, addonid = alfa_assistant.update_alfa_assistant(verbose=verbose)
        except:
            logger.error("Alfa Assistant.  Error en actualización")
            logger.error(traceback.format_exc())


def copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree using copy2().

    *** Obtained from Kody Python 2.7 Shutil ***
    *** Ignores error if dst-dir exists ***

    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    length = 16 * 1024
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.exists(dst):
        os.makedirs(dst)

    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)

        if symlinks and os.path.islink(srcname):
            linkto = os.readlink(srcname)
            os.symlink(linkto, dstname)
        elif os.path.isdir(srcname):
            copytree(srcname, dstname, symlinks, ignore)
        else:
            # Will raise a SpecialFileError for unsupported file types
            with open(srcname, 'rb') as fsrc:
                with open(dstname, 'wb') as fdst:
                    while 1:
                        buf = fsrc.read(length)
                        if not buf:
                            break
                        fdst.write(buf)


def get_ua_list():
    logger.info()
    url = "http://omahaproxy.appspot.com/all?csv=1"
    current_ver = config.get_setting("chrome_ua_version", default="").split(".")
    data = httptools.downloadpage(url, alfa_s=True, ignore_response_code=True).data
    new_ua_ver = scrapertools.find_single_match(data, "win64,stable,([^,]+),")
    if not new_ua_ver:
        return

    if not current_ver:
        config.set_setting("chrome_ua_version", new_ua_ver)
    else:
        for pos, val in enumerate(new_ua_ver.split('.')):
            if int(val) > int(current_ver[pos]):
                config.set_setting("chrome_ua_version", new_ua_ver)
                break


def show_update_info(new_fix_json):
    import re
    import os
    from core import jsontools
    from core import channeltools
    from platformcode import help_window
    from platformcode import platformtools

    fixed = list()
    old_fix = os.path.join(config.get_runtime_path(), 'last_fix.json')

    if isinstance(new_fix_json, dict):
        if not os.path.exists(old_fix):
            for k, v in new_fix_json["files"].items():
                if "channels" in v:
                    v = re.sub(r"\.py|\.json", "", v[1])
                    channel_parameters = channeltools.get_channel_parameters(v)
                    if not channel_parameters["channel"] or channel_parameters["adult"]:
                        continue
                    fixed.append("- %s\n" % v.title())
        else:
            with open(old_fix, "r") as f:
                old_fix_json = jsontools.load(f.read())

            last_id = old_fix_json.get("last_id", 0)

            for k, v in new_fix_json["files"].items():
                if int(k) > last_id and "channels" in v:
                    v = re.sub(r"\.py|\.json", "", v[1])
                    channel_parameters = channeltools.get_channel_parameters(v)
                    if not channel_parameters["channel"] or channel_parameters["adult"]:
                        continue
                    fixed.append("- %s\n" % v.title())
    elif isinstance(new_fix_json, list):
        if not os.path.exists(old_fix):
            for fix in new_fix_json["files"]:
                if "channels" in fix:
                    fix = re.sub(r"\.py|\.json", "", fix[1])
                    channel_parameters = channeltools.get_channel_parameters(fix)
                    if not channel_parameters["channel"] or channel_parameters["adult"]:
                        continue
                    fixed.append("- %s\n" % fix.title())
        else:
            with open(old_fix, "r") as f:
                old_fix_json = jsontools.load(f.read())

            last_id = old_fix_json.get("last_id", 0)
            if len(new_fix_json["files"]) > last_id:
                for fix in new_fix_json["files"][last_id + 1:]:
                    if "channels" in fix:
                        fix = re.sub(r"\.py|\.json", "", fix[1])
                        channel_parameters = channeltools.get_channel_parameters(fix)
                        if not channel_parameters["channel"] or channel_parameters["adult"]:
                            continue
                        fixed.append("- %s\n" % fix.title())

    if fixed:
        fix_number = "%s - FIX %s" % (new_fix_json["addon_version"], new_fix_json["fix_version"])
        fixed_list = "".join(set(fixed))
        text = "[B]Se han aplicado correcciones a los siguientes canales:[/B] \n\n%s\n\n" % fixed_list
        text += "[I]Si no deseas ver esta ventana desactívala desde:[/I]\nConfiguración > Preferencias > General > Mostrar informe de correcciones"
        if not platformtools.is_playing() and config.get_setting("show_fixes", default=True):
            help_window.show_info(0, wait=False, title="Alfa - Correcciones (%s)" % fix_number, text=text)
