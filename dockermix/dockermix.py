import docker
import os, sys, yaml, copy, StringIO
import dockermix
from requests.exceptions import HTTPError
from .container import Container
import utils

class ContainerError(Exception):
  pass

class ContainerMix:
  def __init__(self, conf_file=None, environment=None):
    self.log = utils._setupLogging()
    self.containers = {}
    
    if environment:
      self.load(environment)      
    else:
      if not conf_file.startswith('/'):
        conf_file = os.path.join(os.path.dirname(sys.argv[0]), conf_file)

      data = open(conf_file, 'r')
      self.config = yaml.load(data)
      
    # On load order containers into the proper startup sequence      
    self.start_order = utils.order(self.config['containers'])

  def get(self, container):
    return self.containers[container]

  def build(self, wait_time=60):
    for container in self.start_order:      
      if not self.config['containers'][container]:
        sys.stderr.write("Error: no configuration found for container: " + container + "\n")
        exit(1)

      config = self.config['containers'][container]
      if 'base_image' not in config:
        sys.stderr.write("Error: no base image specified for container: " + container)
        exit(1)

      base = config['base_image']

      self._handleRequire(container, wait_time)
                        
      self.log.info('Building container: %s using base template %s', container, base)
      count = 1
      tag_name = False
      if 'count' in config:
        count = config['count']  
        tag_name = True

      while count > 0:
        name = container
        if tag_name == True:
          name = name + "_" + str(count)

        build = Container(name, copy.deepcopy(config))
        dockerfile = None
        if 'buildspec' in config:
          if 'dockerfile' in config['buildspec']:      
            dockerfile = config['buildspec']['dockerfile']
          if 'url' in config['buildspec']:  
            # TODO: this doesn't do anything yet
            dockerfile_url = config['buildspec']['url']

        build.build(dockerfile)

        self.containers[name] = build
        count = count - 1
      
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
      self.config = yaml.load(input_file)

      for container in self.config['containers']:
        self.containers[container] = Container(container, self.config['containers'][container])
    
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
        
        result = utils.waitForService(service_ip, int(port), wait_time)
        if result < 0:
          self.log.error('Never found service %s on port %s', service, port)
          self.log.error('Shutting down the environment')
          self.destroy()
          raise ContainerError("Couldn't find required services, shutting down")
