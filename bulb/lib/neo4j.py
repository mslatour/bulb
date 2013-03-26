from urlparse import urlparse, urlunparse
import requests, json

class N4J:
    """
    Wrapper class for Neo4J instance
    """
    def __init__(self, url):
        # Parse url to get authentication, if given
        parsed_url = urlparse(url)
        self.url = "http://{host}:{port}/db/data".format(host=parsed_url.hostname,
                                                    port=parsed_url.port)

        # Set authentication if passed in URL
        if (parsed_url.username and parsed_url.password):
            self.auth = requests.auth.HTTPBasicAuth(parsed_url.username,
                                                      parsed_url.password)
        # Otherwise set to None
        else:
            self.auth = None
        
    def _cypher(self, query, params={}):
        """
        PRIVATE
        Runs raw cypher query on Neo4J instance.
        """
        # Construct URL for posting cypher queries
        cypher_url = "{0}/cypher".format(self.url)
        # Content-type is JSON
        headers = {'content-type': 'application/json'}
        # Post query
        r = requests.post(cypher_url, data=json.dumps({"query": query,
                           "params": params}), auth=self.auth,
                           headers=headers)
        return r

    def _is_idea(self, id):
        """
        PRIVATE
        Returns True if the node with ID 'id' is an Idea.
        """
        query = ("start ideaRoot=node:roots(root='idea'), "
                 "idea=node({0}) "
                 "where idea<-[:IDEA]-ideaRoot "
                 "return count(*)".format(id))
        r = self._cypher(query)

        if (r.status_code == 400): # node not found
            return False

        if (r.json()['data'][0][0] > 0):
            return True
        else:
            return False

    def get_user(self, username):
        """
        Returns the Neo4J ID of the user with the given username.
        Returns False if user does not exist.
        """
        r = self._cypher("START u=node:users(username='{0}') RETURN ID(u)".\
                     format(username))
        # If user is found, return True
        if (len(r.json()['data']) > 0):
            # r.json()['data'] is list of results
            # r.json()['data'][0] is first result
            # r.json()['data'][0][0] is first field of first result
            return r.json()['data'][0][0]
        else:
            return False

    def add_idea(self, owner, title, properties={}):
        """
        Adds idea to the Neo4J database and links it to the given owner.

        'properties': A dictionary containing properties to be set on the idea
        """
        ownerID = self.get_user(owner)

        # Generate a cypher-acceptable string of properties
        # from the properties argument
        propertiesAsString = "{{title: '{0}'".format(title)
        for key in properties:
            propertiesAsString += ", {0}: '{1}'".format(key, properties[key])
        propertiesAsString += "}"

        if (ownerID):
            query = ("start ideaRoot=node:roots(root='idea'), "
                     "user=node({0}) "
                     "create (idea {1})"
                     "create ideaRoot-[:IDEA]->idea "
                     "create user-[:OWNS]->idea "
                     "return ID(idea) as id, idea.title as title;"\
                     .format(ownerID, propertiesAsString))

            r = self._cypher(query)
        else:
            raise ValueError('owner does not exist')

    def connect_ideas(self, source, sink):
        """
        Connects two ideas together in Neo4J instance.
        """
        if (self._is_idea(source) and self._is_idea(sink)):
            query = ("start source=node({0}), sink=node({1}) "
                     "create source-[:IS_RELATED_TO]->sink").\
                     format(source, sink)
            r = self._cypher(query)
            print r.content
        else:
            raise ValueError('either source or sink is not a valid idea')

    def delete_idea(self, id):
        """
        Deletes idea from Neo4J instance.
        Checks if 'id' is an Idea first (instead of for example a User)
        """
        if (self._is_idea(id)):
            query = ("start idea=node({0}) "
                     "match idea-[r]-() "
                     "delete r "
                     "delete idea").format(id)
            r = self._cypher(query)
        else:
            raise ValueError('node {0} either does not exist or is not an idea'.format(id))
