from flask import jsonify, make_response

class ResponseBuilder:
    def __init__(self):
        self._response = {
            "status": "success",   
            "message": "",
            "data": None,
            "error": None          
        }
        self._status_code = 200

    def success(self, message="Success", data=None, status_code=200):
        self._response["status"] = "success"
        self._response["message"] = message
        self._response["data"] = data
        self._response["error"] = None
        self._status_code = status_code
        return self

    def error(self, error=None, message="Something went wrong", status_code=400):
        self._response["status"] = "error"
        self._response["message"] = message    
        self._response["data"] = None
        self._response["error"] = error
        self._status_code = status_code
        return self

    def build(self):
        clean_response = {k: v for k, v in self._response.items() if v is not None}
        return make_response(jsonify(clean_response), self._status_code)