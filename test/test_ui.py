# This file is part of beets.
# Copyright 2010, Adrian Sampson.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""Tests for the command-line interface.
"""

import unittest
import sys
import os
import textwrap
from StringIO import StringIO
import _common
sys.path.append('..')
from beets import library
from beets import ui
from beets.ui import commands
from beets import autotag
import test_db

class ListTest(unittest.TestCase):
    def setUp(self):
        self.io = _common.DummyIO()
        self.io.install()

        self.lib = library.Library(':memory:')
        i = test_db.item()
        self.lib.add(i)
        self.lib.add_album([i])

    def tearDown(self):
        self.io.restore()
        
    def test_list_outputs_item(self):
        commands.list_items(self.lib, '', False)
        out = self.io.getoutput()
        self.assertTrue(u'the title' in out)

    def test_list_album_outputs_something(self):
        commands.list_items(self.lib, '', True)
        out = self.io.getoutput()
        self.assertGreater(len(out), 0)
    
    def test_list_album_omits_title(self):
        commands.list_items(self.lib, '', True)
        out = self.io.getoutput()
        self.assertTrue(u'the title' not in out)

    def test_list_uses_track_artist(self):
        commands.list_items(self.lib, '', False)
        out = self.io.getoutput()
        self.assertTrue(u'the artist' in out)
        self.assertTrue(u'the album artist' not in out)
    
    def test_list_album_uses_album_artist(self):
        commands.list_items(self.lib, '', True)
        out = self.io.getoutput()
        self.assertTrue(u'the artist' not in out)
        self.assertTrue(u'the album artist' in out)

class PrintTest(unittest.TestCase):
    def setUp(self):
        self.io = _common.DummyIO()
        self.io.install()
    def tearDown(self):
        self.io.restore()
    
    def test_print_without_locale(self):
        lang = os.environ.get('LANG')
        if lang:
            del os.environ['LANG']

        try:
            ui.print_(u'something')
        except TypeError:
            self.fail('TypeError during print')
        finally:
            if lang:
                os.environ['LANG'] = lang

    def test_print_with_invalid_locale(self):
        old_lang = os.environ.get('LANG')
        os.environ['LANG'] = ''
        old_ctype = os.environ.get('LC_CTYPE')
        os.environ['LC_CTYPE'] = 'UTF-8'

        try:
            ui.print_(u'something')
        except ValueError:
            self.fail('ValueError during print')
        finally:
            if old_lang:
                os.environ['LANG'] = old_lang
            else:
                del os.environ['LANG']
            if old_ctype:
                os.environ['LC_CTYPE'] = old_ctype
            else:
                del os.environ['LC_CTYPE']

class AutotagTest(unittest.TestCase):
    def setUp(self):
        self.io = _common.DummyIO()
        self.io.install()
    def tearDown(self):
        self.io.restore()

    def _no_candidates_test(self, result):
        res = commands.choose_match(
            'path',
            [test_db.item()], # items
            'artist',
            'album',
            [], # candidates
            autotag.RECOMMEND_NONE
        )
        self.assertEqual(res, result)
        self.assertTrue('No match' in self.io.getoutput())

    def test_choose_match_with_no_candidates_skip(self):
        self.io.addinput('s')
        self._no_candidates_test(commands.CHOICE_SKIP)

    def test_choose_match_with_no_candidates_asis(self):
        self.io.addinput('u')
        self._no_candidates_test(commands.CHOICE_ASIS)

class InputTest(unittest.TestCase):
    def setUp(self):
        self.io = _common.DummyIO()
        self.io.install()
    def tearDown(self):
        self.io.restore()

    def test_manual_search_gets_unicode(self):
        self.io.addinput('\xc3\x82me')
        self.io.addinput('\xc3\x82me')
        artist, album = commands.manual_search()
        self.assertEqual(artist, u'\xc2me')
        self.assertEqual(album, u'\xc2me')

class ConfigTest(unittest.TestCase):
    def setUp(self):
        self.test_cmd = ui.Subcommand('test', help='test')
        commands.default_commands.append(self.test_cmd)
    def tearDown(self):
        commands.default_commands.pop()
    def _run_main(self, args, config, func):
        self.test_cmd.func = func
        ui.main(args + ['test'], StringIO(config))

    def test_paths_section_respected(self):
        def func(lib, config, opts, args):
            self.assertEqual(lib.path_formats['x'], 'y')
        self._run_main([], textwrap.dedent("""
            [paths]
            x=y"""), func)

    def test_default_paths_preserved(self):
        def func(lib, config, opts, args):
            self.assertEqual(lib.path_formats['default'],
                             ui.DEFAULT_PATH_FORMATS['default'])
        self._run_main([], textwrap.dedent("""
            [paths]
            x=y"""), func)

    def test_default_paths_overriden_by_legacy_path_format(self):
        def func(lib, config, opts, args):
            self.assertEqual(lib.path_formats['default'], 'x')
            self.assertEqual(len(lib.path_formats), 1)
        self._run_main([], textwrap.dedent("""
            [beets]
            path_format=x"""), func)

    def test_paths_section_overriden_by_cli_switch(self):
        def func(lib, config, opts, args):
            self.assertEqual(lib.path_formats['default'], 'z')
            self.assertEqual(len(lib.path_formats), 1)
        self._run_main(['-p', 'z'], textwrap.dedent("""
            [paths]
            x=y"""), func)
def suite():
    return unittest.TestLoader().loadTestsFromName(__name__)

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
