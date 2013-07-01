import docker
import os, sys, time, subprocess, yaml, shutil, copy
import logging
import dockermix

class ContainerMix:
  def __init__(self, conf_file=None, environment=None):
    self._setupLogging()
    self.containers = {}
    
    if environment:
      self.load(environment)
    else:
      if not conf_file.startswith('/'):
        conf_file = os.path.join(os.path.dirname(sys.argv[0]), conf_file)

      data = open(conf_file, 'r')
      self.config = yaml.load(data)      

  def get(self, container):
    return self.containers[container]

  def build(self):
    for container in self.config['containers']:
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

  def dump(self):
    result = {}
    result['containers'] = {}
    for container in self.containers:      
      output = result['containers'][container] = self.containers[container].config

    return yaml.dump(result, Dumper=yaml.SafeDumper)

  def _setupLogging(self):
    self.log = logging.getLogger('dockermix')
    self.log.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(levelname)-10s %(message)s")
    filehandler = logging.FileHandler('dockermix.log', 'w')
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(formatter)
    self.log.addHandler(filehandler)  


class Container:
  def __init__(self, name, config={}, build_tag=None):
    self.log = logging.getLogger('dockermix')

    self.config = config
    self.name = name
    
    self.build_tag = build_tag
    if not build_tag:
      self.build_tag = name + '-' + str(os.getpid())

    if 'command' not in self.config:
      # TODO: this should probably raise an error rather than default.
      self.log.info('No command specified in configuration defaulting to /bin/true')     
      self.config['command'] = '/bin/true'
    
    self.docker_client = docker.Client()
    
    if 'base_image' not in self.config:
      self.config['base_image'] = 'ubuntu'
      
  def build(self, dockerfile=None):
    if dockerfile:        
      self._build_container(dockerfile)
    else:
      # If there's no dockerfile then we're just launching an empty base    
      self.config['image_id'] = self.config['base_image']
    
    self._start_container()
    
  def destroy(self):
    self.stop()
    self.docker_client.remove_container(self.config['container_id'])    
    self.docker_client.remove_image(self.build_tag)

  def stop(self):
    self.docker_client.stop(self.config['container_id'])
    
  def _build_container(self, dockerfile):
    # Build the container
    result = self.docker_client.build(dockerfile.split('\n'))
    # Commented out until my pull request to add logger configuration gets merged into docker-py
    #result = self.docker_client.build(dockerfile.split('\n'), logger=self.log)
    
    self.config['image_id'] = result[0]
    
    # Tag the container with the name and process id
    self.docker_client.tag(self.config['image_id'], self.build_tag)
    self.log.info('Container registered with tag: %s', self.build_tag)      

  def _start_container(self):
    # Start the container
    clean_config = self._clean_config(self.config, ['image_id', 'base_image', 'dockerfile'])
    self.config['container_id'] = self.docker_client.create_container(self.config['image_id'], **clean_config)['Id']
    
    self.docker_client.start(self.config['container_id'])

    self.log.info('Container started: %s', self.build_tag)     

  # Get rid of unused keys so that we can do parameter expansion
  def _clean_config(self, config, keys):
    result = copy.deepcopy(config) 
    for key in keys:
      result.pop(key, None)
    return result