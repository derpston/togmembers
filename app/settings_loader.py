import yaml
import os

APPNAME = "togmembers"

# Places to search for configuration, in order. Defaults, system-wide, user-specific.
config_paths = [
      "conf/default.yaml"
   ,  "/etc/%s.yaml" % APPNAME
   ,  os.path.join(os.environ.get("HOME", "/"), "%s.yaml" % APPNAME)
   ]

for path in os.environ.get('EXTRA_CONFIG_PATHS', '').split(" "):
   config_paths.append(path)

def loadconfig(path):
   global_vars = globals()
   try:
      config = open(path).read()

      for key, value in yaml.load(config).iteritems():
         global_vars[key] = value
         
   except IOError, ex:
      if ex.errno != 2: # No such file/dir
         raise

for path in config_paths:
   loadconfig(path)

