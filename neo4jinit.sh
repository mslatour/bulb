#!/bin/bash

# create 'roots' index
curl -s -X POST -H 'Content-Type: application/json' -d '{"name": "roots"}' $NEO4J_URL/db/data/index/node/
# create 'users' index
curl -s -X POST -H 'Content-Type: application/json' -d '{"name": "users"}' $NEO4J_URL/db/data/index/node/

# create idea root node and add to roots index
idIdeaRootJson=`curl -s -X POST -H 'Content-Type: application/json' -d '{"query": "create (n {} ) return ID(n)"}' $NEO4J_URL/db/data/cypher`
echo $idIdeaRootJson
idIdeaRoot=`python -c "raw=$idIdeaRootJson;print raw['data'][0][0]"`

curl -X POST -H 'Content-Type: application/json' -d "{\"key\": \"root\", \"value\": \"idea\", \"uri\": \"node/$idIdeaRoot\"}" $NEO4J_URL/db/data/index/node/roots

# create user root node and add to roots index
idUserRootJson=`curl -s -X POST -H 'Content-Type: application/json' -d '{"query": "create (n {} ) return ID(n)"}' $NEO4J_URL/db/data/cypher`
idUserRoot=`python -c "raw=$idUserRootJson;print raw['data'][0][0]"`

curl -s -X POST -H 'Content-Type: application/json' -d "{\"key\": \"root\", \"value\": \"user\", \"uri\": \"node/$idUserRoot\"}" $NEO4J_URL/db/data/index/node/roots
