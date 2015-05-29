import logging
import json
import sys
import os
import imp

if (hasattr(sys, "frozen") or  # new py2exe
        hasattr(sys, "importers") or  # old py2exe
        imp.is_frozen("__main__")):
    ROOTDIR = os.path.dirname(sys.executable)
else:
    ROOTDIR = os.path.dirname(sys.argv[0])

try:
    __file__  # note py2exe can have __file__. refer into the `.exe` file
except NameError:
    LIBDIR = ROOTDIR
else:
    LIBDIR = os.path.normpath(os.path.join(__file__, '..', '..', '..'))

sys.path.insert(0, LIBDIR)
from lib.tool.minsix import open
sys.path.pop(0)

logger = logging.getLogger('tool.translate')


class Translate(object):
    _ins = None

    def __new__(cls):
        if cls._ins is None:
            ins = super(Translate, cls).__new__(cls)
            ins._lang = None
            ins._supported = []
            ins._translate = {}
            trans_path = os.path.join(ROOTDIR, 'src', 'translate')
            logger.debug(trans_path)
            try:
                dirpath, _, filenames = next(os.walk(trans_path))
            except StopIteration as e:
                logger.info('no translation found')
            else:
                for file in filenames:
                    path = os.path.join(dirpath, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        try:
                            info = json.load(f)
                        except ValueError as e:
                            logger.error('%s formatted error: %s', path, e)
                            continue
                        code = info['code']
                        name = info['name']
                        eng_name = info['englishname']
                        translate = info['translate']

                        if code in ins._translate:
                            raise ValueError('%s (%s) translation duplicated' %
                                             (path, code))
                        ins._supported.append({'code': code, 'name': name,
                                               'eng_name': eng_name})
                        ins._translate[code] = translate
                        logger.debug('New translation %s(%s)', code, name)
                else:
                    logger.info('supported translation: %s',
                                list(ins._supported))

            cls._ins = ins
        return cls._ins

    @property
    def lang(self):
        return self._lang

    @lang.setter
    def lang(self, value):
        if value in (None, 'en_US'):
            self._lang = value
            return

        # perfect match
        if value in self._translate:
            self._lang = value
            return
        # fuzzy match
        if '_' in value:
            this_lang = (value, value.split('_')[0])
        else:
            this_lang = (value,)
        for this in this_lang:
            for support in self._translate.keys():
                if support.startswith(this):
                    self._lang = support
                    return
        return

        self._lang = value

    def translate(self, s):
        if self._lang in (None, 'en_US'):
            return s
        return self._translate[self._lang].get(s, s)

    def support(self, lang):
        if lang in self._translate:
            return True
        elif lang == 'en_US':
            return True
        # fuzzy match
        if '_' in lang:
            this_lang = (lang, lang.split('_')[0])
        else:
            this_lang = (lang,)
        for this in this_lang:
            for support in self._translate.keys():
                if support.startswith(this):
                    return True
        return False

    def supported(self):
        return self._supported
