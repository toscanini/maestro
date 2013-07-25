import logging
import os, sys, time, socket
import docker

def setupLogging():
  log = logging.getLogger('maestro')
  log.setLevel(logging.DEBUG)

  formatter = logging.Formatter("%(asctime)s %(levelname)-10s %(message)s")
  filehandler = logging.FileHandler('maestro.log', 'w')
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

def findImage(name, tag="latest"):
  result =  docker.Client().images(name=name)

  for image in result:
    if image['Tag'] == tag:
      return image['Id']
  return None