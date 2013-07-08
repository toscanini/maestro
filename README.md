dockermix
============

A quick and simple tool to start/destroy multiple docker containers based on a simple YAML specification.

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
    git clone https://github.com/kstaken/dockermix.git
    cd dockermix
    sudo pip install -r requirements.txt 
    sudo python setup.py install
```

Configuration File Format
=========================

YAML format basically maps to the docker-py api. Here's an example yaml file:

Note: the syntax for volumes is not fully specified and bind mounts are not currently supported.

```
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
            
    test_server_2: 
      base_image: ubuntu
      command: 'ls -l'
      hostname: test_server_2
```

Command Line Tools
===

Initial enironments are defined in `dockermix.yml`. If there is a `dockermix.yml` in the current directory it will be automatically used otherwise the `-f` option can be used to specify the location of the file.

The environment state will be saved to a file named `environment.yml` and commands that manipulate existing environments will look for an `environment.yml` in the current directory or it can be specified by the `-e` option.

dockermix build
----

Setup a new environment using a `dockermix.yml` specification.

dockermix start
----

Start an existing environment that had been previously stopped and save in `environment.yml`

dockermix stop
----

Stop all containers in an environment and save the state to `environment.yml`


dockermix destroy
----

Destroy all containers defined in an environment. Once destroyed the containers can not be recoved.

dockermix status
----

Show the status of the containers in an environment.

Roadmap
====

- Bootstrap installer
- Add the ability to share configuration data between containers
- Explicitly specify startup order and dependencies
- More powerful Docker Builder support (currently docker-py reimplements Docker Builder and it out of sync with the server implementation)
- ...