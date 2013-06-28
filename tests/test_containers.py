import unittest, sys
sys.path.append('.')
from dockermix import dockermix

class TestContainer(unittest.TestCase):
  def testBuild(self):
    context = self._containers.get('example_test')
    self.assertEquals(context.test_name, 'example_test')
    
  def testDestroy(self):
    context = self._containers.get('example_test')
    self.assertEquals(context.salt_client.cmd(context.build_tag, 'cmd.run', ['cat /tmp/test-file'])[context.build_tag], 'Just a test')

    context = self._containers.get('example_test2')
    self.assertEquals(context.salt_client.cmd(context.build_tag, 'cmd.run', ['cat /tmp/test-file'])[context.build_tag], 'Just a test')

if __name__ == '__main__':
    unittest.main()