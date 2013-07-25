import docker
import exceptions, utils, container
import StringIO, copy
from requests.exceptions import HTTPError


class Template:
  def __init__(self, name, config, service, version):
    self.name     = name    
    self.config   = config
    self.service  = service
    self.version  = version
    self.log      = utils.setupLogging()

    self.docker_client = docker.Client()

  def build(self):
    # verify the base image and pull it if necessary
    try:
      base = self.config['base_image']    
      self.docker_client.inspect_image(base)
    except HTTPError:
      # Attempt to pull the image.
      self.log.info('Attempting to pull base: %s', base)
      result = self.docker_client.pull(base)
      if 'error' in result:
        self.log.error('No base image could be pulled under the name: %s', base)      
        raise exceptions.TemplateError("No base image could be pulled under the name: " + base)
    except KeyError:
      raise exceptions.TemplateError("Template: " + self.name + "No base image specified.")

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
      # We're just operating off the base so add our tags to that image.
        # Well there doesn't seem to be a way to currently remove tags so we'll generate a new image.
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
    if command:
      config['command'] = command

    return container.Container(name, {'image_id': self.config['image_id']}, config)

  def destroy(self):
    # If there is an image_id then we need to destroy the image.
    if 'image_id' in self.config:      
      self.docker_client.remove_image(self.config['image_id'])
    
  def full_name(self):
    return self.service + "." + self.name

  def _base_id(self, base):
    tag = 'latest'
    if ':' in base:
      base, tag = base.split(':')
    
    result = self.docker_client.images(name=base)
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
      result = self.docker_client.build(fileobj=StringIO.StringIO(dockerfile))
    elif (url):
      result = self.docker_client.build(path=url)
    else:
      raise exceptions.TemplateError("Can't build if no buildspec is provided: " + self.name)
    
    if result[0] == None:
      raise exceptions.TemplateError("Build failed for template: " + self.name)
    
    # TODO: figure out what to do with the result of this execution
    #self.log.info('Result of docker build:', str(result))      

    self.config['image_id'] = result[0]
    
    self._tag(self.config['image_id'])

    self.log.info('Container registered with tag: %s', self._mid())   

  def _tag(self, image_id):
    # Tag the container with the name and process id
    self.docker_client.tag(image_id, self.service + "." + self.name, tag=self.version)
    
    # TODO: make sure this is always appropriate to do as there may be cases where tagging a build as latest isn't desired.
    self.docker_client.tag(image_id, self.service + "." + self.name, tag='latest')
     
