import unittest, sys, yaml
import docker
sys.path.append('.')
from dockermix import dockermix
from requests.exceptions import HTTPError

class TestContainer(unittest.TestCase):
  def testBuild(self):
    mix = dockermix.ContainerMix('dockermix.yml')
    mix.build()
    env = yaml.load(mix.dump())

    self.assertIsNotNone(env)
    
    for container in env['containers']:
      self.assertIn(container, ['test_server_1', 'test_server_2'])

      state = docker.Client().inspect_container(env['containers'][container]['container_id'])

      #self.assertEqual(state['Path'], 'ps')
      #self.assertEqual(state['Args'][0], 'aux')
      self.assertEqual(state['Config']['Image'], 'ubuntu')

  def testPorts(self):
    mix = dockermix.ContainerMix('dockermix.yml')
    mix.build()
    env = yaml.load(mix.dump())

    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
      
      self.assertIsNotNone(state)
      if container == 'test_server_1':
        self.assertIn('8080', state['NetworkSettings']['PortMapping'])
      elif container == 'test_server_2':
        self.assertEqual(state['NetworkSettings']['PortMapping'], {})
      else:
        # Shouldn't get here
        self.assertFalse(True)

  def testDestroy(self):
    mix = dockermix.ContainerMix('dockermix.yml')
    mix.build()
    env = yaml.load(mix.dump())
    mix.destroy()

    for container in env['containers']:
      with self.assertRaises(HTTPError) as e:
        docker.Client().inspect_container(env['containers'][container]['container_id'])

      self.assertEqual(str(e.exception), '404 Client Error: Not Found')
    
if __name__ == '__main__':
    unittest.main()