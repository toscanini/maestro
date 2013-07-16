import docker
import os, sys, time, subprocess, yaml, shutil, copy
import logging
import dockermix
from requests.exceptions import HTTPError


def _setupLogging():
  log = logging.getLogger('dockermix')
  log.setLevel(logging.DEBUG)

  formatter = logging.Formatter("%(asctime)s %(levelname)-10s %(message)s")
  filehandler = logging.FileHandler('dockermix.log', 'w')
  filehandler.setLevel(logging.DEBUG)
  filehandler.setFormatter(formatter)
  log.addHandler(filehandler)  
  return log

class ContainerError(Exception):
  pass

class ContainerMix:
  def __init__(self, conf_file=None, environment=None):
    self.log = _setupLogging()
    self.containers = {}
    
    if environment:
      self.load(environment)
    else:
      if not conf_file.startswith('/'):
        conf_file = os.path.join(os.path.dirname(sys.argv[0]), conf_file)

      data = open(conf_file, 'r')
      self.config = yaml.load(data)
      # On load order containers into the proper startup sequence
        # Walk the list of containers
          # Any container that doesn't have a require goes at the top of the stack
          # Any container that does have a require goes below the container it requires
          # Watch for containers that depend on them self
          # Look for containers that can be started in parallel
        # If a require fails then the environment should be unwound
          # there should be an override for this
        # Also dockermix commands should be separated from docker commands
        # Loading could be complex with lots of dependencies 
        # Will need to check for circular dependencies
      # Create a way to wait for a container to be running.
        # Will need the IP and Port pair to check for
        # Polling should be limited to a set time or poll count      

  def get(self, container):
    return self.containers[container]

  def build(self):
    for container in self.config['containers']:
      #TODO: confirm base_image exists
      if not self.config['containers'][container]:
        sys.stderr.write("Error: no configuration found for container: " + container + "\n")
        exit(1)

      if 'base_image' not in self.config['containers'][container]:
        sys.stderr.write("Error: no base image specified for container: " + container)
        exit(1)

      base = self.config['containers'][container]['base_image']
        
      self.log.info('Building container: %s using base template %s', container, base)
      
      build = Container(container, self.config['containers'][container])
      dockerfile = None
      if 'dockerfile' in self.config['containers'][container]:
        dockerfile = self.config['containers'][container]['dockerfile']
      build.build(dockerfile)

      self.containers[container] = build
      
  def destroy(self):
    for container in self.containers:
      self.log.info('Destroying container: %s', container)      
      self.containers[container].destroy()     

  def start(self):
    for container in self.containers:      
      self.containers[container].start()

  def stop(self):
    for container in self.containers:      
      self.containers[container].stop()

  def load(self, filename='envrionment.yml'):
    self.log.info('Loading environment from: %s', filename)      
    
    with open(filename, 'r') as input_file:
      environment = yaml.load(input_file)

      for container in environment['containers']:
        self.containers[container] = Container(container, environment['containers'][container])
    
  def save(self, filename='environment.yml'):
    self.log.info('Saving environment state to: %s', filename)      
      
    with open(filename, 'w') as output_file:
      output_file.write(self.dump())

  def status(self):
    columns = "{0:<14}{1:<19}{2:<34}{3:<11}\n" 
    result = columns.format("ID", "NODE", "COMMAND", "STATUS")
    for container in self.containers:
      container_id = self.containers[container].config['container_id']
      
      node_name = (container[:15] + '..') if len(container) > 17 else container

      command = ''
      status = 'OFF'
      try:
        state = docker.Client().inspect_container(container_id)
        command = "".join([state['Path']] + state['Args'] + [" "])
        command = (command[:30] + '..') if len(command) > 32 else command
        
        if state['State']['Running']:
          status = 'Running'
      except HTTPError:
        status = 'Destroyed'

      result += columns.format(container_id, node_name, command, status)

    return result

  def dump(self):
    result = {}
    result['containers'] = {}
    for container in self.containers:      
      output = result['containers'][container] = self.containers[container].config

    return yaml.dump(result, Dumper=yaml.SafeDumper)

class Container:
  def __init__(self, name, container_desc={}):
    self.log = _setupLogging()
    
    if 'config' not in container_desc:
      raise ContainerError('No Docker configuration parameters found.')

    self.desc = container_desc
    self.config = container_desc['config']

    self.name = name
    
    self.build_tag = name + '-' + str(os.getpid())

    if 'command' not in self.config:
      self.log.error("Error: No command specified for container " + name + "\n")
      raise ContainerError('No command specified in configuration') 
      
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
    
  def destroy(self):
    self.stop()
    self.docker_client.remove_container(self.desc['container_id'])    
    self.docker_client.remove_image(self.build_tag)

  def start(self):
    self.docker_client.start(self.desc['container_id'])
  
  def stop(self):
    self.docker_client.stop(self.desc['container_id'])
    
  def _build_container(self, dockerfile):
    # Build the container
    result = self.docker_client.build(dockerfile.split('\n'))
    # Commented out until my pull request to add logger configuration gets merged into docker-py
    #result = self.docker_client.build(dockerfile.split('\n'), logger=self.log)
    
    self.desc['image_id'] = result[0]
    
    # Tag the container with the name and process id
    self.docker_client.tag(self.desc['image_id'], self.build_tag)
    self.log.info('Container registered with tag: %s', self.build_tag)      

  def _start_container(self):
    # Start the container
    #clean_config = self._clean_config(self.config, ['image_id', 'base_image', 'dockerfile'])
    self.desc['container_id'] = self.docker_client.create_container(self.desc['image_id'], **self.config)['Id']
    
    self.start()

    self.log.info('Container started: %s', self.build_tag)     

  # Get rid of unused keys so that we can do parameter expansion
  def _clean_config(self, config, keys):
    result = copy.deepcopy(config) 
    for key in keys:
      result.pop(key, None)
    return result