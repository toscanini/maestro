import sys
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

    def do_start(self, subcmd, opts, *args):
      """Start a set of Docker containers

        usage:
            start 
        
        ${cmd_option_list}
      """
      print "Got start"

      containers = dockermix.ContainerMix('../dockermix.yml')
      containers.build()
      containers.save()
