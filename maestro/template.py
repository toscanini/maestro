import exceptions, utils, container, py_backend
import StringIO, copy, logging, sys
from requests.exceptions import HTTPError

class Template:
  def __init__(self, name, config, service, version):
    self.name     = name    
    self.config   = config
    self.service  = service
    self.version  = version
    self.log      = logging.getLogger('maestro')

    self.backend = py_backend.PyBackend()

  def build(self):
    # If there is a docker file or url hand off to Docker builder    
    if 'buildspec' in self.config:
      if self.config['buildspec']:
        if 'dockerfile' in self.config['buildspec']:
          self._build(dockerfile=self.config['buildspec']['dockerfile'])
        elif 'url' in self.config['buildspec']:
          self._build(url=self.config['buildspec']['url'])
      else:
        raise exceptions.TemplateError("Template: " + self.name + " Buildspec specified but no dockerfile or url found.")
    else:
      # verify the base image and pull it if necessary
      try:
        base = self.config['base_image']    
        self.backend.inspect_image(base)
      except HTTPError:
        # Attempt to pull the image.
        self.log.info('Attempting to pull base: %s', base)
        result = self.backend.pull_image(base)
        if 'error' in result:
          self.log.error('No base image could be pulled under the name: %s', base)      
          raise exceptions.TemplateError("No base image could be pulled under the name: " + base)
      except KeyError:
        raise exceptions.TemplateError("Template: " + self.name + "No base image specified.")

      # There doesn't seem to be a way to currently remove tags so we'll generate a new image.
      # More consistent for all cases this way too but it does feel kinda wrong.
      dockerfile = """
      FROM %s
      MAINTAINER %s
      """ % (base, self._mid())
      self._build(dockerfile=dockerfile)

    return True

  # Launches an instance of the template in a new container
  def instantiate(self, name, command=None):    
    config = copy.deepcopy(self.config['config'])

    # Setup bind mounts to the host system    
    bind_mounts = {}
    if 'mounts' in self.config:
      bind_mounts = self.config['mounts']
      for src, dest in self.config['mounts'].items():
        if 'volumes' not in config:          
          config['volumes'] = {}
        
        config['volumes'][dest] = {}

    if command:
      config['command'] = " ".join(command)
    print config['command']
    return container.Container(name, {'template': self.name, 'image_id': self.config['image_id']}, config, mounts=bind_mounts)

  def destroy(self):
    # If there is an image_id then we need to destroy the image.
    if 'image_id' in self.config:      
      self.backend.remove_image(self.config['image_id'])
    
  def full_name(self):
    return self.service + "." + self.name

  def _base_id(self, base):
    tag = 'latest'
    if ':' in base:
      base, tag = base.split(':')
    
    result = self.backend.images(name=base)
    for image in result:
      if image['Tag'] == tag:
        return image['Id']

    return None

  # Generate the meastro specific ID for this template.
  def _mid(self):
    return self.service + "." + self.name + ":" + self.version

  def _build(self, dockerfile=None, url=None):
    self.log.info('Building container: %s', self._mid())      

    if (dockerfile):
      result = self.backend.build_image(fileobj=StringIO.StringIO(dockerfile))
    elif (url):
      result = self.backend.build_image(path=url)
    else:
      raise exceptions.TemplateError("Can't build if no buildspec is provided: " + self.name)
    
    if result[0] == None:
      # TODO: figure out what to do with the result of this execution
      print result
      raise exceptions.TemplateError("Build failed for template: " + self.name)

    self.config['image_id'] = result[0]
    
    self._tag(self.config['image_id'])

    self.log.info('Container registered with tag: %s', self._mid())   

  def _tag(self, image_id):
    # Tag the container with the name and process id
    self.backend.tag_image(image_id, self.service + "." + self.name, tag=self.version)
    
    # TODO: make sure this is always appropriate to do as there may be cases where tagging a build as latest isn't desired.
    self.backend.tag_image(image_id, self.service + "." + self.name, tag='latest')
     
