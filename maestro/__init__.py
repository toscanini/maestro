__all__ = ["container", "service", "utils", "cli"]


LOCAL_ENV=".maestro"
GLOBAL_ENV="/var/lib/maestro"

# Maintain a list of environments on disk
  # By default an environemnt is created in .maestro unless -g is specified to make it global.
  # Global enviroments are stored in /var/lib/maestro. Permission setting will come into play for this. 
  # The environment directory contains:
    # environment.yml capturing the state of the running system
    # settings.yml capturing the user configuration settings
    # maestro.yml ?? The original environment description used to create the environment

# Initialize a new environment
def init_environment(name, description="maestro.yml", system=False):
  # Verify the environment doesn't already exist
    # Check for both local and system environments that may conflict

  if (system):
    # Create a system wide environment
    pass
  else:
    # We're just creating an environment that lives relative to the local directory
    pass
  
# retrieve environment
def get_environment(name):
  pass

# list environments
def list_environments():
  # Include the local environment if there is one
  # Include a list of the system environments
  pass
  
def destroy_environment(name):
  pass

