import unittest, sys
sys.path.append('.')
from maestro import container, exceptions, utils
from requests.exceptions import HTTPError

class TestContainer(unittest.TestCase):
  def testInit(self):
    with self.assertRaises(exceptions.ContainerError) as e:
        container.Container('test_container', utils.findImage('ubuntu'), {})

  def testGetIpAddress(self):
    # TODO: image_id will change
    c = container.Container('test_container', utils.findImage('ubuntu'), {'command': 'ps aux'})

    c.run()

    self.assertIsNotNone(c.desc['container_id'])    
    self.assertIsNotNone(c.get_ip_address())

  def testDestroy(self):
    c = container.Container('test_container', utils.findImage('ubuntu'), {'command': 'ps aux'})

    c.run()

    self.assertIsNotNone(c.desc['container_id'])

    c.destroy()

    with self.assertRaises(HTTPError) as e:
      c.docker_client.inspect_container(c.desc['container_id'])
    
    self.assertEqual(str(e.exception), '404 Client Error: Not Found')
    
if __name__ == '__main__':
    unittest.main()