import os
import docker
import service
import utils, StringIO

class Container:
  def __init__(self, name, container_desc={}):
    self.log = utils._setupLogging()
    
    if 'config' not in container_desc:
      raise service.ContainerError('No Docker configuration parameters found.')

    self.desc = container_desc
    self.config = container_desc['config']

    self.name = name
    
    self.build_tag = name + '-' + str(os.getpid())

    if 'command' not in self.config:
      self.log.error("Error: No command specified for container " + name + "\n")
      raise service.ContainerError('No command specified in configuration') 
      
    self.docker_client = docker.Client()
    
    if 'base_image' not in self.desc:
      self.desc['base_image'] = 'ubuntu'
      
  def build(self, dockerfile=None):
    if dockerfile:        
      self._build_container(dockerfile)
    else:
      # If there's no dockerfile then we're just launching an empty base    
      self.desc['image_id'] = self.desc['base_image']
    
    self._start_container()
    
  def destroy(self, timeout=None):
    self.stop(timeout)
    self.docker_client.remove_container(self.desc['container_id'])    
    self.docker_client.remove_image(self.build_tag)

  def start(self):
    self.docker_client.start(self.desc['container_id'])
  
  def stop(self, timeout=10):    
    self.docker_client.stop(self.desc['container_id'], timeout=timeout)
    
  def get_ip_address(self):
    container_id = self.desc['container_id']
      
    state = docker.Client().inspect_container(container_id)    
    return state['NetworkSettings']['IPAddress']

  def _build_container(self, dockerfile):
    # Build the container
    result = self.docker_client.build(fileobj=StringIO.StringIO(dockerfile))
    # Commented out until my pull request to add logger configuration gets merged into docker-py
    #result = self.docker_client.build(dockerfile.split('\n'), logger=self.log)
    
    self.desc['image_id'] = result[0]
    
    # Tag the container with the name and process id
    self.docker_client.tag(self.desc['image_id'], self.build_tag)
    self.log.info('Container registered with tag: %s', self.build_tag)      

  def _start_container(self):
    # Start the container
    self.desc['container_id'] = self.docker_client.create_container(self.desc['image_id'], **self.config)['Id']
    
    self.start()

    self.log.info('Container started: %s %s', self.build_tag, self.desc['container_id'])     
