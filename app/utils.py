# stdlib
import functools
import logging

# Third party
import jinja2
import ldap

# This will be populated by togmembers.py after the configs have been loaded.
config = {}

# This will cache an LDAP client object after the first time we need one.
ldapclient = None

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

def get_ldap_client():
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
      ldapclient.bind(config['LDAP_BIND_DN'], config['LDAP_BIND_PASSWORD'])

      return ldapclient

def ldap_search(**kwargs):
   ldapclient = get_ldap_client()

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

   results = ldap_search(uid = username, attrs = ['userPassword'])

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



