#!/bin/bash

echo -n "Username: "
read username
echo -n "Password: "
read password

sha224=`python -c "import hashlib;print hashlib.sha224('$password').hexdigest()"`
idUserJson=`curl -s -X POST -H "Content-Type: application/json" -d "{\"query\":
\"CREATE (user { username: '$username', password: '$sha224' } ) RETURN ID(user)\"}" $NEO4J_URL/db/data/cypher`
idUser=`python -c "raw=$idUserJson;print raw['data'][0][0]"`
curl -s -X POST -H "Content-Type: application/json" -d "{\"key\": \"username\", \"value\": \"$username\", \"uri\": \"node/$idUser\"}" $n4j/db/data/index/node/users
echo "Added user $username at node $idUser"
