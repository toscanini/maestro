import unittest, sys
sys.path.append('.')
from maestro import service
from requests.exceptions import HTTPError

class TestContainer(unittest.TestCase):
  def testInit(self):
    with self.assertRaises(service.ContainerError) as e:
        service.Container('test_container', {})

  def testGetIpAddress(self):
    container = service.Container('test_container', {'config': {'command': 'ps aux'}})

    container.build()

    self.assertIsNotNone(container.desc['container_id'])    
    self.assertIsNotNone(container.get_ip_address())

  def testBuild(self):
    container = service.Container('test_container', {'config': {'command': 'ps aux'}})

    container.build()

    self.assertIsNotNone(container.desc['container_id'])
    
    state = container.docker_client.inspect_container(container.desc['container_id'])

    self.assertEqual(state['Path'], 'ps')
    self.assertEqual(state['Args'][0], 'aux')
    self.assertEqual(state['Config']['Image'], 'ubuntu')

  def testDestroy(self):
    container = service.Container('test_container', {'config': {'command': 'ps aux'}})

    container.build()

    self.assertIsNotNone(container.desc['container_id'])

    container.destroy()

    with self.assertRaises(HTTPError) as e:
      container.docker_client.inspect_container(container.desc['container_id'])
    
    self.assertEqual(str(e.exception), '404 Client Error: Not Found')
    
if __name__ == '__main__':
    unittest.main()