import unittest, sys
sys.path.append('.')
from dockermix import dockermix
from requests.exceptions import HTTPError

class TestContainer(unittest.TestCase):
  def testBuild(self):
    pass