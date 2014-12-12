# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - api is an example of Hypermedia API support and access control
#########################################################################

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html

    if you need a simple wiki simply replace the two lines below with:
    return auth.wiki()
    """
    response.flash = T("Welcome to Divvy!")
    #return dict(message=T('Hello World'))
    #
    # REDIRECT TO HOME (CHANGE IN FUTURE?)
    #return redirect(URL('home'))
    return dict(message=T('Welcome!!'))

@auth.requires_login()
def home():
    return dict(message=T('testing'))

@auth.requires_login()
def new_transaction():
    names = []

    for row in db(db.auth_user).select():
        if row.email != auth.user.email:
            names.append(row.email)

    return dict(names=names)

@auth.requires_login()
def process_transaction():
    #create a new record in the transaction table
    userid = auth.user.id
    transactionid = db.transaction_table.insert(author=userid, total=request.post_vars["total"])
    #from hw3 hints: orderid = db.cust_order.insert(customer=userid, co_date=datime,amount=amount)

    #for each user, create a new payment record in the payment table
    for row in db(db.auth_user).select():
        if (row.email != auth.user.email and request.post_vars["owes_"+row.email] != 0):
            print(request.post_vars["owes_"+row.email])
            db.payment.insert(transaction_n=transactionid, payer=row.id, amount=request.post_vars['owes_'+row.email], receiver=userid)

    return redirect(URL('index'))

@auth.requires_login()
def details_transaction():
    # Fetch transaction entry
    this_transaction = db.transaction_table(request.args(0,cast=int)) or redirect(URL('index'))
    # Fetch payments related to the transaction
    payment_rows = db(request.args(0,cast=int) == db.payment.transaction_n).select(orderby=~db.payment.transaction_n)
    # Return transaction ID
    trans_id = request.args(0,cast=int)
    # Boolean to know if a payer or receiver viewing
    is_payer = True
    id_payer = 0
    if this_transaction.author == auth.user.id:
        is_payer = False
        id_payer = auth.user.id
    return dict(trans=this_transaction, rows=payment_rows, trans_id=trans_id, is_payer=is_payer, id_payer=id_payer)

@auth.requires_login()
def mark_as_paid():
    db.payment[request.args(0,cast=int)] = dict(state="paid")
    return redirect(URL('index'))

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_login()
def api():
    """
    this is example of API with access control
    WEB2PY provides Hypermedia API (Collection+JSON) Experimental
    """
    from gluon.contrib.hypermedia import Collection
    rules = {
        '<tablename>': {'GET':{},'POST':{},'PUT':{},'DELETE':{}},
        }
    return Collection(db).process(request,response,rules)
