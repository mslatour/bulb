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
        return N4JResponse(r)

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

        if (r.is_error()): # node not found
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
        if (len(r.raw.json()['data']) > 0):
            # r.json()['data'] is list of results
            # r.json()['data'][0] is first result
            # r.json()['data'][0][0] is first field of first result
            return r.raw.json()['data'][0][0]
        else:
            return False

    def get_idea(self, id):
        """
        Returns properties of id
        """
        if (self._is_idea(id)):
            query = ("start idea=node({0}) "
                     "match x<-[:OWNS]-user "
                     "return ID(x) as id, x.title as title, "
                     "user.username as owner").format(id)
            r = self._cypher(query)
            return r

    def get_all_ideas(self):
        """
        Returns all ideas in the system.
        Will be removed in the future because of excessive memory use.
        """
        query = ("start ideaRoot=node:roots(root='idea') "
                 "match ideaRoot-[:IDEA]->idea "
                 "return ID(idea) as id, idea.title as title")
        r = self._cypher(query)
        return r

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
            return r
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
            return r
        else:
            raise ValueError('node {0} either does not exist or is not an idea'.format(id))
       
class N4JResponse:
    """ Response object for N4J queries.
    
    :param raw: raw requests.Response object
    :param content: either raw.json() or raw.text()
    """

    def __init__(self, raw):
        """ Init N4JResponse object with requests.Response object. 
        If `raw' is not a requests.Response object, a TypeError is raised.
        """
        # check if raw is a requests.Response object
        if not isinstance(raw, requests.Response):
            raise TypeError

        # Store raw response
        self.raw = raw
           
        # If content appears to be json
        if self.has_content_type("application/json"):
            try:
                # Attempt to decode JSON
                self.content = raw.json()
            except (TypeError, ValueError, simplejson.JSONDecodeError):
                # Fallback, store text
                self.content = raw.text()
        else:
                # If not json, then just store the plain text
                self.content = raw.text()
    
    def is_error(self):
        return self.raw.status_code != 200

    def content_type(self):
        """ Returns the content-type that was set in the HTTP headers. """
        return self.raw.headers['content-type']

    def has_content_type(self, content_type):
        """ Checks if the returned content is of the specified type.
        Implemented by searching for the substring
        """
        return self.content_type().find(content_type) > -1

    def bulb(self):
        """ Converts N4J content to bulb format using the following rules:
         1) IF is_error() RETURN { "error": "Error message"}
         2) ELIF content is well-formed RETURN zipped result:
            Example:
            { data: [ "value1", "value2" ], columns: [ "col1", "col2" ] }

            Zipped Example:
            { "col1" : "value1", "col2" : "value2" }
            
            Implemented using dict(zip(["col1","col2"],["value1","value2"])).
         3) ELSE RETURN { "result": content }
        """
        # if content was an json error message
        if self.is_error() and \
                isinstance(self.content, dict) and \
                "message" in self.content:
            return {"error": self.content["message"]}
        # if content is well-formed 
        elif isinstance(self.content, dict) and \
                "columns" in self.content and \
                "data" in self.content:
            return dict(zip(self.content["columns"], self.content["data"]))
        else:
            return { "result" : self.content }
