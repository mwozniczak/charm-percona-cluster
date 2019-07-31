import io
import os
import logging
import unittest

import yaml

from contextlib import contextmanager
from mock import patch, MagicMock


def load_config():
    '''
    Walk backwords from __file__ looking for config.yaml, load and return the
    'options' section'
    '''
    config = None
    f = __file__
    while config is None:
        d = os.path.dirname(f)
        if os.path.isfile(os.path.join(d, 'config.yaml')):
            config = os.path.join(d, 'config.yaml')
            break
        f = d

    if not config:
        logging.error('Could not find config.yaml in any parent directory '
                      'of %s. ' % __file__)
        raise Exception

    return yaml.safe_load(open(config, encoding="UTF-8").read())['options']


def get_default_config():
    '''
    Load default charm config from config.yaml return as a dict.
    If no default is set in config.yaml, its value is None.
    '''
    default_config = {}
    config = load_config()
    for k, v in config.items():
        if 'default' in v:
            default_config[k] = v['default']
        else:
            default_config[k] = None
    return default_config


class CharmTestCase(unittest.TestCase):

    def setUp(self, obj, patches):
        super(CharmTestCase, self).setUp()
        self.patches = patches
        self.obj = obj
        self.test_config = TestConfig()
        self.test_relation = TestRelation()
        self.patch_all()

    def patch(self, method):
        _m = patch.object(self.obj, method)
        mock = _m.start()
        self.addCleanup(_m.stop)
        return mock

    def patch_all(self):
        for method in self.patches:
            setattr(self, method, self.patch(method))


class TestConfig(object):

    def __init__(self):
        self.config = get_default_config()
        self.config_prev = {}

    def previous(self, k):
        return self.config_prev[k] if k in self.config_prev else self.config[k]

    def set_previous(self, k, v):
        self.config_prev[k] = v

    def unset_previous(self, k):
        if k in self.config_prev:
            self.config_prev.pop(k)

    def changed(self, k):
        if not self.config_prev:
            return True
        return self.get(k) != self.previous(k)

    def get(self, attr=None):
        if not attr:
            return self
        try:
            return self.config[attr]
        except KeyError:
            return None

    def get_all(self):
        return self.config

    def set(self, attr, value):
        if attr not in self.config:
            raise KeyError
        self.config[attr] = value

    def __getitem__(self, k):
        return self.get(k)


class TestRelation(object):

    def __init__(self, relation_data={}):
        self.relation_data = relation_data

    def set(self, relation_data):
        self.relation_data = relation_data

    def get(self, attr=None, unit=None, rid=None):
        if attr is None:
            return self.relation_data
        elif attr in self.relation_data:
            return self.relation_data[attr]
        return None


@contextmanager
def patch_open():
    """Patch open().

    Patch open() to allow mocking both open() itself and the file that is
    yielded.

    Yields the mock for "open" and "file", respectively.
    """
    mock_open = MagicMock(spec=open)
    mock_file = MagicMock(spec=io.FileIO)

    @contextmanager
    def stub_open(*args, **kwargs):
        mock_open(*args, **kwargs)
        yield mock_file

    with patch('builtins.open', stub_open):
        yield mock_open, mock_file
