import docker
import os, sys, yaml, copy, string, StringIO
import maestro, template
from requests.exceptions import HTTPError
from .container import Container

import utils

class ContainerError(Exception):
  pass

class Service:
  def __init__(self, conf_file=None, environment=None):
    self.log = utils.setupLogging()
    self.containers = {}
    self.templates = {}

    if environment:
      self.load(environment)      
    else:
      if not conf_file.startswith('/'):
        conf_file = os.path.join(os.path.dirname(sys.argv[0]), conf_file)

      data = open(conf_file, 'r')
      self.config = yaml.load(data)
      
    # On load, order templates into the proper startup sequence      
    self.start_order = utils.order(self.config['templates'])

  def get(self, container):
    return self.containers[container]

  def build(self, wait_time=60):
    for tmpl in self.start_order:      
      if not self.config['templates'][tmpl]:
        sys.stderr.write("Error: no configuration found for template: " + tmpl + "\n")
        exit(1)

      config = self.config['templates'][tmpl]

      self._handleRequire(tmpl, wait_time)
      
      # Create the template. The service name and version will be dynamic once the new config format is implemented
      tmpl_instance = template.Template(tmpl, config, 'service', '0.1')
      tmpl_instance.build()

      self.templates[tmpl] = tmpl_instance

      # If count is defined in the config then we're launching multiple instances of the same thing
      # and they'll need to be tagged accordingly. Count only applies on build.
      count = tag_name = 1
      if 'count' in config:
        count = tag_name = config['count']  
      
      while count > 0:      
        name = tmpl
        if tag_name > 1:
          name = name + "__" + str(count)

        instance = tmpl_instance.instantiate(name)
        instance.run()

        self.containers[name] = instance
        
        count = count - 1
      
  def destroy(self, timeout=None):
    for container in self.containers:
      self.log.info('Destroying container: %s', container)      
      self.containers[container].destroy(timeout)     

  def start(self, container=None, wait_time=60):
    # If a container is provided we just start that container
    # TODO: may need an abstraction here to handle names of multi-container groups
    if container:
      self.log.info('Starting container: %s', container)      
      self.containers[container].start()  
    else:
      for container in self.start_order:
        self.log.info('Starting container: %s', container)      
        
        self._handleRequire(container, wait_time)
        
        self.containers[container].start()

  def stop(self, container=None, timeout=None):
    if container:
      self.log.info('Stopping container: %s', container)      
      self.containers[container].stop(timeout)
    else:
      for container in self.containers:     
        self.log.info('Stopping container: %s', container)      
        self.containers[container].stop(timeout)

  def load(self, filename='envrionment.yml'):
    self.log.info('Loading environment from: %s', filename)      
    
    with open(filename, 'r') as input_file:
      self.config = yaml.load(input_file)

      for tmpl in self.config['templates']:
        # TODO fix hardcoded service name and version
        self.templates[tmpl] = template.Template(tmpl, self.config['templates'][tmpl], 'service', '0.1')
      
      for container in self.config['containers']:
        self.containers[container] = Container(container, self.config['containers'][container], 
          self.config['containers'][container])
    
  def save(self, filename='environment.yml'):
    self.log.info('Saving environment state to: %s', filename)      
      
    with open(filename, 'w') as output_file:
      output_file.write(self.dump())

  def run(self, template, commandline=None):
    if template in self.templates:
      # TODO: name need to be dynamic here. Need to handle static and temporary cases.
      container = self.templates[template].instantiate(template + "32", commandline)
      container.run()

      # for dynamic runs there  needs to be a way to display the output of the command.

      return container
    else:
      # Should handle arbitrary containers
      raise ContainerError("Unknown template")

  def ps(self):
    columns = "{0:<14}{1:<19}{2:<44}{3:<11}\n" 
    result = columns.format("ID", "NODE", "COMMAND", "STATUS")
    for container in self.containers:
      container_id = self.containers[container].state['container_id']
      
      node_name = (container[:15] + '..') if len(container) > 17 else container

      command = ''
      status = 'Stopped'
      try:
        state = docker.Client().inspect_container(container_id)
        command = string.join([state['Path']] + state['Args'])
        command = (command[:40] + '..') if len(command) > 42 else command
        
        if state['State']['Running']:
          status = 'Running'
      except HTTPError:
        status = 'Destroyed'

      result += columns.format(container_id, node_name, command, status)

    return result.rstrip('\n')

  def dump(self):
    result = {}
    result['templates'] = {}
    for template in self.templates:      
      result['templates'][template] = self.templates[template].config

    result['containers'] = {}
    for container in self.containers:      
      result['containers'][container] = self.containers[container].state

    return yaml.dump(result, Dumper=yaml.SafeDumper)

  def _pollService(self, container, service, port, wait_time):
    # Based on start_order the service should already be running
    service_ip = self.containers[service].get_ip_address()
    self.log.info('Starting %s: waiting for service %s on ip %s and port %s', container, service, service_ip, port)            
    
    result = utils.waitForService(service_ip, int(port), wait_time)
    if result < 0:
      self.log.error('Never found service %s on port %s', service, port)
      raise ContainerError("Couldn't find required services, aborting")

    return service_ip + ":" + str(port)

  def _handleRequire(self, container, wait_time):
    env = []
    # Wait for any required services to finish registering        
    config = self.config['templates'][container]
    if 'require' in config:
      try:
        # Containers can depend on mulitple services
        for service in config['require']:
          service_env = []
          port = config['require'][service]['port']          
          if port:
            # If count is defined then we need to wait for all instances to start                    
            count = config['require'][service].get('count', 1)          
            if count > 1:
              while count > 0:
                name = service + "__" + str(count)
                service_env.append(self._pollService(container, name, port, wait_time))
                count = count - 1                
            else:
              service_env.append(self._pollService(container, service, port, wait_time))

            env.append(service.upper() + "=" + " ".join(service_env))
      except:
        self.log.error('Failure on require. Shutting down the environment')
        self.destroy()
        raise
      
      # Setup the env for dependent services
      if 'environment' in config['config']:
        config['config']['environment'] += env
      else:
        config['config']['environment'] = env
    