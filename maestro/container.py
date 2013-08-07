import os
from exceptions import ContainerError
import utils, StringIO, logging
import py_backend

class Container:
  def __init__(self, name, state, config, mounts=None):
    self.log = logging.getLogger('maestro')
    
    self.state = state    
    self.config = config
    self.name = name
    self.mounts = mounts

    if 'hostname' not in self.config:
      self.config['hostname'] = name
      
    #if 'command' not in self.config:
    #  self.log.error("Error: No command specified for container " + name + "\n")
    #  raise ContainerError('No command specified in configuration') 
      
    self.backend = py_backend.PyBackend()

  def create(self):
    self._start_container(False) 

  def run(self):
    self._start_container()

  def start(self):
    utils.status("Starting container %s - %s" % (self.name, self.state['container_id'])) 
    self.backend.start_container(self.state['container_id'], self.mounts)
  
  def stop(self, timeout=10):
    utils.status("Stopping container %s - %s" % (self.name, self.state['container_id']))     
    self.backend.stop_container(self.state['container_id'], timeout=timeout)
    
  def destroy(self, timeout=None):
    self.stop(timeout)
    utils.status("Destroying container %s - %s" % (self.name, self.state['container_id']))         
    self.backend.remove_container(self.state['container_id'])    

  def get_ip_address(self):
    return self.backend.get_ip_address(self.state['container_id']) 

  def inspect(self):
    return self.backend.inspect_container(self.state['container_id'])   
    
  def _start_container(self, start=True):
    # Start the container
    self.state['container_id'] = self.backend.create_container(self.state['image_id'], self.config)
    
    if (start):
      self.start()

    self.log.info('Container started: %s %s', self.name, self.state['container_id'])     
