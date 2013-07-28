import sys, os
import cmdln
from . import service

class MaestroCli(cmdln.Cmdln):
    """Usage:
        maestro SUBCOMMAND [ARGS...]
        maestro help SUBCOMMAND

    Maestro provides a command to manage multiple Docker containers
    from a single configuration.

    ${command_list}
    ${help_list}
    """
    name = "maestro"

    def __init__(self, *args, **kwargs):
      cmdln.Cmdln.__init__(self, *args, **kwargs)
      cmdln.Cmdln.do_help.aliases.append("h")

    @cmdln.option("-f", "--maestro_file",
                  help='path to the maestro file to use')
    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    @cmdln.option("-n", "--no_save", action='store_true',
                  help='do not save the state to an environment file')
    def do_build(self, subcmd, opts, *args):
      """Setup and start a set of Docker containers.

        usage:
            build
        
        ${cmd_option_list}
      """
      config = opts.maestro_file
      if not config:
        config = os.path.join(os.getcwd(), 'maestro.yml')

      if not config.startswith('/'):
        config = os.path.join(os.getcwd(), config)

      if not os.path.exists(config):
        sys.stderr.write("No maestro configuration found {0}\n".format(config))
        exit(1)
      
      containers = service.Service(config)
      containers.build()
      if (not opts.no_save):
        environment = opts.environment_file
        if not environment:  
          environment = os.path.join(os.getcwd(), 'environment.yml')

        containers.save(environment)

      print "Launched."


    def do_deploy(self, subcmd, opts, *args):
      """Setup and start a set of Docker containers from a git repo.

        usage:
            deploy git_repo_url
        
        ${cmd_option_list}
      """
      config = opts.maestro_file
      if not config:
        config = os.path.join(os.getcwd(), 'maestro.yml')

      if not config.startswith('/'):
        config = os.path.join(os.getcwd(), config)

      if not os.path.exists(config):
        sys.stderr.write("No maestro configuration found {0}\n".format(config))
        exit(1)
      
      containers = service.Service(config)
      containers.build()
      if (not opts.no_save):
        environment = opts.environment_file
        if not environment:  
          environment = os.path.join(os.getcwd(), 'environment.yml')

        containers.save(environment)

      print "Environment launched."    

    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    def do_start(self, subcmd, opts, *args):
      """Start a set of Docker containers that had been previously stopped. Container state is defined in an environment file. 

        usage:
            start [container_name]
        
        ${cmd_option_list}
      """
      container = None
      if (len(sys.argv) > 2):
        container = sys.argv[2]

      environment = self._verify_environment(opts.environment_file)
      
      containers = service.Service(environment=environment)
      if containers.start(container):
        containers.save(environment)
        print "Started."

    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    def do_stop(self, subcmd, opts, *args):
      """Stop a set of Docker containers as defined in an environment file. 

        usage:
            stop [container_name]
        
        ${cmd_option_list}
      """
      container = None
      if (len(sys.argv) > 2):
        container = sys.argv[2]

      environment = self._verify_environment(opts.environment_file)
      
      containers = service.Service(environment=environment)
      if containers.stop(container):
        containers.save(environment)
        print "Stopped."

    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    def do_restart(self, subcmd, opts, *args):
      """Restart a set of containers as defined in an environment file. 

        usage:
            restart [container_name]
        
        ${cmd_option_list}
      """
      self.do_stop('stop', opts, args)
      self.do_start('start', opts, args)

    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    def do_destroy(self, subcmd, opts, *args):
      """Stop and destroy a set of Docker containers as defined in an environment file. 

        usage:
            destroy
        
        ${cmd_option_list}
      """
      environment = self._verify_environment(opts.environment_file)
      
      containers = service.Service(environment=environment)
      if containers.destroy():
        containers.save(environment)
        print "Destroyed."
 
    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    def do_run(self, subcmd, opts, *args):
      """Start a set of Docker containers that had been previously stopped. Container state is defined in an environment file. 

        usage:
            run container_name [commandline]
        
        ${cmd_option_list}
      """
      container = None
      if (len(sys.argv) <= 2):
        sys.stderr.write("Error: Container name must be provided\n")
        exit(1)

      environment = self._verify_environment(opts.environment_file)
      
      template = sys.argv[2]
      commandline = sys.argv[3:]
      
      containers = service.Service(environment=environment)
      containers.run(template, commandline) 
      containers.save(environment)

      print "Running a new instance of " + template     

    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    def do_ps(self, subcmd, opts, *args):
      """Show the status of a set of containers as defined in an environment file. 

        usage:
            ps
        
        ${cmd_option_list}
      """
      environment = self._verify_environment(opts.environment_file)
      
      containers = service.Service(environment=environment)
      print containers.ps() 

    def _verify_environment(self, environment):
      if not environment:  
        environment = os.path.join(os.getcwd(), 'environment.yml')
      
      if not os.path.exists(environment):
        sys.stderr.write("Could not locate the environments file {0}\n".format(environment))
        exit(1)

      return environment
    