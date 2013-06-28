import unittest, sys
sys.path.append('.')
from dockermix import dockermix
from requests.exceptions import HTTPError

class TestContainer(unittest.TestCase):
  def testBuild(self):
    container = dockermix.Container('test_container', 'ps aux')

    container.build()

    self.assertIsNotNone(container.container_id)
    
    state = container.docker_client.inspect_container(container.container_id)

    self.assertEqual(state['Path'], 'ps')
    self.assertEqual(state['Args'][0], 'aux')
    self.assertEqual(state['Config']['Image'], 'ubuntu')

  def testDestroy(self):
    container = dockermix.Container('test_container', 'ps aux')

    container.build()

    self.assertIsNotNone(container.container_id)

    container.destroy()

    with self.assertRaises(HTTPError) as e:
      container.docker_client.inspect_container(container.container_id)
    
    self.assertEqual(str(e.exception), '404 Client Error: Not Found')
    
if __name__ == '__main__':
    unittest.main()