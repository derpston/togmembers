# stdlib
import functools
import logging

# Third party
import jinja2
import ldap
import ldap.modlist

# This will be populated by togmembers.py after the configs have been loaded.
config = {}

# This will cache an LDAP client object after the first time we need one.
# XXX Not used anymore, using per-user credentials.
ldapclient = None

# Holds uid => ldap client objects
cached_ldap_clients = {}

def page(func):
   @functools.wraps(func)
   def wrapper(*args, **kwargs):
      template_env = jinja2.Environment(loader = jinja2.FileSystemLoader('templates'))
      try:
         template = template_env.get_template('%s.html' % func.__name__)
      except jinja2.TemplateNotFound:
         template = None
      content = func(template, *args, **kwargs)
      return content
   return wrapper

def get_ldap_client(dn, password):
   global ldapclient
   try:
      # Try to return a cached ldapclient object.
      assert ldapclient is not None
      return ldapclient
   except AssertionError:
      # This is the first time we're connecting to LDAP.

      protocol = "ldaps" if config['LDAP_TLS_ENABLED'] else "ldap"
      uri = "%s://%s:%d" % (protocol, config['LDAP_HOST'], config['LDAP_PORT'])
      ldapclient = ldap.initialize(uri)
      ldapclient.bind(dn, password)#config['LDAP_BIND_DN'], config['LDAP_BIND_PASSWORD'])

      return ldapclient

def ldap_search(bind_uid, **kwargs):
   ldapclient = get_uid_ldap_client(bind_uid)

   # Pick the attrs argument out, if it exists, because it needs to be
   # passed to search_s separately from filterstr.
   try:
      attrs = kwargs['attrs']
      del kwargs['attrs']
   except KeyError:
      attrs = None

   # All remaining keyword arguments are treated as filters.
   filters = []
   for key, value in kwargs.iteritems():
      filters.append("%s=%s" % (key, value))
   
   if len(filters):
      filterstr = "(%s)" % ",".join(filters)
   else:
      # If no filters are provided, match everything.
      filterstr = "(objectClass=*)"

   logging.debug("Searching LDAP with filter '%s'", filterstr)

   response = ldapclient.search_s(config['LDAP_BASE'], ldap.SCOPE_SUBTREE, filterstr, attrs)

   results = {}
   for dn, attrs in response:
      results[dn] = attrs

   return results

def validate_user(username, password):
   """Given a username and password, returns a boolean indicating whether this matches a user."""
   get_uid_ldap_client(username, password)

   results = ldap_search(username, uid = username, attrs = ['userPassword'])

   assert len(results) < 2, "Expected only one object to match uid=%s, got %d objects." % (username, len(results))

   if len(results) == 0:
      return False

   result = results.values()[0]
   
   return result['userPassword'][0] == hash_user_password(password)

def hash_user_password(password):
   # We suck, there's no password hashing yet!
   return password

def parse_dn(dn):
   """Returns a dict representing all the fields in an LDAP Distinguished Name."""
   fields = dn.split(",")
   return dict([field.split("=") for field in fields])

def change_password(uid, oldpassword, password):
   ldapclient = get_uid_ldap_client(uid)

   if ldapclient:
      old = {'userPassword': [str(oldpassword)]}
      new = {'userPassword': [str(password)]}
      ldif = ldap.modlist.modifyModlist(old, new)

      state = ldapclient.modify_s("uid=%s,ou=people,O=TOG" % uid, ldif)
      
      return True
   else:
      return False

def get_uid_ldap_client(uid, password = None):
   global cached_ldap_clients
   print "looking up ldap client for", uid, password
   print cached_ldap_clients
   if password:
      # Create an LDAP connection object for this user.
      ldapclient = get_ldap_client("uid=%s,ou=people,O=TOG" % uid, password)
      
      print "made new ldap connection", uid, password, ldapclient

      # Cache this connection object so other requests can use it.
      cached_ldap_clients[uid] = ldapclient
   else:
      # Look for a cached LDAP client object for this user.
      try:
         return cached_ldap_clients[uid]
      except KeyError:
         return None
