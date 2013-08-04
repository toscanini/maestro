import docker

class PyBackend:
  def __init__(self):
    self.docker_client = docker.Client()

  def create_container(self, image_id, config):
    return self._start_container(image_id, config, False) 

  def run_container(self, image_id, config):
    return self._start_container(image_id, config)

  def start_container(self, container_id):
    self.docker_client.start(container_id)
  
  def stop_container(self, container_id, timeout=10):
    self.docker_client.stop(container_id, timeout=timeout)
    
  def remove_container(self, container_id, timeout=None):
    self.stop_container(timeout)
    self.docker_client.remove_container(container_id)    

  def inspect_container(self, container_id):
    self.docker_client.inspect_container(container_id)
  
  def get_ip_address(self, container_id):
    state = self.docker_client.inspect_container(container_id)    
    return state['NetworkSettings']['IPAddress']

  def _start_container(self, image_id, config, start=True):
    # Start the container
    container_id = self.docker_client.create_container(image_id, **config)['Id']
    
    if (start):
      self.start_container(container_id)

    return container_id