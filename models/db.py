# -*- coding: utf-8 -*-

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    #db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
    db = DAL('sqlite://storage.sqlite')
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore+ndb')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []

## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################

from gluon.tools import Auth, Service, PluginManager

auth = Auth(db)
service = Service()
plugins = PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' if request.is_local else 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.janrain_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)


#########################################################################
# PERSON TABLE
#########################################################################
db.define_table(
 'person',
 Field('first_name', default=''),
 Field('last_name', default=''),
 Field('email', unique=True),
 Field('password', 'password', length=512, readable=False, label='Password'),
 Field('registration_key', length=512, writable=False, readable=False, default=''),
 Field('reset_password_key', length=512, writable=False, readable=False, default=''),
 Field('registration_id', length=512, writable=False, readable=False, default=''),
 format = '%(first_name)s %(last_name)s',
 singular = 'Person',
 plural = 'Persons',
)

# Customer table requires a name and valid email (if provided)
db.person.first_name.requires = IS_NOT_EMPTY()
db.person.last_name.requires = IS_NOT_EMPTY()
db.person.email.requires = [IS_EMPTY_OR(IS_EMAIL()), IS_NOT_IN_DB(db, 'person.email')]

# Settings for authentication using customer database
custom_auth_table = db['person']

custom_auth_table.first_name.requires = IS_NOT_EMPTY(error_message = auth.messages.is_empty)
custom_auth_table.last_name.requires = IS_NOT_EMPTY(error_message = auth.messages.is_empty)
custom_auth_table.email.requires = IS_NOT_IN_DB(db, custom_auth_table.email)
custom_auth_table.password.requires = [IS_STRONG(), CRYPT()]
custom_auth_table.email.requires = [ IS_EMAIL(error_message = auth.messages.invalid_email), IS_NOT_IN_DB(db, custom_auth_table.email)]

auth.settings.table_user = custom_auth_table
auth.settings.table_user_name = 'person'
auth.settings.table_group_name = 'person'
auth.settings.table_membership_name = 'person_membership'
auth.settings.table_permission_name = 'person_permission'
auth.settings.table_event_name = 'person_event'
auth.settings.login_userfield = 'email'
auth.define_tables(username=False)


#########################################################################
# TRANSACTION TABLE
#########################################################################
db.define_table(
 'transaction_table',
 Field('author', db.person),
 Field('total', 'double', default='0.0'),
)

db.transaction_table.author.requires = IS_NOT_EMPTY()


#########################################################################
# PAYMENT TABLE
#########################################################################
db.define_table(
 'payment',
 Field('transaction_n', db.transaction_table),
 Field('payer', db.person),
 Field('amount', 'double', default='0.0'),
 Field('receiver', db.person),
)

db.payment.transaction_n.requires = db.payment.payer.requires = IS_NOT_EMPTY()
db.payment.receiver.requires = IS_NOT_EMPTY()
