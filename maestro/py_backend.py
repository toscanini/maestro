import docker

class PyBackend:
  def __init__(self):
    self.docker_client = docker.Client()

  ## Container management

  def create_container(self, image_id, config):
    return self._start_container(image_id, config, False) 

  def run_container(self, image_id, config):
    return self._start_container(image_id, config)

  def start_container(self, container_id, mounts=None):
    self.docker_client.start(container_id, binds=mounts)
  
  def stop_container(self, container_id, timeout=10):
    self.docker_client.stop(container_id, timeout=timeout)
    
  def remove_container(self, container_id, timeout=None):
    self.stop_container(timeout)
    self.docker_client.remove_container(container_id)    

  def inspect_container(self, container_id):
    return self.docker_client.inspect_container(container_id)

  def commit_container(self, container_id):
    return self.docker_client.commit(container_id)  
  
  def attach_container(self, container_id):
    return self.docker_client.attach(container_id)  
  
  ## Image management

  def build_image(self, fileobj=None, path=None):
    return self.docker_client.build(path=path, fileobj=fileobj)

  def remove_image(self, image_id):
    self.docker_client.remove_image(image_id)

  def inspect_image(self, image_id):
    return self.docker_client.inspect_image(image_id)

  def images(self, name):
    return self.docker_client.images(name=name)

  def tag_image(self, image_id, name, tag):
    self.docker_client.tag(image_id, name, tag=tag)

  def pull_image(self, name):
    return self.docker_client.pull(name)
  
  ## Helpers

  def get_ip_address(self, container_id):
    state = self.docker_client.inspect_container(container_id)    
    return state['NetworkSettings']['IPAddress']

  def _start_container(self, image_id, config, start=True):
    # Start the container
    container_id = self.docker_client.create_container(image_id, **config)['Id']
    
    if (start):
      self.start_container(container_id)

    return container_id