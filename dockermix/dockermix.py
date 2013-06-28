import docker
import os, sys, time, subprocess, yaml, shutil
import logging
import dockermix

class ContainerMix:
  def __init__(self, conf_file=None, environment=None):
    self._setupLogging()
    self.containers = {}
    
    if (environment):
      self.load(environment)
    else:
      if (not conf_file.startswith('/')):
        conf_file = os.path.join(os.path.dirname(sys.argv[0]), conf_file)

      data = open(conf_file, 'r')
      self.config = yaml.load(data)      

  def get(self, container):
    return self.containers[container]

  def build(self):
    for container in self.config['containers']:
      base = self.config['containers'][container]['base']
      ports = None
      if ('ports' in self.config['containers'][container]):
        ports = self.config['containers'][container]['ports']
        
      #BaseContainer(base)
      self.log.info('Building container: %s using base template %s', container, base)
      build = Context(container, base_image=base, ports=ports)
      build.build()

      self.containers[container] = build
      
  def destroy(self):
    for container in self.containers:
      self.log.info('Destroying container: %s', container)      
      self.containers[container].destroy()     
 
  def load(self, filename='envrionment.yml'):
    self.log.info('Loading environment from: %s', filename)      
    
    with open(filename, 'r') as input_file:
      environment = yaml.load(input_file)

      for container in environment['containers']:
        self.containers[container] = Container(container, build_tag=environment['containers'][container]['build_tag'], 
          container_id=environment['containers'][container]['container_id'], image_id=environment['containers'][container]['image_id'])
    
  def save(self, filename='environment.yml'):
    self.log.info('Saving environment state to: %s', filename)      
      
    with open(filename, 'w') as output_file:
      output_file.write(self.dump())

  def dump(self):
    result = {}
    result['containers'] = {}
    for container in self.containers:
      origin = self.containers[container]
      output = result['containers'][container] = {}
      output['image_id'] = str(origin.image_id)
      output['container_id'] = str(origin.container_id)
      output['build_tag'] = str(origin.build_tag)
      
      if (origin.ports):
        output['ports'] = {}
        for port in origin.ports:
          public_port = origin.docker_client.port(origin.container_id, str(port))
          output['ports'][port] = str(public_port)

      str(self.containers[container].container_id)

    # TODO, change the YAML Dumper used here to be safe
    return yaml.dump(result)

  def _setupLogging(self):
    self.log = logging.getLogger('dockermix')
    self.log.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s %(levelname)-10s %(message)s")
    filehandler = logging.FileHandler('dockermix.log', 'w')
    filehandler.setLevel(logging.DEBUG)
    filehandler.setFormatter(formatter)
    self.log.addHandler(filehandler)
  

class Container:
  def __init__(self, name, build_tag=None, container_id=None, image_id=None, base_image=None, minion_config=None, top_state=None, ports=None):
    self.log = logging.getLogger('dockermix')

    self.name = name
    self.container_id=container_id
    self.image_id=image_id
    self.build_tag = build_tag
    if (not build_tag):
      self.build_tag = name + '-' + str(os.getpid())
    
    self.minion_config = minion_config
    self.top_state = top_state
    
    self.docker_client = docker.Client()
    self.ports = ports
    self.base_image = 'ubuntu'
    if (base_image):
      self.base_image = base_image

  def build(self):        
    self._build_container()
    self._start_container()
    self._accept_keys()
    self._verify_minion()
    
  def destroy(self):
    self.docker_client.stop(self.container_id)
    self.docker_client.remove_image(self.build_tag)

  def _build_container(self):
    # Generate the docker build profile
    dockerfile = """FROM %s
    MAINTAINER Kimbro Staken "kstaken@kstaken.com"

    CMD ["salt-minion"]

    RUN echo %s > /etc/salt/minion
    """

    # master ip here probably needs to be dynamic
    minionconfig = '\"master: 172.16.42.1\\nid: %s\"' % self.build_tag
    
    self.log.info("Building container with minionconfig: %s", minionconfig)
    # Build the container
    result = self.docker_client.build((dockerfile % (self.base_image, minionconfig)).split('\n'))
    self.image_id = result[0]
    
    # Tag the container with the name and process id
    self.docker_client.tag(self.image_id, self.build_tag)
    self.log.info('Container registered with tag: %s', self.build_tag)      

  def _start_container(self):
    # Start the container
    self.container_id = self.docker_client.create_container(self.image_id, 'salt-minion', 
      detach=True, ports=self.ports, hostname=self.build_tag)['Id']
    self.docker_client.start(self.container_id)
    self.log.info('Container started: %s', self.build_tag)      
      
class BaseContainer:
  def __init__(self, container_name):
    self.log = logging.getLogger('dockermix')
    self.log.info('Building base container: %s - This may take a while', container_name)      
    
    template = os.path.join(os.path.dirname(dockermix.__file__), 'docker', container_name + '.docker')
    self.dockerfile = open(template, 'r').readlines()
    self.docker_client = docker.Client()
    self.container_name = container_name
    
    self.build()

  def build(self):
    # Build the container
    result = self.docker_client.build(self.dockerfile)
    self.image_id = result[0]

    # Tag the container with the name
    self.docker_client.tag(self.image_id, self.container_name)
    self.log.info('Base container registered with tag: %s', self.container_name)      

  def destroy(self):
    self.log.info('Cleaning up base container: %s', self.container_name)      
    self.docker_client.remove_image(self.container_name)
