#########################################################################
# HOUSE TABLE
#########################################################################
db.define_table(
 'house',
 Field('Name', 'string', default=''),
 Field('Address', 'string', default=''),
 Field('City', 'string', default=''),
 Field('State', 'string', default=''),
 Field('ZIP', 'integer', default='0'),
 Field('Members', 'list:reference auth_user'),
 format = '%(name)s House',
 singular = 'House',
 plural = 'Houses',
)

db.house.Name.requires = db.house.Members.requires = IS_NOT_EMPTY()

#########################################################################
# TRANSACTION TABLE
#########################################################################
db.define_table(
 'transaction_table',
 Field('author', 'reference auth_user'),
 Field('total', 'double', default='0.0'),
 Field('title', 'string', default='New Transaction'),
)

#db.transaction_table.author.requires = IS_NOT_EMPTY()


#########################################################################
# PAYMENT TABLE
#########################################################################
db.define_table(
 'payment',
 Field('transaction_n', 'reference  transaction_table'),
 Field('payer', 'reference  auth_user'),
 Field('amount', 'double', default='0.0'),
 Field('receiver', 'reference  auth_user'),
 Field('state', 'string', default='null'),
)

db.payment.transaction_n.requires = db.payment.payer.requires = IS_NOT_EMPTY()
db.payment.receiver.requires = IS_NOT_EMPTY()
