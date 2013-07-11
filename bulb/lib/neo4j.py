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

        if (r.raw.json()['data'][0][0] > 0):
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
                     "match idea<-[:OWNS]-user "
                     "return ID(idea) as id, idea.title as title, "
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
    
    :param raw: Raw requests.Response object
    :param status_code: HTTP status code
    :param reason: HTTP reason
    :param columns: Columns from neo4j result, if no error occured
    :param data: Data from neo4j result, if no error occured
    """

    def __init__(self, raw):
        """ Init N4JResponse object with requests.Response object. 
        If `raw' is not a requests.Response object, a TypeError is raised.
        """
        # check if raw is a requests.Response object
        if not isinstance(raw, requests.Response):
            raise TypeError("A valid requests.Response object should be provided")

        # Store raw response
        self.raw = raw
        # Store status code and reason
        self.status_code = raw.status_code
        self.reason = raw.reason
           
        if not self.is_error():
            # raw needs to contain a JSON encoded message
            if self.has_content_type("application/json"):
                try:
                    content = raw.json()
                except (TypeError, ValueError) as e:
                    raise ValueError("Invalid JSON provided ({0}):{1}".format(\
                            e.errno, e.strerror))
                else:
                    if "columns" in content and "data" in content:
                        self.columns = content["columns"]
                        self.data = content["data"]
                    else:
                        raise ValueError("JSON object should contain \
                                `columns' and `data' fields")
            else:
                raise ValueError("Only JSON requests are supported.")

    def is_error(self):
        return self.status_code != 200

    def error_message(self):
        # If no error occured
        if not self.is_error():
            return ""
        
        # If N4J JSON Error
        try:
            error = self.raw.json()
            return error["message"]
        except:
            return self.reason

    def content_type(self):
        """ Returns the content-type that was set in the HTTP headers. """
        return self.raw.headers['content-type']

    def has_content_type(self, content_type):
        """ Checks if the returned content is of the specified type.
        Implemented by searching for the substring
        """
        return self.content_type().find(content_type) > -1

    def count(self):
        return len(self.data)

    def bulb(self):
        """ Converts N4J content to bulb format using the following rules:
         IF is_error() RETURN { "error": "Error message"}
         ELSE:
            Example:
            { data: [ "value1", "value2" ], columns: [ "col1", "col2" ] }

            Zipped Example:
            { "col1" : "value1", "col2" : "value2" }
            
            Implemented using dict(zip(["col1","col2"],["value1","value2"])).
        """
        # if content was an json error message
        if self.is_error():
            return {"error": self.error_message()}
        else:
            output = []
            for datapoint in self.data:
                output.append(dict(zip(self.columns, datapoint)))
            return output
