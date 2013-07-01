import sys, os
import cmdln
from dockermix import dockermix

class DockermixCli(cmdln.Cmdln):
    """Usage:
        dockermix SUBCOMMAND [ARGS...]
        dockermix help SUBCOMMAND

    Dockermix provides a command to manage multiple Docker containers
    from a single configuration.

    ${command_list}
    ${help_list}
    """
    name = "dockermix"

    def __init__(self, *args, **kwargs):
      cmdln.Cmdln.__init__(self, *args, **kwargs)
      cmdln.Cmdln.do_help.aliases.append("h")

    @cmdln.option("-f", "--dockermix_file",
                  help='path to the dockermix file to use')
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
      config = opts.dockermix_file
      if not config:
        config = os.path.join(os.getcwd(), 'dockermix.yml')

      if not config.startswith('/'):
        config = os.path.join(os.getcwd(), config)

      if not os.path.exists(config):
        print "No dockermix configuration found {0}".format(config)
        exit(1)
      
      containers = dockermix.ContainerMix(config)
      containers.build()
      if (not opts.no_save):
        environment = opts.environment_file
        if not environment:  
          environment = os.path.join(os.getcwd(), 'environment.yml')

        containers.save(environment)

    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    def do_start(self, subcmd, opts, *args):
      """Start a set of Docker containers that had been previously stopped. Container state is defined in an environment file. 

        usage:
            start
        
        ${cmd_option_list}
      """
      environment = self._verify_environment(opts.environment_file)
      
      containers = dockermix.ContainerMix(environment=environment)
      containers.start() 

    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    def do_stop(self, subcmd, opts, *args):
      """Stop a set of Docker containers as defined in an environment file. 

        usage:
            stop
        
        ${cmd_option_list}
      """
      environment = self._verify_environment(opts.environment_file)
      
      containers = dockermix.ContainerMix(environment=environment)
      containers.stop() 

    @cmdln.option("-e", "--environment_file",
                  help='path to the environment file to use to save the state of running containers')
    def do_destroy(self, subcmd, opts, *args):
      """Stop and destroy a set of Docker containers as defined in an environment file. 

        usage:
            stop
        
        ${cmd_option_list}
      """
      environment = self._verify_environment(opts.environment_file)
      
      containers = dockermix.ContainerMix(environment=environment)
      containers.destroy() 

    def _verify_environment(self, environment):
      if not environment:  
        environment = os.path.join(os.getcwd(), 'environment.yml')
      
      if not os.path.exists(environment):
        print "Could not locate the environments file {0}".format(environment)
        exit(1)

      return environment
    