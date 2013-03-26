import requests, simplejson

class N4J:
    def __init__(self, url, auth=None):
        self.url = url
        self.auth = auth

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
