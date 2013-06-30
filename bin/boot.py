#!/usr/bin/env python

import sys
sys.path.append('.')
from dockermix import dockermix

containers = dockermix.ContainerMix('../dockermix.yml')
containers.build()
containers.save()
