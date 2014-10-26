'''

Copyright 2014, Institute e-Austria, Timisoara, Romania
    http://www.ieat.ro/
Developers:
 * Gabriel Iuhasz, iuhasz.gabriel@info.uvt.ro

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:
    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''



#!flask/bin/python
from flask import Flask, jsonify
from flask import request
from flask import redirect
from flask import make_response
from flask import abort
from flask import url_for
from flask import render_template
from flask import Response
from flask import send_file
from sqlalchemy import desc
import jinja2
import sys
import socket
import re

# import tempfile
# from shutil import copyfileobj
import sqlite3, os
import subprocess
import signal
from subprocess import call
from multiprocessing import Process
import os.path
import json
#from flask.ext.moment import Moment
from datetime import datetime
from flask.ext.sqlalchemy import SQLAlchemy
# generate temporary random named file
import tempfile
import random
# util import
from lbcutil import checkFile, portScan, checkPID, signalHandler


basedir = os.path.abspath(os.path.dirname(__file__))
template_loc = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
#conf_loc = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'configuration')
#pid_loc = os.path.join(os.path.dirname(os.path.abspath(__file__)),'tmp')

#db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)))

#idGen = random.randint(0,900)
randPort = '90'+str(random.randint(10,99))

portGen = portScan(int(randPort))





# Need to create temporary file for pid use tempfile

app = Flask('hrapy')

"""
Uncoment if use from flask.ext.moment import Moment
"""
#moment = Moment(app)

"""
Data Base Initialization
"""
# app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(basedir,'test.db')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True

db = SQLAlchemy(app)
#this creates a table with 5 columns
class db_hrapy(db.Model):
	__tablename__='Gateways'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	revision=db.Column(db.String(64), unique=False)
	schema = db.Column(db.String(64), unique=False)
	schemaVerion=db.Column(db.String(64), unique=False)
	mode = db.Column(db.String(64), unique=False, default = "http")
	defBack = db.Column(db.String(64), unique=False, default = 'None')
	data=db.Column(db.LargeBinary, unique=False)
	endpoints = db.relationship('db_endpoints',backref='name',lazy='dynamic') # added for relationship

	def __rep__(self):
		return '<db_hrapy %r>' % self.name

#create endpoint db table
class db_endpoints(db.Model):
	__tablename__='Endpoints'
	id = db.Column(db.Integer, primary_key=True)
	alias = db.Column(db.String(64), unique=True)
	entity_id = db.Column(db.String(64), unique=False)
	gateway_id = db.Column(db.String, db.ForeignKey(db_hrapy.name))
	revision = db.Column(db.String(64), unique=False, default = 1)
	schema = db.Column(db.String(64), unique=False)
	data = db.Column(db.LargeBinary, unique=False)

	def __rep__(self):
		return '<db_endpoints %r>' % self.name

#create pool db
class db_pool(db.Model):
	__tablename__='Pools'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	revision=db.Column(db.String(64), unique=False)
	schema = db.Column(db.String(64), unique=False)
	method = db.Column(db.String(64), unique=False)
	policy = db.Column(db.String(64), unique=False, default = 'roundrobin')
	policy_weights = db.Column(db.Float, unique=False, default = 1.0)
	enabled = db.Column(db.Boolean, unique=False)
	data=db.Column(db.LargeBinary, unique=False)
	target = db.relationship('db_target',backref='name',lazy='dynamic')

	def __rep__(self):
		return '<db_pool %r>' % self.name

class db_poolG(db.Model):
	__tablename__='GatewaysPools'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), unique=True)
	revision=db.Column(db.String(64), unique=False)
	schema = db.Column(db.String(64), unique=False)
	method = db.Column(db.String(64), unique=False)
	policy = db.Column(db.String(64), unique=False, default = 'roundrobin')
	policy_weights = db.Column(db.Float, unique=False, default = 0.0)
	data=db.Column(db.LargeBinary, unique=False, default = "none")
	#target = db.relationship('db_hrapy',backref='name',lazy='dynamic')

	def __rep__(self):
		return '<db_poolG %r>' % self.name

#create target db
class db_target(db.Model):
	__tablename__='Targets'
	id = db.Column(db.Integer, primary_key=True)
	revision=db.Column(db.String(64), unique=False)
	schema = db.Column(db.String(64), unique=False)
	pool_id = db.Column(db.String, db.ForeignKey(db_pool.name))
	alias = db.Column(db.String(64), unique=True)
	entity_id = db.Column(db.String(64), unique=True)
	weight = db.Column(db.String(64), unique=False, default = 1)
	enabled = db.Column(db.Boolean, unique=False, default = 1)
	
	
	def __rep__(self):
		return '<db_target %r>' % self.name

#create commit db
class db_commit(db.Model):
	__tablename__='Commits'
	id = db.Column(db.Integer, primary_key=True)
	schema = db.Column(db.String(64), unique=False)
	method = db.Column(db.String(64), unique=False)
	revision=db.Column(db.String(64), unique=False)
	data=db.Column(db.LargeBinary, unique=False)
	timestamp = db.Column(db.DateTime, default=datetime.utcnow)

	def __rep__(self):
		return '<db_commit %r>' % self.name





"""
Gateways Resources

"""


@app.route('/v1/gateways',methods=['GET'])
def getGateways():
	#how to query sqlite
	gatewayAll=db.session.query(db_hrapy.name).all()
	gatewayList = []
	for g in gatewayAll:
		gatewayList.append(g.name)
	response = jsonify({"Gateways":gatewayList})
	response.status_code = 200
	return response
    #return "List gateways!!"

@app.route('/v1/gateways/<gateway>' ,methods=['GET'])
def getGateway(gateway):
	if len(gateway)==0:
		abort(404)
	#get first instance of gateway from name field
	getGateway = db_hrapy.query.filter_by(name = gateway).first()
	if getGateway is None:
		response = jsonify({"No such gateway":gateway})
		response.status_code=404
		return response
	else:
		qEnd = db_endpoints.query.filter_by(gateway_id = gateway).all()
		qPool = db.session.query(db_poolG.name).all()
		
		endList = []
		for n in qEnd:
			endList.append(n.alias)

		entityList = []
		for e in qEnd:
			entityList.append(e.entity_id)

		#merge two lists into one dictionady	
		compose = dict(zip(endList,entityList))	
		poolList = []
		for p in qPool:
			poolList.append(p.name)
		#problem dictionary passed to json not in corect order
		response = jsonify({"gateway":gateway,"protocol":getGateway.mode,"endpoints":compose,"pools":poolList})	
		response.status_code = 200
		return response
		#response = jsonify({"gateway":gateway,"protocol":"http","endpoints"})

		
		# gateData = getGateway.data
		# return Response(gateData, mimetype = 'application/json')
	


@app.route('/v1/gateways/<gateway>',methods=['PUT'])
def addGateway(gateway):
	if len(gateway)==0:
		abort(404)
	if not request.json or not 'endpoints' in request.json:
		abort(400)	

	
	#queryPool = db_poolG.query.filter_by(name = ).first()
	
	# modifies endpoints in db_endpoints
	st = request.json['endpoints']	
	for key, value in 	st.iteritems():
		qend = db_endpoints.query.filter_by(alias = key).first()
		if qend is None:
			#e = db_endpoints(alias = key, revision = 1,schema = "/v1/gateways/"+gateway+"/endpoints/"+key, entity_id = value, gateway_id = gateway, data = data)
			#e = db_endpoints(alias = key, entity_id = value, gateway_id = gateway, schema = "whatever", data = data)
			e = db_endpoints(alias = key, entity_id = value, gateway_id = gateway, schema = "/v1/gateways/"+gateway+"/endpoints/"+key, data = "{\"address\":"+value+"}")
			db.session.add(e)
			db.session.commit
		else:
			rev= qend.revision
			qend.revision = int(rev) + 1
			qend.entity_id = value
			qend.gateway_id = gateway
			qend.data = "{\"address\":"+value+"}"
			db.session.add(qend) 
			db.session.commit()		

	# this is temporary as pools is required for beta version
	#qp = request.json['pools']
	if not 'pools' in request.json:
		pass
	else:
		qp = request.json['pools']
		for k in qp:
			qpool = db_poolG.query.filter_by(name = k).first()
			if qpool is None:
				p = db_poolG(revision = 1, name = k,schema = "/v1/gateways/pools/"+key, method = request.method)
				db.session.add(p)
				db.session.commit()
			else:
				rev = qpool.revision
				qpool.revision = int(rev)+1
				#need to talk to cc
				db.session.add(qpool)
				db.session.commit()


	queryGateway = db_hrapy.query.filter_by(name = gateway).first()

	if not 'defaultBack' in request.json:
			default = 'None'
	else:
		default = request.json['defaultBack']

	if queryGateway is None:
		# sent to data the request body in the form of a json
		u = db_hrapy(revision = 1,name = gateway, schema = url_for('addGateway', gateway = gateway) ,schemaVerion = request.method, data = request.data, mode = request.json['protocol'], defBack = default)
		#p = db_poolG(revision = 1,name = alias, schema = stringSchema ,method = "PUT", data = "dummydata", policy = "roundrobin", policy_weights = 1.0)
		#e = db_endpoints(revision = 1, alias = endpoint1, entity_id ="124.123.123.12", gateway_id = "test", schema = url_for('putEndpoint', gateway = gateway, endpoint1 = endpoint1), data = request.data )
		db.session.add(u) 
		db.session.commit()
		response = jsonify({'Added gateway':gateway})
		response.status_code = 200
		return response
	else:
		rev= queryGateway.revision
		queryGateway.revision = int(rev) + 1
		queryGateway.data = request.data
		queryGateway.defBack = request.json['defaultBack']
		db.session.add(queryGateway) 
		db.session.commit()
		response = jsonify({'Modified':gateway})
		response.status_code =200
		return response

	#return "Added Gateway with id %s!" % gateway

'''
Created query over database using name field for filter then returned the 
first mathing the <gateway> string
'''

@app.route('/v1/gateways/<gateway>',methods=['DELETE'])
def delGateway(gateway):
	if len(gateway)==0:
		abort(404)
	delete_gateway_id = db_hrapy.query.filter_by(name = gateway).first()
	if delete_gateway_id is None:
		response = jsonify({'Gateway Not Found':gateway})
		response.status_code = 404
		return response
	else:	
		db.session.delete(delete_gateway_id)
		db.session.commit()
		response = jsonify ({'Delete Gateway':gateway})
		response.status_code = 200
		return response

@app.route('/v1/gateways/<gateway>/endpoints', methods = ['GET'])
def getEndpoints(gateway):
	if len(gateway)==0:
		abort(404)
	endpoints=db.session.query(db_endpoints.alias).filter_by(gateway_id = gateway).all()
	if len(endpoints)==0:
		response = jsonify({"Gateway Not Found":gateway})
		response.status_code = 404
		return response
	else:
		endpointList = []
		for e in endpoints:
			endpointList.append(e.alias)
		response = jsonify({"Gateway":gateway,"Endpoints":endpointList})
		response.status_code = 200
		return response
	#return "Return endpoints"

@app.route('/v1/gateways/<gateway>/endpoints/<endpoint>', methods = ['GET'])
def getEndpoint(gateway,endpoint):
	if len(gateway)==0 or len(endpoint)==0:
		abort(404)
		#get first instance of gateway and endpoint from name field
	queryGateway = db_hrapy.query.filter_by(name = gateway).first()
	getEndpoint= db_endpoints.query.filter_by(alias = endpoint).first()
	queryGatewayEndpoint = db_endpoints.query.filter_by(gateway_id = gateway).first()

	if queryGateway is None:
		response = jsonify({"No such gateway":gateway})
		response.status_code=404
		return response

	if getEndpoint is None:
		response = jsonify({"No such endpoint":endpoint})
		response.status_code=404
		return response

	if queryGatewayEndpoint is None:
		response = jsonify({"Wrong gateway":gateway})
		response.status_code = 404
		return response 

	response = jsonify({"address":getEndpoint.entity_id})
	response.status_code =200
	return response
	#endData = getEndpoint.data
	#return Response(endData, mimetype = 'application/json')
	

@app.route('/v1/gateways/<gateway>/endpoints/<endpoint1>',methods=['PUT'])
def putEndpoint(gateway, endpoint1):
	if len(gateway)==0 or len(endpoint1)==0:
		abort(404)
	if not request.json or not 'address' in request.json:
		abort(400)

	endpointQuery = db_endpoints.query.filter_by(alias=endpoint1).first()
	if endpointQuery is None:
		e = db_endpoints(revision = 1, alias = endpoint1, entity_id =request.json['address'], gateway_id = gateway, schema = url_for('putEndpoint', gateway = gateway, endpoint1 = endpoint1), data = request.data )
		db.session.add(e)
		db.session.commit()
		response = jsonify({"Added Endpoint":endpoint1})
		response.status_code = 200
		return response
	else:
		rev= endpointQuery.revision
		endpointQuery.revision = int(rev) + 1
		# add code for modification
		endpointQuery.data = request.data
		endpointQuery.entity_id = request.json['address']
		db.session.add(endpointQuery) 
		db.session.commit()
		response = jsonify({'Modified':endpoint1})
		response.status_code =200
		return response
		


@app.route('/v1/gateways/<gateway>/endpoints/<endpoint>',methods=['DELETE'])
def deleteEndpoint(gateway,endpoint):
	if len(endpoint)==0:
		abort(404)
	delete_endpoint_id = db_endpoints.query.filter_by(alias = endpoint).first()
	db.session.delete(delete_endpoint_id)
	db.session.commit()
	response = jsonify ({'Delete Endpoint':endpoint})
	response.status_code = 200
	return response
	#return "Delete speccific endpoint %s" % endpoint


@app.route('/v1/gateways/pools', methods = ['GET'])
def getPools():
	poolAll=db.session.query(db_poolG.name).all()
	if len(poolAll) == 0:
		response = jsonify({"Pool Error":"No pools present"})
		response.status_code = 404
		return response
	else:
		poolList = []
		for g in poolAll:
			poolList.append(g.name)
		response = jsonify({"Pools":poolList})
		response.status_code = 200
		return response
	#return "Return Pools"


@app.route('/v1/gateways/pools/<pool>' ,methods=['GET'])
def getPool(pool):
	if len(pool)==0:
		abort(404)
	#get first instance of gateway from name field
	getPool = db_poolG.query.filter_by(name = pool).first()
	if getPool is None:
		response = jsonify({"No such Pool":pool})
		response.status_code=404
		return response
	else:
		poolData = getPool.data
		return Response(poolData, mimetype = 'application/json')
	#return "Get specific pool: %s" % pool

@app.route('/v1/gateways/pools/<pool>',methods=['PUT'])
def putPool(pool):
	curent_time = datetime.utcnow()
	if len(pool)==0:
		abort(404)
	if not request.json or not 'targets' in request.json:
		abort(400)	
	queryPool = db_poolG.query.filter_by(name = pool).first()
	if queryPool is None:
		# sent to data the request body in the form of a json to db_harpy
		u = db_hrapy(revision = 1,name = pool, schema = url_for('putPool', pool = pool) ,schemaVerion = request.method, data = request.data)
		db.session.add(u) 
		db.session.commit()
		response = jsonify({'Added pool':pool})
		response.status_code = 200
		return response
	else: # if pool exists only update revision number and request data
		rev= queryPool.revision
		queryPool.revision = int(rev) + 1
		queryPool.data = request.data
		db.session.add(queryPool) 
		db.session.commit()
		response = jsonify({'Modified':pool})
		response.status_code =200
		return response
	#return "Put specific pool: %s" % pool

@app.route('/v1/gateways/pools/<pool>', methods=['DELETE'])
def delPool(pool):
	if len(pool)==0:
		abort(404)
	delete_pool_id = db_hrapy.query.filter_by(name = pool).first()
	db.session.delete(delete_pool_id)
	db.session.commit()
	response = jsonify ({'Delete pool':pool})
	response.status_code = 200
	return response
	#return "Delete specific pool: %s" % pool


"""
Pool Resources

"""

@app.route('/v1/pools', methods=['GET'])
def getStPools():
	poolAll=db.session.query(db_pool.name).all()
	if len(poolAll) == 0:
		response = jsonify({"Pool Error":"No pools present"})
		response.status_code = 404
		return response
	else:
		poolList = []
		for g in poolAll:
			poolList.append(g.name)
		response = jsonify({"Pools":poolList})
		response.status_code = 200
		return response
	#return jsonify({'pools':['something', 'something']})

@app.route('/v1/pools/<pool>', methods=['GET'])
def getStPool(pool):
	if len(pool)==0:
		abort(404)

	qPool= db_pool.query.filter_by(name = pool).first()
	if qPool is None:
		response = jsonify({"No such pool":pool})
		response.status_code = 404
		return response
	
	#qTarget = db.session.query(db_target.name).all()
	qTarget = db_target.query.filter_by(pool_id = pool).all()

	tList = []
	for t in qTarget:
		tList.append(t.alias)

	idList = []
	for i in qTarget:
		idList.append(i.entity_id)

	compPool = dict(zip(tList,idList))	

	response = jsonify({"targets":compPool,"enabled":qPool.enabled})
	response.status_code = 200
	return response
	

@app.route('/v1/pools/<pool>',methods = ['PUT'])
def putStPool(pool):
	if len(pool)==0:
		abort(404)
	if not request.json or not 'targets' in request.json:
		abort(400)

	pl = request.json['targets']
	for key, value in 	pl.iteritems():
		qtar = db_target.query.filter_by(alias = key).first()
		if qtar is None:
			tar = db_target(alias = key, entity_id = value, pool_id = pool, schema = "/v1/pools/"+pool,revision = 1)
			db.session.add(tar)
			db.session.commit
		else:
			rev= qtar.revision
			qtar.revision = int(rev) + 1
			qtar.entity_id = value
			qtar.pool_id = pool
			qtar.enabled = request.json['enabled']
			db.session.add(qtar) 
			db.session.commit()		

	queryStPool = db_pool.query.filter_by(name = pool).first()
	if queryStPool is None:
		# sent to data the request body in the form of a json to db_pool
		u = db_pool(revision = 1,name = pool, schema = url_for('putStPool', pool = pool) ,method = request.method, data = request.data, enabled = 1)
		db.session.add(u) 
		db.session.commit()
		response = jsonify({'Added pool':pool})
		response.status_code = 200
		return response
	else:
		rev= queryStPool.revision
		queryStPool.revision = int(rev) + 1
		queryStPool.data = request.data
		queryStPool.enabled = request.json['enabled']
		db.session.add(queryStPool) 
		db.session.commit()
		response = jsonify({'Modified':pool})
		response.status_code =200
		return response

@app.route('/v1/pools/<pool>',methods = ['DELETE'])
def delStPool(pool):
	if len(pool)==0:
		abort(404)
	delete_Stpool_id = db_pool.query.filter_by(name = pool).first()	
	if delete_Stpool_id is None:
		response = jsonify({'No such pool':pool})
		response.status_code = 404
		return response
	else:
		db.session.delete(delete_Stpool_id)
		db.session.commit()
		response = jsonify ({'Delete pool':pool})
		response.status_code = 200
		return response
	#return "delStPool here"

@app.route('/v1/pools/<pool>/policy',methods = ['GET'])
def getPolicy(pool):
	if len(pool) ==0:
		abort(404)

	qPolicy = db_pool.query.filter_by(name = pool).first()
	if qPolicy is None:
		response = jsonify({"No such pool":pool})
		response.status_code = 404
		return response
	else:
		response = jsonify({"policy":qPolicy.policy,"weights":qPolicy.policy_weights})
		response.status_code = 200
		return response


@app.route('/v1/pools/<pool>/policy',methods = ['PUT'])
def putPolicy(pool):
	if len(pool) ==0:
		abort(404)
	if not request.json or not 'policy' in request.json:
		abort(400)

	#list of all accepted policy names

	accepted_policy = {'leastconn','backfill','roundrobin'}
	

	if request.json['policy'] not in accepted_policy:
		response = jsonify({'Invalid policy': request.json['policy']})
		response.status_code = 400
		return response	

	policyQuery = db_pool.query.filter_by(name = pool).first()

	if policyQuery is None:
		response = jsonify({'Pool Not found':pool})
		response.status_code = 404
		return response
	else: # gets from request json the wights and policy
		rev=policyQuery.revision
		policyQuery.revision = int(rev)+1
		policyQuery.policy = request.json['policy']
		policyQuery.policy_weights = request.json['weights']
		response = jsonify({'Modified policy':pool})
		response.status_code = 200
		return response
		#abort(400)


@app.route('/v1/pools/<pool>/policy',methods = ['DELETE'])
def delPolicy(pool):
	if len(pool) == 0:
		abort(404)
	qp = db_pool.query.filter_by(name = pool).first()
	if qp is None:
		response = jsonify({"No such pool":pool})
		response.status_code=404
		return response
	else:
		rev = qp.revision
		qp.revision = int(rev)+1
		qp.policy = 'roundrobin'
		qp.policy_weights = 1.0
		db.session.add(qp)
		db.session.commit()
		response = jsonify({"Reset policy for pool":pool})
		response.status_code = 200
		return response



@app.route('/v1/pools/<pool>/targets', methods=['GET'] )
def getPTargets(pool):
	if len(pool)==0:
		abort(404)

	poolQ = db_pool.query.filter_by(name = pool).first()
	if poolQ is None:
		response = jsonify({"No such pool":pool})
		response.status_code = 404
		return response
	else:
		#targetAll=db.session.query(db_target.alias).all()
		targetAll = db_target.query.filter_by(pool_id = pool).all()
		targetList = []
		for t in targetAll:
			targetList.append(t.alias)
		response = jsonify({"Targets":targetList})
		response.status_code = 200
		return response


@app.route('/v1/pools/<pool>/targets/<target>', methods=['GET'])
def getTarget(pool,target):
	if len(pool)==0 or len(target)==0:
		abort(404)

	qp = db_pool.query.filter_by(name = pool).first()
	if qp is None:
		response = jsonify({"No such pool":pool})
		response.status_code = 404
		return response

	qTarget = db_target.query.filter_by(alias = target).first()
	if qTarget is None:
		response = jsonify({"No such target":target})
		response.status_code=404
		return response
	else:

		response = jsonify({"address":qTarget.entity_id,"weight":qTarget.weight,"enabled":qTarget.enabled})
		response.status_code = 200
		return response
		


@app.route('/v1/pools/<pool>/targets/<target>', methods=['PUT'])
def setTarget(pool, target):
	if len(target) ==0:
		abort(404)
	if not request.json or not 'address' in request.json:
		abort(400)
	if not 'weight' in request.json:
		abort(400)
	
	qp = db_pool.query.filter_by(name = pool).first()
	if qp is None:
		response = jsonify({"No such Pool":pool})
		response.status_code = 404
		return response 

	targetQuery = db_target.query.filter_by(alias = target).first()
	if targetQuery is None:
		u = db_target(revision = 1, alias = target, entity_id = request.json['address'] , schema = url_for('setTarget', pool = pool, target = target), enabled = request.json['enabled'], pool_id = pool, weight = request.json['weight'])
		db.session.add(u) 
		db.session.commit()
		response = jsonify({'Added Target':target})
		response.status_code = 200
		return response
	else:
		rev= targetQuery.revision
		targetQuery.revision = int(rev) + 1
		targetQuery.entity_id = request.json['address']
		targetQuery.pool_id = pool
		targetQuery.enabled = request.json['enabled']
		targetQuery.weight = request.json['weight']
		db.session.add(targetQuery) 
		db.session.commit()
		response = jsonify({'Modified':target})
		response.status_code =200
		return response
		

@app.route('/v1/pools/<pool>/targets/<target>', methods=['DELETE'])
def delTarget(pool,target):
	if len(target)==0:
		abort(404)

	qp = db_pool.query.filter_by(name = pool).first()
	if qp is None:
		response = jsonify({"No such pool":pool})
		response.status_code = 404
		return response

	delete_target_id = db_target.query.filter_by(alias = target).first()	
	if delete_target_id is None:
		response = jsonify({'No such target':target})
		response.status_code = 404
		return response
	else:
		db.session.delete(delete_target_id)
		db.session.commit()
		response = jsonify ({'Deleted target':target})
		response.status_code = 200
		return response
	
'''
Check if target is online
'''

@app.route('/v1/pools/<pool>/targets/<target>/check', methods =['GET'])
def checkTarget(pool,target):
	if len(target)==0:
		abort(404)

	qp = db_pool.query.filter_by(name = pool).first()
	if qp is None:
		response = jsonify({"No such pool":pool})
		response.status_code = 404
		return response

	qTarget = db_target.query.filter_by(alias = target).first()
	if qTarget is None:
		response = jsonify({"No such target":target})
		response.status_code=404
		return response
	else:
		# parse entity_id for host and port
		entityID = qTarget.entity_id
		p = '(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
		m = re.search(p,entityID)
		targetHost =  m.group('host') 
		targetPort =  m.group('port') 
		s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.settimeout(10) #set timeout
		try:
			s.connect((targetHost,int(targetPort)))
			response = jsonify({"Target":qTarget.alias,"Host":targetHost,"Port":targetPort,"Status":"Online"})
			response.status_code = 200
			s.close()
			return response
			#print "Port 22 reachable"
		except socket.error as e:
			response = jsonify({"Target":qTarget.alias,"Host":targetHost,"Port":targetPort,"Status":"Offline"})
			response.status_code = 500
			qTarget.enabled = 0
			db.session.add(qTarget) 
			db.session.commit()
			s.close()
			return response
			#print "Error on connect: %s" % e
		

		# response = jsonify({"Address":qTarget.entity_id,"weight":qTarget.weight,"enabled":qTarget.enabled})
		# response.status_code = 200
		# return response
"""
	Controllers

"""
@app.route('/v1/controller/_export-cdb', methods=['GET'])
def exportCDB():
	return "TODO - export cdb"

@app.route('/v1/controller/_export-sql', methods=['GET'])
def exportSQL():
	try:
		dbDump = open(basedir+'/test.db','rb')
		
		return send_file(dbDump,mimetype = 'application/x-sqlite2',as_attachment = True)
		# dbCon = sqlite3.connect(basedir+'/test.db')
		# with open('dump.sql', 'w') as dbDump:
		# 	for line in dbCon.iterdump():
		# 		f.write('%s\n' % line)

	except IOError: 
		print "Error: File does not appear to exist."
		response = jsonify({"DB Error":"File missing"})
		response.status_code =404
		return response
	
	# tempFileObj = tempfile.NamedTemporaryFile(mode='w+b',suffix='db')	
	# copyfileobj(dbDump,tempFileObj)
	# dbDump.close()
	# tempFileObj.seek(0,0)

	# response = send_file(tempFileObj, mimetype='application/octet-stream',as_attachment=True,attachment_filename='backup.db')
	# response.status_code = 200

	
	#return response
	#return Response(response=dbDump, status=200, content_type='application/x-sqlite3')

@app.route('/v1/controller/_import-sql', methods=['PUT'])
def importSQL():
	if len(request.data) == 0:
		response = jsonify({"Import error":"request has no content"})
		response.status_code = 400
		return response

	if not request.headers['content-type'] == 'application/x-sqlite2':
		response = jsonify({"Import error":"invalid content-type"})
		response.status_code = 400
		return response

	dbImp =  open(basedir+"/imp.db","w+")
	dbImp.write(request.data)
	dbImp.close()

	response = jsonify({"DB import":"Done"})
	response.status_code = 200
	return response



# @app.route('/v1/controller/status', methods = ['GET'])
# def haStatus():
# 	return redirect("127.0.0.1:9100/status")


'''
First render the configuration template 'conf'.
It then writes it to a file named 'haproxy.temp'.
Afther closing the file it starts a multiprocess call 
that starts haproxy by loading the conf file

'''

@app.route('/v1/controller/commit',methods=['POST'])
def reloadLB():
	templateLoader = jinja2.FileSystemLoader( searchpath="/" )
	templateEnv = jinja2.Environment( loader=templateLoader )
	
	TEMPLATE_FILE = template_loc+"/haproxy.temp"
	#TEMPLATE_FILE = "/Users/Gabriel/Desktop/jinja.test"
	# Read the template file using the environment object.
	# This also constructs our Template object.
	template = templateEnv.get_template( TEMPLATE_FILE )



	queryPool = db_pool.query.filter_by(enabled = 1).all()

	# create a list of enabled pools
	listPool = []
	for p in queryPool:
		listPool.append(p.name)
	
		# comlex dict
		dictPT = {}
		

		for i in listPool:
			# create lists of associated enabled targets
			listTname = []
			listTaddress = []
			listWeights = []
			tarID = []
			# dict for target
			dictTarget = {}
			qt = db_target.query.filter_by(pool_id = i).all()
			for t in qt:
				if t.enabled == 1:
					listTname.append(t.alias)
					listTaddress.append(t.entity_id)
					listWeights.append(t.weight)
					
					#dictTarget = dict(zip(listTname,listTaddress))
					#composed target ID
					tarID = [x + " "+ y for x, y in zip(listTname, listTaddress)]
					
					dictTarget = dict(zip(tarID,listWeights))
					
					
				dictPT.update({i:{ "policy":p.policy,"weight":t.weight,  "targets":dictTarget}})
		

	ga=db.session.query(db_hrapy.name).all()
	gd=db.session.query(db_hrapy.defBack).all() # for default backends
	gatewayList = []
	defBackend = []
	defDict = {}

	for g in ga:
		gatewayList.append(g.name)

	
	for d in gd:						# list of default backends
		defBackend.append(d.defBack)
			
	defDict = dict(zip(gatewayList,defBackend))
	
	#listGID = []
	dictGateway = {}
	
	for i in gatewayList:
		
		qe = db_endpoints.query.filter_by(gateway_id = i).all()
		listEID = [] # Init list after iteration for gatewaylist; Stores items for each gateway

		for n in qe:
			listTemp = []	# reinitialize after every iteration to store individual endpoint for gateways 
			listEID.append(n.entity_id)

			listTemp = listEID
				
		dictGateway.update({i:listEID})




	# removed "default_back":listPool.pop(0) and added "default_back":defDict			
	tmp = {"conf":dictPT,"default_back":defDict,"pid":tmp_loc+pid_name,"gateway":dictGateway,"listenPort":portGen}			
	conf = template.render(tmp)
	

	#conf = render_template('haproxy.conf_template', def_back = 'backendOne', method = 'roundrobin', server_alias = 'backOneA1',server_address ='127.0.0.1:9001' )
	file =  open(tmp_loc+conf_name,"w+")
	file.write(conf)
	file.close()

	#call(["haproxy", "-f","-D", conf_loc + "/haproxy.conf"])    #added -D to start haproxy as deamon (?)
	

	'''
	Parse pid file and see if process is still running
	'''
	try:
		pidfile = open(tmp_loc+pid_name,"r").readline()
		pidString = pidfile.strip()
		pid = int(pidString)
		#pidfile.readline()
	except IOError: 
		print "File does not exist."
		#response = jsonify({"PID Error":"File did not exist"})
		#response.status_code =201
		bFile = open(tmp_loc+pid_name,'w')
		bFile.write(str(0))
		bFile.close()
		print "Created PID file"
		pidfile = open(tmp_loc+pid_name,"r").readline()
		pidString = pidfile.strip()
		pid = int(pidString)
		#return response
	
		
		
	#finally: - to run regardless of pid file
	#if pid exists than reload conf
	if checkPID(pid) == True:
		#return "Haproxy is running with PID %s" %pid
		#haproxy -f /etc/haproxy.cfg -p /var/run/haproxy.pid -sf $(cat /var/run/haproxy.pid)
		p=Process(target=call, args=(('haproxy', '-f', tmp_loc +conf_name,'-p', tmp_loc +pid_name,'-sf',pidString), ))
		p.start()
		#order in desending order the primary key ids and return the biggest one
		commitQuery = db_commit.query.order_by(desc(db_commit.id)).first()
		rev=commitQuery.revision
		commitQuery.revision = int(rev)+1
		commitQuery.data = conf
		response = jsonify({"HaProxy Status":"restarted","PID":pid,'Listen Port':portGen})
		response.status_code = 200
		return response
	else:
		p=Process(target=call, args=(('haproxy', '-f', tmp_loc +conf_name), ))
		p.start()
		response = jsonify({'Haproxy Status':'Started','Listen Port':portGen})
		#Query the db and if commit exists increase revision number and change commit name
		u = db_commit(revision = 1, schema = url_for('reloadLB') ,method = request.method, data = conf)
		db.session.add(u) 
		db.session.commit()
		response.status_code = 200
		return  response
	



"""
Custom errot Handling

"""	


@app.errorhandler(403)
def forbidden(e):
    response = jsonify({'error': 'forbidden'})
    response.status_code = 403
    return respons


@app.errorhandler(404)
def page_not_found(e):
    response = jsonify({'error': 'not found'})
    response.status_code = 404
    return response
   


@app.errorhandler(500)
def internal_server_error(e):
    response = jsonify({'error': 'internal server error'})
    response.status_code = 500
    return response
   

@app.errorhandler(405)
def meth_not_allowed(e):
	response=jsonify({'error':'method not allowed'})
	response.status_code=405
	return response

@app.errorhandler(400)
def bad_request(e):
	response=jsonify({'error':'bad request'})
	response.status_code=400
	return response


'''
Only for testing do not use
'''
@app.route('/v1/test', methods = ['POST'])
def tempTest():

	# The search path can be used to make finding templates by
	#   relative paths much easier.  In this case, we are using
	#   absolute paths and thus set it to the filesystem root.
	templateLoader = jinja2.FileSystemLoader( searchpath="/" )
	# An environment provides the data necessary to read and
	#   parse our templates.  We pass in the loader object here.
	templateEnv = jinja2.Environment( loader=templateLoader )
	
	# This constant string specifies the template file we will use.
	TEMPLATE_FILE = "/Users/Gabriel/Documents/workspaces/pyHrapi/api_1_0/templates/haproxy.temp"
	#TEMPLATE_FILE = "/Users/Gabriel/Desktop/jinja.test"
	# Read the template file using the environment object.
	# This also constructs our Template object.
	template = templateEnv.get_template( TEMPLATE_FILE )



	queryPool = db_pool.query.filter_by(enabled = 1).all()

	# create a list of enabled pools
	listPool = []
	for p in queryPool:
		listPool.append(p.name)
	
		# comlex dict
		dictPT = {}
		#comlex = {}

		for i in listPool:
			# create lists of associated enabled targets
			listTname = []
			listTaddress = []
			listWeights = []
			tarID = []
			# dict for target
			dictTarget = {}
			qt = db_target.query.filter_by(pool_id = i).all()
			for t in qt:
				if t.enabled == 1:
					listTname.append(t.alias)
					listTaddress.append(t.entity_id)
					listWeights.append(t.weight)
					# add the name and address lists
					tarID = [x + " "+ y for x, y in zip(listTname, listTaddress)]
					
					dictTarget = dict(zip(tarID,listWeights))
					#dictTest = {"name":i,"prop":{"policy":p.policy,"weight":p.policy_weights,"target":dictTarget}}
				#dictPT.update({i:{ "policy":p.policy,"weight":t.weight,  "targets":dictTarget}})
				dictPT.update({i:{ "policy":p.policy,"weight":t.weight,  "targets":dictTarget}})
		
	ga=db.session.query(db_hrapy.name).all()
	gd=db.session.query(db_hrapy.defBack).all() # for default backends
	gatewayList = []
	defBackend = []
	defDict = {}
	for g in ga:
		gatewayList.append(g.name)

	for d in gd:						# list of default backends
		defBackend.append(d.defBack)
			
	defDict = dict(zip(gatewayList,defBackend))
	compDict = {"defaults":defDict}
	
	dictGateway = {}
	
	for i in gatewayList:
		
		qe = db_endpoints.query.filter_by(gateway_id = i).all()
		
		listEID = []
		for n in qe:
			#listGID.append(n.gateway_id)
			
			listEID.append(n.entity_id)
			dictGateway.update({i:listEID})
		
		dictGateway['default'+i] = d

	tmp = {"conf":dictPT}			
	#outputText = template.render(tmp)
	tmp2 = {"whatever":dictGateway}
	#response = jsonify(tmp)

	#return response
	return str(listEID)
	#return str(defBackend)

"""
Populating dbs with dummy values - WARNING do NOT USE

"""	
@app.route('/v1/dummy',methods=['POST'])
def dummy():
  	poolname = ["testPool3","testPool4","testPool53","testPool63","testPool73","testPool83",
	"testPool39","testPool130","testPool131","testPool132","testPool133","testPool134"]
	endpointName = {"EndpointOne":"11.0.0.1","EndpointTwo":"11.0.0.2","EndpointThree":"11.0.0.3","EndpointFour":"11.0.0.4","EndpointFive":"11.0.0.5",}
	stringEndpointSchema = "/v1/gateways/test1/endpoints/"
	targetName = {"targetOne":"10.0.0.1","targetTwo":"10.0.0.2","targetThree":"10.0.0.3","targetFour":"10.0.0.4","targetFive":"10.0.0.5","targetSix":"10.0.0.6",}
	stringTargetSchema = "/v1/pools/testPool3/targets/"

	gatewayName = {"gatewayOne":"{'something':g1}","gatewayTwo":"{'something':g2}","gatewayThree":"{'something':g3}","gatewayFour":"{'something':g4}","gatewayFive":"{'something':g5}"}

	for k, v in gatewayName.iteritems():
		stringSchema = "/v1/gateways/"+k
		g = db_hrapy(revision = 1, name = k,schema = stringSchema, schemaVerion = "PUT", data = v,mode = "https")
		db.session.add(g)
		db.session.commit()

	for alias in poolname:
		stringSchema = "/v1/pools/"+alias
		pool = db_pool(revision = 1,name = alias, schema = stringSchema ,method = "PUT", data = "dummydata", policy = "roundrobin", policy_weights = 1.0, enabled = 1)
		db.session.add(pool) 
		db.session.commit()

	for alias in poolname:
		stringSchema = "/v1/gateways/pools/"+alias
		pool = db_poolG(revision = 1,name = alias, schema = stringSchema ,method = "PUT", data = "dummydata", policy = "roundrobin", policy_weights = 1.0)
		db.session.add(pool) 
		db.session.commit()

	for key , value in endpointName.iteritems():
		endpoint = db_endpoints(revision = 1, alias = key, entity_id = value , schema = stringEndpointSchema+key, gateway_id = "test1",data = '{"address":"127.0.0.122"}')
		db.session.add(endpoint) 
		db.session.commit()

	
	for key, value in targetName.iteritems():
		target = db_target(revision = 1, alias = key, entity_id = value , schema = stringTargetSchema+key, enabled = True, pool_id = "testPool3")
		db.session.add(target) 
		db.session.commit()

	

	response = jsonify({"Succesfull":"db_dummy"})
	response.status_code=200
	return response


if __name__ == '__main__':
	tmp_loc = tempfile.gettempdir()
	conf_name = checkFile('haproxy','conf',tmp_loc, 1)
	pid_name = checkFile('haproxy','pid',tmp_loc, 1)

	if len(sys.argv) == 1:
		app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(tmp_loc,'default.db')
		db.create_all()
		app.run(host='0.0.0.0', port=8088, debug = True)
		signal.signal(signal.SIGINT, signalHandler(tmp_loc,pid_name))
		signal.pause()
	else:
		arList = sys.argv
		host = arList[1]
		port = int(arList[2])
		dbname = str(arList[3])
		app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///'+os.path.join(tmp_loc,dbname+'.db')
		db.create_all()
		app.run(host = host, port = port)
		signal.signal(signal.SIGINT, signalHandler(tmp_loc,pid_name))
		signal.pause()

	
		
	