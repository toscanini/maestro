Maestro
============

Maestro provides the ability to easily launch, orchestrate and manage mulitple Docker containers as single unit. Container sets are defined in a simple YAML format that allows you to define how the containers should be created and to specify relationships between containers. The intention is to make easy to create and use complex multi-node container envionments for testing and development.

This is what it currently looks like to use maestro and deploy a multi-tier node.js/mongodb application. All that's required is a maestro.yml in the root of the repository.

```
$ git clone https://github.com/kstaken/express-todo-example.git
$ cd express-todo-example && maestro build
Building template mongodb
Building template nodejs
Launching instance of template mongodb named mongodb
Starting container mongodb - 144af5ca089d
Starting nodejs: waiting for service mongodb on ip 172.16.0.61 and port 27017
Found service mongodb on ip 172.16.0.61 and port 27017
Launching instance of template nodejs named nodejs
Starting container nodejs - 52be61a3242c
Launched.

$ maestro ps
ID            NODE               COMMAND                                     STATUS     PORTS
144af5ca089d  mongodb            /usr/bin/mongod --config /etc/mongodb.conf  Running
52be61a3242c  nodejs             /usr/bin/node /var/www/app.js               Running    49184->80

$ maestro stop
Stopping container mongodb - 144af5ca089d
Stopping container nodejs - 52be61a3242c
Stopped.

$ maestro start
Starting container mongodb - 144af5ca089d
Starting nodejs: waiting for service mongodb on ip 172.16.0.63 and port 27017
Found service mongodb on ip 172.16.0.63 and port 27017
Starting container nodejs - 52be61a3242c
Started.
```

In this example the app would be accessible on http://localhost:49184/.

Status
======

Early development. It can be useful for testing and development but the feature set and configuration format are changing rapidly.

Note: this project used to be called DockerMix.

Features
========

- Build/start/stop/destroy multi-container docker environments via simple commands
- Specify dependencies between containers so they start in order and wait for services to become available
- Automatically configure dependent containers to know where to locate services from other containers in the same environment
- Easily launch and manage multiple copies of the same environment
- Declarative YAML format to specify container configurations for the environment
- Easily launch multiple instances of the same container for testing cluster operations
- Share data between the host machine and containers running in the environment
- ... Much more to come

Dependencies
=============

- Docker: https://github.com/dotcloud/docker
- docker-py: https://github.com/dotcloud/docker-py
- Python pip package manager

Installation
============

Install Docker as described here: http://www.docker.io/gettingstarted/

Note: Docker 0.5.2 changed from listening on a network socket to listening on a unix socket due to a security issue. At this time, to use Maestro with Docker 0.5.2 you must re-enable the TCP socket in Docker. `/usr/bin/docker -d -H=tcp://127.0.0.1:4243` This is safe if you're running Docker inside a VM dedicated to that purpose but not if you're running Docker directly on your physical computer. This will be fixed in the future.

Then:
```
    sudo apt-get install -y python-pip
    git clone https://github.com/toscanini/maestro.git
    cd maestro
    sudo pip install -r requirements.txt 
    sudo python setup.py install
    docker pull ubuntu
```

Configuration File Format
=========================

**Note:** This format is changing heavily.

The configuration file defines an environment that is made up of multiple templates that can be used to generate containers. The templates can have relationships defined between them to specify start order and Maestro will handle starting instances of the templates in containers in the correct order and then providing environment configuration to the containers.

This example will setup two templates, one for nodejs and one for mongodb. The nodejs template depends on mongodb so that when you start the environment no nodejs containers will be started until a mongdb container is fully up and running.

In this instance the templates are built from repositories stored on Github but there are various ways to set these up.

```
templates:
  nodejs: 
    config:
      command: /usr/bin/node /var/www/app.js
      ports: 
        - '80'  
      environment:
        - PORT=80
    buildspec:
      url: github.com/toscanini/docker-nodejs
    require:
      mongodb: 
        port: '27017'
  mongodb:     
    config:
      command: /usr/bin/mongod --config /etc/mongodb.conf
    buildspec:
      url: github.com/toscanini/docker-mongodb
```

To build and launch an environment you just place this config in a file named `maestro.yml` then run `maestro build`. It will take a few seconds to start as it waits for MongoDB to initialize. Currently the environment state lives in the current directory but that will have more flexibility in the future.

Templates also define a basic docker configuration so that you can pre-define the parameters used on docker run.

`base_image` is the Docker container to use to run the command. It must already exist on the system and won't be pulled automatically.

`base_image` and `command` are the only required options if no `buildspec` is provided. If `buildspec` is provided `base_image` can be omitted

`require` is used to specify dependencies between services. The start order will be adjusted and any container that requires a port on a another container will wait for that port to become available before starting.

`mount` allows you to define bind mounts between a directory on the host and a directory in a container. This allows you to share files between the host and the container. 
    Note: if you define a bind mount on a template then every instance of that template will mount the same host directory.

This example yaml file shows how some of the docker parameters look:

```
  templates:
    test_server_1:
      base_image: ubuntu
      mount:
        /host/path: /container/path
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
```

**Note:** *Command is required by the Docker Python api and having to specify it here can cause problems with images that pre-define entrypoints and commands.*

Command Line Tools
===

The command line tool is called `maestro` and initial enironments are defined in `maestro.yml`. If there is a `maestro.yml` in the current directory it will be automatically used otherwise the `-f` option can be used to specify the location of the file.

The environment state will be saved to a file named `environment.yml` and commands that manipulate existing environments will look for an `environment.yml` in the current directory or it can be specified by the `-e` option.

If you want to create a named environment you can use `-n` to set the name and it will be made a global environment that lives either under ~/.maestro or /var/lib/maestro depending on your setup.

`maestro build`

Setup a new environment using a `maestro.yml` specification.

`maestro start [node_name]`

Start an existing environment that had been previously stopped and saved in `environment.yml`. If `node_name` is provided just that node will be stopped.

`maestro stop [node_name]`

Stop all containers in an environment and save the state to `environment.yml` If `node_name` is provided just that node will be stopped.

`maestro run template [commandline]`

Run a new instance of the template in the environment. *Limited functionality on this currently*

`maestro destroy`

Destroy all containers defined in an environment. Once destroyed the containers can not be recoved.

`maestro ps`

Show the status of the containers in an environment.

Roadmap
====

- Bootstrap installer
- Add the ability to share configuration data between containers. Limited capabilities exist for this currently.
- ~~Explicitly specify startup order and dependencies~~
- ~~More powerful Docker Builder support~~ ~~(currently docker-py reimplements Docker Builder and it out of sync with the server implementation)~~
- ~~Add automatic pulling of base images~~
- Make it easier to run the full test suite
- Add the ability to depend on external services
- ~~Add the ability to have named global environments as well as environments stored in the local directory~~
- More robust support for running and adding containers to an existing environment
- Direct build and instantiation of an environment from a git repo
- ...
