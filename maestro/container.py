import os
import docker
from exceptions import ContainerError
import utils, StringIO, logging

class Container:
  def __init__(self, name, state, config):
    self.log = logging.getLogger('maestro')
    
    self.state = state    
    self.config = config

    self.name = name
    
    #if 'command' not in self.config:
    #  self.log.error("Error: No command specified for container " + name + "\n")
    #  raise ContainerError('No command specified in configuration') 
      
    self.docker_client = docker.Client()
  
  def create(self):
    self._start_container(false) 

  def run(self):
    self._start_container()

  def start(self):
    self.docker_client.start(self.state['container_id'])
  
  def stop(self, timeout=10):
    self.docker_client.stop(self.state['container_id'], timeout=timeout)
    
  def destroy(self, timeout=None):
    self.stop(timeout)
    self.docker_client.remove_container(self.state['container_id'])    

  def get_ip_address(self):
    state = docker.Client().inspect_container(self.state['container_id'])    
    return state['NetworkSettings']['IPAddress']

  def _start_container(self, start=True):
    # Start the container
    self.state['container_id'] = self.docker_client.create_container(self.state['image_id'], **self.config)['Id']
    
    if (start):
      self.start()

    self.log.info('Container started: %s %s', self.name, self.state['container_id'])     
