dockermix
============

A quick and simple tool to start/destroy multiple docker containers based on a simple YAML specification.

Dependencies
=============

docker-py: https://github.com/dotcloud/docker-py

Installation
============

    python setup.py install

Configuration File Format
=========================

YAML format basically maps to the docker-py api. Here's an example format:

    containers:
      test_server_1: 
        base_image: ubuntu
        ports: 
          - '8080' 
        command: 'ps aux' 
        hostname: test_server_1 
        user: root
        detach: true
        stdin_open: true
        tty: true
        mem_limit: 2560000
        environment: 
          - ENV_VAR=testing
        dns: 
          - 8.8.8.8
          - 8.8.4.4
        volumes: 
          /var/testing: {}
              
        #volumes_from: container_id
        #dockerfile:
        #  body: {}
        #  tag: {}
        #  commit: {}
      test_server_2: 
        base_image: ubuntu
        command: 'ls -l'
        hostname: test_server_2

API
===