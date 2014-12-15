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
    return dict(message=T('Welcome!'))

@auth.requires_login()
def home():
    queries=[]
    query = db.transaction_table.id == -1
    payment_rows = db(auth.user.id == db.payment.payer).select(orderby=~db.payment.transaction_n)
    for row in payment_rows:
        queries.append(db.transaction_table.id == row.transaction_n)
    query = reduce(lambda a,b:(a|b),queries)
    t_payer_rows = db(query).select(orderby=~db.transaction_table.id)
    transaction_rows = db(auth.user.id == db.transaction_table.author).select(orderby=~db.transaction_table.id)
    return dict(message=T('test!!'), trans_rows=transaction_rows, pay_rows=t_payer_rows)

@auth.requires_login()
def new_transaction():
    users = {}

    for row in db(db.auth_user).select():
        if row.email != auth.user.email:
            users[row.id]=row.first_name + ' ' + row.last_name
    return dict(users=users)

@auth.requires_login()
def process_transaction():
    #create a new record in the transaction table
    userid = auth.user.id
    transactionid = db.transaction_table.insert(author=userid, total=request.post_vars["total"], title=request.post_vars["item"])

    #for each user, create a new payment record in the payment table
    for row in db(db.auth_user).select():
        if (row.email != auth.user.email and int(request.post_vars["owes_"+str(row.id)]) != 0):
            print(request.post_vars["owes_"+ str(row.id)])
            db.payment.insert(transaction_n=transactionid, payer=row.id, amount=request.post_vars['owes_'+str(row.id)], receiver=userid, state='null')
    return redirect(URL('details_transaction/'+str(transactionid)))

@auth.requires_login()
def details_transaction():
    # Fetch transaction entry
    this_transaction = db.transaction_table(request.args(0,cast=int)) or redirect(URL('home'))
    # Fetch payments related to the transaction
    payment_rows = db(request.args(0,cast=int) == db.payment.transaction_n).select(orderby=~db.payment.transaction_n)
    # Return transaction ID
    trans_id = request.args(0,cast=int)
    # Boolean to know if a payer or receiver viewing
    is_payer = True
    id_payer = auth.user.id
    if this_transaction.author == auth.user.id:
        is_payer = False
    return dict(trans=this_transaction, rows=payment_rows, trans_id=trans_id, is_payer=is_payer, id_payer=id_payer)

@auth.requires_login()
def mark_as_paid():
    db.payment[request.args(0,cast=int)] = dict(state="paid")
    return redirect(URL('details_transaction/'+request.args(1,cast=str)))

@auth.requires_login()
def delete_transaction():
    this_transaction = db.transaction_table(request.args(0,cast=int)) or redirect(URL('home'))
    payment_rows = db(request.args(0,cast=int) == db.payment.transaction_n).select(orderby=~db.payment.transaction_n)
    return dict(trans=this_transaction, rows=payment_rows)

@auth.requires_login()
def delete_t_confirm():
    this_transaction = db.transaction_table(request.args(0,cast=int)) or redirect(URL('home'))
    payment_rows = db(request.args(0,cast=int) == db.payment.transaction_n).select(orderby=~db.payment.transaction_n)
    db(db.transaction_table.id == this_transaction.id).delete()
    for row in payment_rows:
        db(db.payment.id == row.id).delete()
    return redirect(URL('home'))

@auth.requires_login()
def edit_transaction():
    users = {}
    # Get requested transaction
    this_transaction = db.transaction_table(request.args(0,cast=int)) or redirect(URL('home'))
    # Get user's full name
    for row in db(db.auth_user).select():
        if row.email != auth.user.email:
            users[row.id]=row.first_name + ' ' + row.last_name
    return dict(users=users, trans=this_transaction)

@auth.requires_login()
def edit_confirm():
    TRANS_ID = request.post_vars["transaction_id"]
    userid = auth.user.id
    # Edit transaction record
    db.transaction_table[TRANS_ID] = dict(title=request.post_vars["item"])
    db.transaction_table[TRANS_ID] = dict(total=request.post_vars["total"])

    # For each user, check value, and modify/create payment entry
    for row in db(db.auth_user).select():
        if (row.email != auth.user.email and float(request.post_vars["owes_"+str(row.id)]) != float(0.0)):
            payment_row = db((TRANS_ID == db.payment.transaction_n)&(row.id == db.payment.payer)).select().first()
            if payment_row != None:
                amount_val = request.post_vars['owes_'+str(row.id)]
                db.payment[payment_row.id] = dict(amount=request.post_vars['owes_'+str(row.id)])
                db.payment[payment_row.id] = dict(state='null')
            else:
                db.payment.insert(transaction_n=TRANS_ID, payer=row.id, amount=request.post_vars['owes_'+str(row.id)], receiver=userid, state='null')
    return redirect(URL('details_transaction/'+str(TRANS_ID)))

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
