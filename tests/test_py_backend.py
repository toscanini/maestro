import unittest, sys, StringIO
sys.path.append('.')
from maestro import py_backend, exceptions, utils
from requests.exceptions import HTTPError

utils.setQuiet(True)

class TestContainer(unittest.TestCase):
  #@unittest.skip("skipping")
  def testStartStopRm(self):
    p = py_backend.PyBackend()
    
    c = p.create_container(utils.findImage('ubuntu'), {'command': '/bin/bash -c "while true; do echo hello world; sleep 60; done;"'})
    state = p.docker_client.inspect_container(c)
    self.assertFalse(state['State']['Running'])

    p.start_container(c)
    state = p.docker_client.inspect_container(c)
    self.assertTrue(state['State']['Running'])

    p.stop_container(c, 1)
    state = p.docker_client.inspect_container(c)
    self.assertFalse(state['State']['Running'])
        
    p.remove_container(c, 1)
    with self.assertRaises(HTTPError) as e:
      p.docker_client.inspect_container(c)
      
    self.assertEqual(str(e.exception), '404 Client Error: Not Found')
    
  def testBuildImage(self):
    dockerfile = """
      FROM ubuntu
      MAINTAINER test
      """
    p = py_backend.PyBackend()
    image_id = p.build_image(fileobj=StringIO.StringIO(dockerfile))[0]
    self.assertEqual(p.inspect_image(image_id)['author'], 'test') 

    p.remove_image(image_id)
    with self.assertRaises(HTTPError) as e:
      p.inspect_image(image_id)

  #@unittest.skip("skipping")  
  def testGetIpAddress(self):
    # TODO: image_id will change
    p = py_backend.PyBackend()
    
    c = p.run_container(utils.findImage('ubuntu'), {'command': 'ps aux'})

    self.assertIsNotNone(c)    
    
    self.assertIsNotNone(p.get_ip_address(c))
    
if __name__ == '__main__':
    unittest.main()