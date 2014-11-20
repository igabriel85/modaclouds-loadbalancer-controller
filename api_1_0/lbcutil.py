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


import os.path
import socket
import sys
import signal
import subprocess
from subprocess import CalledProcessError, check_output, check_call,call



def checkFile(appname,ftype,temp_loc,  version):
	'''
		Checks if a certain type of file version is present in a directory.
		It takes appname,ftype,temp_loc and version parameters
	'''
	fname = '/'+appname+'-'+str(version)+'.'+ftype
	test =  os.path.exists(temp_loc+fname)
	if test == False:
		return fname
	else:
		return checkFile(appname,ftype,temp_loc,version+1)

def portScan(listenPort):
	'''
		Check if a port is occupied or not
	'''
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sockTest = sock.connect_ex(('0.0.0.0',listenPort))
	if sockTest == 0:
		#print "Port is not good:%s" % listenPort
		return portScan(listenPort +1)
	else:
		#print "Port %s is good!" % listenPort
		return listenPort




def checkPID(pid):
	"""
	Check For the existence of a unix pid.
	Sending signal 0 to a pid will raise an OSError exception if the pid is not running, and do nothing otherwise.
	"""
	if pid == 0:	#If PID newly created return False
		return False
	try:
		os.kill(pid, 0)
	except OSError:
		return False
	else:
		return True




def signalHandler(tmp_loc,pid_name):
	'''
	Handle User break gracefully and killing Haproxy
	'''
	print'Stopping controller ...'
	try:
		pidf = open(tmp_loc+pid_name,"r").readline()
		pidS = pidf.strip()
		#pidI = int(pidS)
	except IOError:
		#print "Error: File does not appear to exist."
		#print "Enter panic mode!"
		#checkOrf()
		sys.exit(0)
	#os.kill(pidI, signal.SIGKILL)
	#print gPID
	call(["kill", "-9", pidS])
	sys.exit(0)



"""
Check if orphan haproxy is running at startup
and kills it 
"""
def checkOrf():
	p = subprocess.Popen(['pgrep','haproxy'], stdout=subprocess.PIPE)
	out,err=p.communicate()
	if len(out)==0:
		pass
		# Not yet working
		# print "No haproxy detected."
		# ha= Process(target=call, args=(('haproxy', '-f', conf_loc +'/basic.cfg'), ))
		# ha.start()
		# print "Haproxy running with PID %s" %ha.pid
		# haPID = ha.pid
	else:
		for item in out.splitlines():
			print "Killing haproxy at PID %s" %item
			os.kill(int(item), signal.SIGKILL)
			# ha= Process(target=call, args=(('haproxy', '-f', conf_loc +'/basic.cfg'), ))
			# ha.start()
			# print "Haproxy running with PID %s" %ha.pid
			# haPID = ha.pid
	
	 

	#Process(target=call, args=(('pgrep','haproxy'),  )).start()
	#haPID.append(haChck)
	#print haPID
	# if len(haPID)==0:
	# 	print "Should start HaProxy"
	# else:
	# 	haKill = Process(target=call, args=(('pkill','haproxy'), )).start()
	# 	print "Killed haproxy"

'''
Parse PID file
'''

def parsePID(tmp_loc,pid_name):
	try:
		pidfile = open(tmp_loc+pid_name,"r").readline()
		pidString = pidfile.strip()
		pid = int(pidString)
		return pid
		#pidfile.readline()
	except IOError: 
		print "File does not exist."
		#response = jsonify({"PID Error":"File did not exist"})
		#response.status_code =201
		bFile = open(tmp_loc+pid_name,'w')
		bFile.write(str(0))
		bFile.close()
		return 0
		#return response


def checkConfig(tmp_loc,conf_name):
	'''
	Validate HAproxy config file.
	'''
	try:
		output = check_call(["haproxy", "-f" ,tmp_loc+'/'+conf_name])
		return 0
	except CalledProcessError as e:
		if e.returncode == 1:
			return 1

