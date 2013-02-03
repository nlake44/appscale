#!/usr/bin/env python
# Programmer: Chris Bunch (chris@appscale.com)


# General-purpose Python library imports
import base64
import httplib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
import yaml


# Third party libraries
from flexmock import flexmock
import M2Crypto
import SOAPpy


# AppScale import, the library that we're testing here
lib = os.path.dirname(__file__) + os.sep + ".." + os.sep + "lib"
sys.path.append(lib)
from appscale_logger import AppScaleLogger
from appscale_tools import AppScaleTools
from custom_exceptions import BadConfigurationException
from local_state import APPSCALE_VERSION
from local_state import LocalState
from node_layout import NodeLayout
from parse_args import ParseArgs
from remote_helper import RemoteHelper


class TestAppScaleAddKeypair(unittest.TestCase):


  def setUp(self):
    self.keyname = "boobazblargfoo"
    self.function = "appscale-add-keypair"

    # mock out any writing to stdout
    flexmock(AppScaleLogger)
    AppScaleLogger.should_receive('log').and_return()

    # mock out all sleeping
    flexmock(time)
    time.should_receive('sleep').and_return()

    # throw some default mocks together for when invoking via shell succeeds
    # and when it fails
    self.fake_temp_file = flexmock(name='fake_temp_file')
    self.fake_temp_file.should_receive('read').and_return('boo out')
    self.fake_temp_file.should_receive('close').and_return()

    flexmock(tempfile)
    tempfile.should_receive('TemporaryFile').and_return(self.fake_temp_file)

    self.success = flexmock(name='success', returncode=0)
    self.success.should_receive('wait').and_return(0)

    self.failed = flexmock(name='success', returncode=1)
    self.failed.should_receive('wait').and_return(1)


  def test_appscale_with_ips_layout_flag_but_no_copy_id(self):
    # assume that we have ssh-keygen but not ssh-copy-id
    flexmock(subprocess)
    subprocess.should_receive('Popen').with_args(re.compile('which ssh-keygen'),
      shell=True, stdout=self.fake_temp_file, stderr=sys.stdout) \
      .and_return(self.success)

    flexmock(subprocess)
    subprocess.should_receive('Popen').with_args(re.compile('which ssh-copy-id'),
      shell=True, stdout=self.fake_temp_file, stderr=sys.stdout) \
      .and_return(self.failed)

    # don't use a 192.168.X.Y IP here, since sometimes we set our virtual
    # machines to boot with those addresses (and that can mess up our tests).
    ips_layout = yaml.safe_load("""
master : public1
database: public1
zookeeper: public2
appengine:  public3
    """)

    argv = [
      "--ips_layout", base64.b64encode(yaml.dump(ips_layout)),
      "--keyname", self.keyname
    ]
    options = ParseArgs(argv, self.function).args
    self.assertRaises(BadConfigurationException, AppScaleTools.add_keypair,
      options)


  def test_appscale_with_ips_layout_flag_and_success(self):
    # assume that we have ssh-keygen and ssh-copy-id
    flexmock(subprocess)
    subprocess.should_receive('Popen').with_args(re.compile('which ssh-keygen'),
      shell=True, stdout=self.fake_temp_file, stderr=sys.stdout) \
      .and_return(self.success)

    flexmock(subprocess)
    subprocess.should_receive('Popen').with_args(re.compile('which ssh-copy-id'),
      shell=True, stdout=self.fake_temp_file, stderr=sys.stdout) \
      .and_return(self.success)

    # assume that we have a ~/.appscale
    flexmock(os.path)
    os.path.should_call('exists')
    os.path.should_receive('exists').with_args(LocalState.LOCAL_APPSCALE_PATH) \
      .and_return(True)

    # don't use a 192.168.X.Y IP here, since sometimes we set our virtual
    # machines to boot with those addresses (and that can mess up our tests).
    ips_layout = yaml.safe_load("""
master : public1
database: public1
zookeeper: public2
appengine:  public3
    """)

    argv = [
      "--ips_layout", base64.b64encode(yaml.dump(ips_layout)),
      "--keyname", self.keyname
    ]
    options = ParseArgs(argv, self.function).args
    AppScaleTools.add_keypair(options)
