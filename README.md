# pyHrapi
 

pyHrapi  is a RESTFul API for  [HaProxy](http://www.haproxy.org/) load balancer. It is created for the [MODAClouds](www.modaclouds.eu) project. It stands for python Haproxy RESTFul API.

It is designed to: 

* **add, edit and delete resources** - You can define pools, gateways, endpoints and targets. These are direct representations of resources present in HaProxy. Also each interaction is saved and versioned.

* **set policy** - You can define the load balancing policy and set the weights for each target. This is for weighted round-robin and other similar policies.
* **start load balancing service** - You are able to create a config file that is then used to start the load balancing service. Each time a new config file is generated it is resubmited to the same service.

It is important to note that it is only an early prototype. No guarantees are given for its use. Furthermore it may be subject to significant changes from version to version.

## Change Log
* v0.2.5-alpha
** listen port check implemented
** code refactoring 

* v0.2-alpha 
**The generated haproxy config, pid files as well as the sqlite database is created in the folder denoted by $TMPDIR env varibale
** now default ip is set to "0.0.0.0" on port "8088".
** renamed default database to default.db instead of test.db
** changed haproxy status URI from "/status" to "__haproxy/dashboard"

### Environmental Variables

```
It uses the $TMPDIR environmental variable to store temporary files for each launched instance.
```

## Install

These instructions were tested on Mac OS X Mavericks, openSuse 13.1 and Ubuntu 14.04. The main development machine was running Mac OS.


Requirements are pretty simple:

* ** [python](https://www.python.org/downloads/) 2.7.4 **

* ** [sqlite3](http://www.sqlite.org/) **

* ** [haproxy](http://www.haproxy.org/) **

* ** [git](http://git-scm.com/) (optional) **




In order to clone the repository create or go to a directory of your choosing and type:

```
$ git clone https://igabriel@bitbucket.org/igabriel/pyhrapi.git

```
Or you can use

```
https://github.com/igabriel85/modaclouds-loadbalancer-controller
```


We used pip and virtualenv to install and run pyHrapi.

First you need to install [pip](http://pip.readthedocs.org/en/latest/installing.html).
In order to use [virtualenv](http://virtualenv.readthedocs.org/en/latest/virtualenv.html#installation) we need to install it first, as an example:

```
$ sudo apt-get install vitrualenv

```

or we can use pip:

```
$pip install virtualenv

```

We need to create a virtualenv this can be done in any directory but it is advised to use a workspace location.

```
$virtualenv henv

```
You can use another name if you like. The we need to enter into the new environment:

```
$source henv/bin/activate

```

Once activated it is time to install the dependencies of pyHrapi this is done like this:

```
(henv)..$ pip freeze -r requirement.txt

```

The file `requirements.txt` can be found in the repository and contains a list of required python modules. pyHrapy was created mainly using [Flask](http://flask.pocoo.org/).

In order to start pyHrapi we must enter the following command

```
(henv)..$ python pyprox.py <ip-address> <port> <db name> 

```


If no host is given pyHrapi uses localhome on port 5000.
If you want to use the provided virtualenv you can start it using the provided bash script:

```
...$ ./start-mlbc.sh
```
or

```
...$./start-mlbc.sh <ip-address> <port> <db name> 
```

It is important to note that because makin virtualenv relocatable is still experimental we have preconfigured environments for MacOS X 10.9 and openSUSE 13.1 (both 32 and 64 bits).


##Usage 
### Gateways

HaProxy Frontend

`GET` `/v1/gateways`

a list of identifiers for the defined gateways; (i.e. the response body is a JSON list containing strings;)
```json
{
  "Gateways": [
    "gatewayHTTP", 
    "gatewayTCP", 
    "gatewayHTTPS" 
  ]
}

```

`GET` `/v1/gateways/{gateway}`

obtain the definition document for a particular gateway (identified by the token {gateway}); the response body is a <gateway-descriptor>;

```json
{
  "endpoints": {
    "EndpointFive": "11.0.0.5", 
    "EndpointFour": "11.0.0.4", 
    "EndpointThree": "11.0.0.3", 
    "EndpointTwo": "11.0.0.2"
  }, 
  "gateway": "gatewayHTTP", 
  "pools": [
    "testPool1", 
    "testPool2", 
    "testPool3", 
    "testPool4", 
    "testPool5", 
    "testPool6", 
    "testPool7" 
  ], 
  "protocol": "http"
}

```

`PUT` `/v1/gateways/{gateway}`

create a new gateway (identified by the token {gateway}), or update an existing gateway in case one exists with the given identifier; the request body is a <gateway-descriptor>;

```json

{
  "gateway": "testPut",
  "protocol": "http",
  "endpoints": 
    {
      "endPutOne": "123.123.123.123:80",
      "endPutTwo":"123.123.123.124:80"
    },
    "pools":
    {
      "poolPutG1": "1.1.1.1:80",
      "poolPutG2": "1.1.1.2:80"
    },
  "enable": "True"
}

```

Currently pool usage in the context of gateways is broken. Thus it can be ommited in the above json when submitting gateways.
Also it is possible to define the default pool (backend) for a given frontend (gateway).

```json
{
  "gateway": "testPut",
  "protocol": "http",
  "endpoints": 
    {
      "endPutOne": "123.123.123.123:80",
      "endPutTwo":"123.123.123.124:80"
    },
    "pools":
    {
      "poolPutG1": "1.1.1.1:80",
      "poolPutG2": "1.1.1.2:80"
    },
  "enable": "True",
  "defaultBack":<backend_id>
}

```

It is important to note that if no default backend is defined it is set to 'None'.


`DELETE` `/v1/gateway/{gateway}`

Deletes the designated gateway; Currently only deletes gateway (db_hrapy) and not the associated pools or endpoints.

`GET` `/v1/gateways/{gateway}/endpoints`

a list of identifiers for all the gateway's endpoints;
```json
{
  "Endpoints": [
    "EndpointThree", 
    "EndpointFive", 
    "EndpointTwo", 
    "EndpointFour"
  ], 
  "Gateway": "gatewayHTTP"
}

```

`GET` `/v1/gateways/{gateway}/endpoints/{endpoint}`

Displays only the address of the endpoint.

```json
{
  "address": "11.0.0.2:80"
}
```
`PUT` `/v1/gateways/{gateway}/endpoints/{endpoint}`

This creates or modifies a given gateway endpoint:

```json
{
  "address": "12.0.0.22:80"
}
```


`DELETE` `/v1/gateways/{gateway}/endpoints/{endpoint}`

This deletes the given endpoint.

`GET` `/v1/gateways/{gateway}/pools`

A list of aliases for all the associated pools;

```json
{
  "Pools": [
    "testPool3", 
    "testPool2", 
    "testPool5", 
    "testPool6", 
    "testPool7", 
    "testPool3", 
    "testPool39", 
    "poolPutG2"
  ]
}
```

`GET` `/v1/gateways/{gateway}/pools/{pool}`

Returns the identifier (the one to be used in /v1/pools/{pool}) of the designated pool; (i.e. in the first URL {pool} is the alias, the key in the gateway's pools object;)

Currently broken.

`PUT` `/v1/gateways/{gateway}/pools/{pool}`

Currently broken.

`DELETE` `/v1/gateways/{gateway}/pools/{pool}`

Currently broken.

## Pools

HaProxy Backends

`GET` `/v1/pools`

Creates a json containing the list of all pools

```json
{
  "Pools": [
    "testPool1", 
    "testPool2", 
    "testPool3", 
    "testPool4", 
    "testPool5", 
    "testPool6", 
    "testPool7", 
    "testPool8", 
    "testPool9" 
  ]
}
```

`GET` `/v1/pools/{pool}`

Returns the pool descriptor of a specific pool member.

```json
{
  "enabled": true, 
  "targets": {
    "targetFive": "10.0.0.5:80", 
    "targetFour": "10.0.0.4:443", 
    "targetOne": "10.0.0.1:8080", 
    "targetSix": "10.0.0.6:8080", 
    "targetTestCLI": "1.2.3.4.5:5000", 
    "targetThree": "10.0.0.3:8080", 
    "targetThreeNew": "127.3.4.5:8080", 
    "targetTwo": "10.0.0.2:80"
  }
}
```

`PUT` `/v1/pools/{pool}`

Creates or modifies a specific pool member.

```json
{
  "enabled": true,
  "targets": {
    "targetT7": "12.1.0.5:80", 
    "targetT8": "12.1.0.4:8080", 
    "targetT9": "12.1.0.1:443", 
    "targetT10": "12.1.0.6:442", 
    "targetT11": "12.1.3.4:80", 
    "targetT12": "12.1.0.3:80"
  }
}
```

Can add multiple targets with their associated addresses.
If the target exists it modifies it. All targets are by default enabled.

`DELETE` `/v1/pools/{pool}`

Deletes a specific pool.

`GET` `/v1/pools/{pool}/targets`

Returns a json containing the list of all target aliases.

```json
{
  "Targets": [
    "targetFour", 
    "targetSix", 
    "targetTwo", 
    "targetFive", 
    "targetThree", 
    "targetOne", 
    "targetTestCLI", 
    "targetThreeNew"
  ]
}
```

`GET` `/v1/pools/{pool}/targets/{target}`

Returns a json containing a the target associated with a pool.

```json
{
  "address": "10.0.0.6:80",
  "weight" : 220,
  "enabled": true
}
```

`PUT` `/v1/pools/{pool}/targets/{target}`

Creates or modifies a target associated with a pool.

```json
{
  "address": "10.0.1.6:80",
  "weight": 12, 
  "enabled": false
}
```

Can also change the pool with which the target is associated.
Only here can the targets be enabled or disabled.

`DELETE` `/v1/pools/{pool}/targets/{target}`

Deletes the target from a specified pool.

### Policy


`GET` `/v1/pools/{pool}/policy`

Obtain the policy of the designated pool; the response body is either the JSON null value in case no policy exists, or a <policy>;
As well as its default weight.
```json
{
  "policy": "roundrobin", 
  "weights": 1.0
}
```


`PUT` `/v1/pools/{pool}/policy`

Updates the policy of the designated pool; (by using the JSON null value the same effect as DELETE is obtained;)

```json
{
  "policy": "roundrobin", 
  "weights": 2.0
}
```

`DELETE` `/v1/pools/{pool}/policy`

Reset the policy of the designated pool to a default value;

It is important to note that all names and aliases of gateways, endpoints, targets and pools are considered unique.
Thus, no duplicate names are allowed. Further more all jsons are case sensitive.

`GET` `/v1/pools/{pool}/targets/{target}/check`

Checks if a target is online or not. If the target is online it returns:

```json
{   
    "Target": <target_id>,
    "Host": <host-ip>,
    "Port": <port>,
    "Status": "Online"
}
```
It the target/service is offline it returns:

```json
{   
    "Target": <target_id>,
    "Host": <host-ip>,
    "Port": <port>,
    "Status": "Offline"
}
```

It is important to note that once a target is determined to be offline it is flagged as disabled and not included into the new configuration file loaded into Haproxy.
The new configuration is not automatically loaded.

## Starting Haproxy

`POST` `/v1/controller/commit`

Starts Haproxy service by generating a valid configuration file and loading it. If the service is already running it will reload the config file only.
There is a bug that is preventing Haproxy child process from stopping correctly if the parent process dies. This will be fixed in future versions.
Please see the Issue tracker for more details.

`GET` `/v1/controller/_export-sql`

This exports the sqlite database and can be used to back up the database. Has bee fixed as of writing this readme. For further details see the issues tracker.


`PUT` `/v1/controller/_import-sql`

Imports an sql database and loads that as the default. The request data is the database itself. Currently broken. For more details see the issue tracker.


`GET` `/v1/controller/_export-cdb`

Currently not implemented. Scheduled for the next version.
   


# Getting Started - Example

First we need to use the virtualenvironment previously created. Once this is done we can start pyHrapi:


```
(henv)..$python pyprox.py <host> <port> <db name>

```

If the host ip and port are omitted it will listen at 127.0.0.1:5000 by default.

Let us say that we want to create a config file that has one http frontend and two backends. 

We can define the gateway and its endpoint using a json like this:

```json
{
  "gateway": "gateHTTP",
  "protocol": "http",
  "endpoints": 
    {
      "endOne": "173.13.23.11:80",
      "endTwo":"13.23.76.14:8080"
    },
  "enable": "True"
}

```
This json has to be used with the resource `/v1/gateways/gateHTTP` using the `PUT` method.

Once this is done we can create the two backends using pool resources:

```json
{
  "enabled": true,
  "targets": {
    "targetS1": "12.1.0.5:80", 
    "targetS2": "12.1.0.4:8080", 
    "targetS4": "12.1.0.1:443", 
    "targetS5": "12.1.0.6:442", 
    "targetS6": "12.1.3.4:80", 
    "targetS7": "12.1.0.3:80"
  }
}
```
Lets call this pool/backend `eta` and has the URI `/v1/pools/eta`

The second pool/gateway is defined by:

```json
{
  "enabled": true,
  "targets": {
    "targetT1": "172.1.0.5:80", 
    "targetT2": "172.1.0.4:8080", 
    "targetT3": "172.1.0.1:443"
  }
}
```
We can call this pool/backend `theta` and has the URI `/v1/pools/theta`

Now we can modify the individual weights of each target by accessing the resource. For example targetS1 from eta using `GET`:

`/v1/pools/eta/targets/targetS1`

```json
{
  "address": "12.1.0.5:80", 
  "weight": 200,
  "enabled": true
}
```

After the weights are adjusted Haproxy can be started with the resourceusing `POST`:

`/v1/controller/commit`

After a succesfull  

When Haproxy starts pyHrapi responds with:

```json
{
    "HaProxy Status": "Started",
    "Listen Port": "9029"
}

```

The listenPort refers to Haproxy status interface which can be accessed at:

```
<host>:<listenPort>/__haproxy/dashboard
```

##Note

In the configuration folder the config file used to start haproxy is stored. This is not necessary, it is only stored in file form for debugging purposes.
All configurations are also stored in the sqlite database. All files are stored into the OS's temporary directory (see: $TMPDIR environmental variable).




# Future Work


Notice
======

Copyright 2014, Institute e-Austria, Timisoara, Romania
    http://www.ieat.ro/

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at:
    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.