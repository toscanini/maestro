import docker
import os, sys, time, subprocess, yaml, shutil, copy, socket
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

def order(raw_list):
  def _process(wait_list):
    new_wait = []
    for item in wait_list:
      match = False
      for dependency in raw_list[item]['require']:
        if dependency in ordered_list:
          match = True  
        else:
          match = False
          break

      if match:
        ordered_list.append(item)
      else:
        new_wait.append(item)

    if len(new_wait) > 0:
      # Guard against circular dependencies
      if len(new_wait) == len(wait_list):
        raise Exception("Unable to satisfy the require for: " + item)

      # Do it again for any remaining items
      _process(new_wait)

  ordered_list = []
  wait_list = []
  # Start by building up the list of items that do not have any dependencies
  for item in raw_list:  
    if 'require' not in raw_list[item]:
      ordered_list.append(item)
    else:
      wait_list.append(item)

  # Then recursively order the items that do define dependencies
  _process(wait_list)

  return ordered_list

def waitForService(ip, port, retries=60):      
  while retries >= 0:
    try:        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect((ip, port))
        s.close()
        break
    except:
      time.sleep(0.5)
      retries = retries - 1
      continue
    
  return retries

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
      self.start_order = order(self.config['containers'])

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

  def build(self, wait_time=60):
    for container in self.start_order:
      #TODO: confirm base_image exists
      if not self.config['containers'][container]:
        sys.stderr.write("Error: no configuration found for container: " + container + "\n")
        exit(1)

      if 'base_image' not in self.config['containers'][container]:
        sys.stderr.write("Error: no base image specified for container: " + container)
        exit(1)

      base = self.config['containers'][container]['base_image']

      self._handleRequire(container, wait_time)
                        
      self.log.info('Building container: %s using base template %s', container, base)
      
      build = Container(container, self.config['containers'][container])
      dockerfile = None
      if 'dockerfile' in self.config['containers'][container]:
        dockerfile = self.config['containers'][container]['dockerfile']
      build.build(dockerfile)

      self.containers[container] = build
      
  def destroy(self):
    for container in reversed(self.start_order):
      self.log.info('Destroying container: %s', container)      
      self.containers[container].destroy()     

  def start(self, wait_time=60):
    for container in self.start_order:
      self.log.info('Starting container: %s', container)      
      
      self._handleRequire(container, wait_time)
      
      self.containers[container].start()

  def stop(self):
    for container in reversed(self.start_order):      
      self.log.info('Stopping container: %s', container)      
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
      container_id = self.containers[container].desc['container_id']
      
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
      output = result['containers'][container] = self.containers[container].desc

    return yaml.dump(result, Dumper=yaml.SafeDumper)

  def _handleRequire(self, container, wait_time):
    # Wait for any required services to finish registering        
    if 'require' in self.config['containers'][container]:
      # Containers can depend on mulitple services
      for service in self.config['containers'][container]['require']:
        port = self.config['containers'][container]['require'][service]
        # Based on start_order the service should already be running
        service_ip = self.containers[service].get_ip_address()
        self.log.info('Starting %s: waiting for service %s on ip %s and port %s', container, service, service_ip, port)            
        
        result = waitForService(service_ip, int(port), wait_time)
        if result < 0:
          self.log.error('Never found service %s on port %s', service, port)
          self.log.error('Shutting down the environment')
          self.destroy()
          raise ContainerError("Couldn't find required services, shutting down")
    
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
    
  def get_ip_address(self):
    container_id = self.desc['container_id']
      
    state = docker.Client().inspect_container(container_id)    
    return state['NetworkSettings']['IPAddress']

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
    self.desc['container_id'] = self.docker_client.create_container(self.desc['image_id'], **self.config)['Id']
    
    self.start()

    self.log.info('Container started: %s %s', self.build_tag, self.desc['container_id'])     
