#!/usr/bin/env python

import sys
#sys.path.append('../salt-test-runner')
from dockermix import dockermix

containers = dockermix.ContainerMix(environment='environment.yml')
containers.destroy()
