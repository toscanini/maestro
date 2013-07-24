import docker
import exceptions, utils
import StringIO
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

    return True

  # Launches an instance of the template in a new container
  def launch(self, command=None):

    pass

  # Generate the meastro specific ID for this template.
  def _mid(self):
    return self.service + "." + self.name + ":" + self.version

  def _build(self, dockerfile=None, url=None):
    self.log.info('Building container: %s', self._mid())      

    if (dockerfile):
      result = self.docker_client.build(fileobj=StringIO.StringIO(dockerfile))
    elif (url):
      print "BUilding"
      result = self.docker_client.build(path=url)
    else:
      raise exceptions.TemplateError("Can't build if no buildspec is provided: " + self.name)
    print result
    if result[0] == None:
      raise exceptions.TemplateError("Build failed for template: " + self.name)
    
    # TODO: figure out what to do with the result of this execution
    #self.log.info('Result of docker build:', result)      

    self.config['image_id'] = result[0]
    
    # Tag the container with the name and process id
    self.docker_client.tag(self.config['image_id'], self.service + "." + self.name, tag=self.version)
    
    # TODO: make sure this is always appropriate to do as there may be cases where tagging a build as latest isn't desired.
    self.docker_client.tag(self.config['image_id'], self.service + "." + self.name, tag='latest')
    
    self.log.info('Container registered with tag: %s', self._mid())      
