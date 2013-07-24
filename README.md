Maestro
============

A command line tool for Container orchestration and management in multi-container docker environments. Container sets are defined in a simple YAML format that mirrors the options available in the Docker API. The intention is to be able to easily launch, orchestrate and destroy complex multi-node envionments for testing and development.


Status
======

Early development. Certainly lots of bugs and not quite useful yet but getting close. The configuration format in particular is changing heavily.

Note: this project used to be called DockerMix.

Features
========

- Build/start/stop/destroy multi-container docker environments via simple commands
- Declarative YAML format to specify container configurations for the environment
- Easily launch multiple instances of the same container for testing cluster operations
- Specify dependencies between containers so they start in order and wait for services to become available
- Automatically configure dependent containers to know where to locate services from other containers in the same environment
- ... Much more to come

Dependencies
=============

- Docker: https://github.com/dotcloud/docker
- docker-py: https://github.com/dotcloud/docker-py
- Python pip package manager

Installation
============

Install Docker as described here: http://www.docker.io/gettingstarted/

Then:
```
    sudo apt-get install -y python-pip
    git clone https://github.com/toscanini/maestro.git
    cd maestro
    sudo pip install -r requirements.txt 
    sudo python setup.py install
```

Configuration File Format
=========================

YAML format basically maps to the docker-py api. 

`base_image` is the Docker container to use to run the command. It must already exist on the system and won't be pulled automatically.

`base_image` and `command` are the only required options. 

You can use `require` to specify dependencies between services. The start order will be adjusted and any container that requires a port on a another container will wait for that port to become available before starting.

Here's an example yaml file:

```
  containers:
    test_server_1:
      base_image: ubuntu
      config:
        ports: 
          - '8080' 
        command: '/bin/bash -c "apt-get install netcat ; nc -l 8080 -k"' 
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
              
    test_server_2: 
      base_image: ubuntu
      config:
        command: 'ls -l'
      require
        test_server_1: 
          port: '8080' 
```

**Note:** *Command is required by the Docker Python api and having to specify it here can cause problems with images that pre-define entrypoints and commands.*

**Note:** *the syntax for volumes is not fully specified and bind mounts are not currently supported.*

**Note:** *There is basic support for embedding dockerfiles in the specification but the details of how that works is going to change.*

Command Line Tools
===

The command line tool is called `maestro` and initial enironments are defined in `maestro.yml`. If there is a `maestro.yml` in the current directory it will be automatically used otherwise the `-f` option can be used to specify the location of the file.

The environment state will be saved to a file named `environment.yml` and commands that manipulate existing environments will look for an `environment.yml` in the current directory or it can be specified by the `-e` option.

`maestro build`

Setup a new environment using a `maestro.yml` specification.

`maestro start`

Start an existing environment that had been previously stopped and saved in `environment.yml`

`maestro stop`

Stop all containers in an environment and save the state to `environment.yml`

`maestro destroy`

Destroy all containers defined in an environment. Once destroyed the containers can not be recoved.

`maestro status`

Show the status of the containers in an environment.

Roadmap
====

- Bootstrap installer
- Add the ability to share configuration data between containers
- ~~Explicitly specify startup order and dependencies~~
- More powerful Docker Builder support ~~(currently docker-py reimplements Docker Builder and it out of sync with the server implementation)~~
- Add automatic pulling of base images
- Make it easier to run the full test suite
- Add external dependencies
- ...