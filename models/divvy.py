db = DAL('sqlite://storage.sqlite')

#########################################################################
# AUTH TABLE
#########################################################################
auth = Auth(db)
auth.define_tables(username=False,signature=False)


#########################################################################
# TRANSACTION TABLE
#########################################################################
db.define_table(
 'transaction_table',
 Field('author', db.auth_user),
 Field('total', 'double', default='0.0'),
)

db.transaction_table.author.requires = IS_NOT_EMPTY()


#########################################################################
# PAYMENT TABLE
#########################################################################
db.define_table(
 'payment',
 Field('transaction_n', db.transaction_table),
 Field('payer', db.auth_user),
 Field('amount', 'double', default='0.0'),
 Field('receiver', db.auth_user),
)

db.payment.transaction_n.requires = db.payment.payer.requires = IS_NOT_EMPTY()
db.payment.receiver.requires = IS_NOT_EMPTY()
