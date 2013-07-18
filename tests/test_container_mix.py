import unittest, sys, yaml
import docker
sys.path.append('.')
from dockermix import dockermix
from requests.exceptions import HTTPError

class TestContainer(unittest.TestCase):
  def setUp(self):
    self.mix = dockermix.ContainerMix('dockermix.yml')
    self.mix.build()
    
  def tearDown(self):
    self.mix.destroy()
  
  #@unittest.skip("skipping")  
  def testBuild(self):
    env = yaml.load(self.mix.dump())
    self._configCheck(env)   

  #@unittest.skip("Skipping")
  def testBuildDockerfile(self):
    mix = dockermix.ContainerMix('dockermix-dockerfile.yml')
    mix.build()
    env = yaml.load(mix.dump())
        
    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
      
      self.assertIsNotNone(state)
      self.assertIn(container, ['test_server_1', 'test_server_2'])

      self.assertEqual(state['State']['ExitCode'], 0)

      if container == 'test_server_1':
        self.assertNotEqual(state['Config']['Image'], 'ubuntu')
        self.assertEqual(state['Path'], 'ns')
        self.assertEqual(state['Args'][0], '-l')
        
      #elif container == 'test_server_2':
      #  self.assertNotEqual(state['Config']['Image'], 'ubuntu')
       # self.assertEqual(state['Path'], 'ls')
       # self.assertEqual(state['Args'][0], '-l')  
        
  
  #@unittest.skip("skipping")
  def testPorts(self):
    env = yaml.load(self.mix.dump())
    self.mix.save()
    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
      
      self.assertIsNotNone(state)
      if container == 'test_server_1':
        self.assertIn('8080', state['NetworkSettings']['PortMapping']['Tcp'])
      elif container == 'test_server_2':
        self.assertEqual(state['NetworkSettings']['PortMapping']['Tcp'], {})
      else:
        # Shouldn't get here
        self.assertFalse(True)
  
  #@unittest.skip("skipping")
  def testDestroy(self):
    mix = dockermix.ContainerMix('dockermix.yml')
    mix.build()
   
    env = yaml.load(mix.dump())
    mix.destroy()

    for container in env['containers']:
      with self.assertRaises(HTTPError) as e:
        docker.Client().inspect_container(env['containers'][container]['container_id'])

      self.assertEqual(str(e.exception), '404 Client Error: Not Found')
  
  #@unittest.skip("skipping")  
  def testSave(self):
    self.mix.save()
    with open('environment.yml', 'r') as input_file:
      env = yaml.load(input_file)

    self._configCheck(env)  

  #@unittest.skip("skipping")
  def testDependencyEnv(self):
    mix = dockermix.ContainerMix('dockermix-count.yml')
        
    mix.build()
    
    # Verify that all three services are running
    env = yaml.load(mix.dump())    
    
    self.assertEqual(len(env['containers']), 4)

    state = docker.Client().inspect_container(env['containers']['service_post']['container_id'])
    #self.assertIn("SERVICE1", state['Config']['Env'])
      
    mix.destroy()
  
  #@unittest.skip("skipping")
  def testCount(self):
    mix = dockermix.ContainerMix('dockermix-count.yml')
        
    mix.build(180)
    
    # Verify that all three services are running
    env = yaml.load(mix.dump())    
    
    self.assertEqual(len(env['containers']), 4)

    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
      
      #Verify the containers are running
      self.assertTrue(state['State']['Running'])
      self.assertEqual(state['State']['ExitCode'], 0)
    
    mix.destroy()

  #@unittest.skip("skipping")
  def testRequire(self):
    mix = dockermix.ContainerMix('dockermix-require.yml')
    
    # Verify that it determined the correct start order
    start_order = mix.start_order
    self.assertEqual(start_order[0], 'test_server_2')
    self.assertEqual(start_order[1], 'test_server_1')
    self.assertEqual(start_order[2], 'test_server_3')
    
    mix.build()
    
    # Verify that all three services are running
    env = yaml.load(mix.dump())    
    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
      
      #Verify the containers are running
      self.assertTrue(state['State']['Running'])
      self.assertEqual(state['State']['ExitCode'], 0)
    
    mix.destroy()

  #@unittest.skip("skipping")
  def testStop(self):
    mix = dockermix.ContainerMix('dockermix-startstop.yml')
    mix.build()
    
    env = yaml.load(mix.dump())    
    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
      
      #Verify the containers are running
      self.assertTrue(state['State']['Running'])
      self.assertEqual(state['State']['ExitCode'], 0)
    
    mix.stop()
    env = yaml.load(mix.dump())    
    
    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
      
      #Verify the containers are stopped 
      self.assertFalse(state['State']['Running'])
      self.assertNotEqual(state['State']['ExitCode'], 0)

    mix.destroy()

  #@unittest.skip("skipping")
  def testStart(self):  
    mix = dockermix.ContainerMix('dockermix-startstop.yml')
    mix.build()
    
    env = yaml.load(mix.dump())    
    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
    
      # Verify the containers are running  
      self.assertTrue(state['State']['Running'])
      self.assertEqual(state['State']['ExitCode'], 0)
    
    mix.stop()
    env = yaml.load(mix.dump())    
    
    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
      
      # Verify the containers are stopped
      self.assertFalse(state['State']['Running'])
      self.assertNotEqual(state['State']['ExitCode'], 0)
    
    mix.start()
    env = yaml.load(mix.dump())    
    
    for container in env['containers']:
      state = docker.Client().inspect_container(env['containers'][container]['container_id'])
      
      # Verify the containers are running again
      self.assertTrue(state['State']['Running'])
      self.assertEqual(state['State']['ExitCode'], 0)
    
    mix.destroy()
  
  #@unittest.skip("skipping")
  def testStatus(self):
    mix = dockermix.ContainerMix('dockermix-startstop.yml')
    mix.build()
    
    status = mix.status() 

    lines = status.split("\n")
    # Skip over the headers
    del(lines[0])
    for line in lines:
      if len(line) > 0:
        self.assertIn(line[14:29].rstrip(),  ['test_server_1', 'test_server_2'])
        self.assertEqual(line[67:77].rstrip(), "Running")

    mix.destroy()

    status = mix.status() 

    lines = status.split("\n")
    # Skip over the headers
    del(lines[0])
    for line in lines:
      if len(line) > 0:
        self.assertIn(line[14:29].rstrip(),  ['test_server_1', 'test_server_2'])
        self.assertEqual(line[67:77].rstrip(), "Destroyed")

  #@unittest.skip("skipping")
  def testLoad(self):
    self.mix.save()
    mix = dockermix.ContainerMix(environment = 'environment.yml')
    env = yaml.load(mix.dump())    
    
    self._configCheck(env)    
    
  def _configCheck(self, env):
    self.assertIsNotNone(env)
    
    for container in env['containers']:
      self.assertIn(container, ['test_server_1', 'test_server_2'])

      state = docker.Client().inspect_container(env['containers'][container]['container_id'])

      self.assertEqual(state['Config']['Image'], 'ubuntu')
      self.assertEqual(state['State']['ExitCode'], 0)

      if container == 'test_server_1':
        self.assertEqual(state['Path'], 'ps')
        self.assertEqual(state['Args'][0], 'aux')
        self.assertEqual(state['Config']['Hostname'], 'test_server_1')
        self.assertEqual(state['Config']['User'], 'root')
        self.assertTrue(state['Config']['OpenStdin'])
        self.assertTrue(state['Config']['Tty'])
        self.assertEqual(state['Config']['Memory'], 2560000)
        self.assertIn("ENV_VAR=testing", state['Config']['Env'])
        self.assertIn("8.8.8.8", state['Config']['Dns'])
        
      elif container == 'test_server_2':
        self.assertEqual(state['Path'], 'ls')
        self.assertEqual(state['Args'][0], '-l')  
        self.assertEqual(state['Config']['Hostname'], 'test_server_2')
      
if __name__ == '__main__':
    unittest.main()