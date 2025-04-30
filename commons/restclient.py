'''
Created on 12-Feb-2018

Used as rest client. Authentication is not implemented yet.
@author: Devasish Ghosh<dghosh2@sastasundar.com>
'''
import requests
import json
import certifi
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

def prepauth(authdata):
    """
    Prepares authentication header as per authentication type and credentials
    """
    if authdata is None:
        return None
    
    try:
        if authdata['type'] == 'basic':
            return HTTPBasicAuth(authdata['username'], authdata['password'])
        elif authdata['type'] == 'digest':
            return HTTPDigestAuth(authdata['username'], authdata['password'])
    except:
        return None
    
def post(url, data, headers={}, authdata = None, ssl=False, files = {}):
    """
    Post request to api
    @param url: (string) api url
    @param data : (dict) data to send
    @param headers: (dict) header info
    @param authdata: (dict) 'type' is the compulsory key, containse auth type e.g. 'basic', 'digest' etc. other keys are as per auth  type, if type=basic or type=digest, other keys 'username' and 'password' must be there
    
    @return: content, response. returns 2 items, content in in JSON format and the response object
    """
    if ssl is True:
        ssl = certifi.where()
    if headers.get('Content-Type', "") == 'application/json':
        resp = requests.post(url, json=data, headers=headers, auth=prepauth(authdata), verify=ssl)
    else:
        if not files:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            resp = requests.post(url, data=data, headers=headers, auth=prepauth(authdata), verify=ssl)
        else:
            # headers['Content-Type'] = 'multipart/form-data'
            resp = requests.post(url, data=data, files=files, auth=prepauth(authdata), verify=ssl)

    try:
        return json.loads(resp.text), resp
    except:
        return resp.text, resp

def put(url, data, headers, authdata = None):
    """
    Put request to api
    @param url: (string) api url
    @param data : (dict) data to send
    @param headers: (dict) header info
    @param authdata: (dict) 'type' is the compulsory key, containse auth type e.g. 'basic', 'digest' etc. 
     other keys are as per auth  type, if type=basic or type=digest, other keys 'username' and 'password' must be there
     
    @return: content, response. returns 2 items, content in in JSON format and the response object
    """
    if headers.get('Content-Type', "") == 'application/json':
        resp = requests.put(url, json=data, headers=headers, auth=prepauth(authdata))
    else:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        resp = requests.put(url, data=data, headers=headers, auth=prepauth(authdata))
        
    try:
        return json.loads(resp.text), resp
    except:
        return resp.text, resp

def get(url, data, headers={}, authdata = None, https = False):
    """
    Get request to api
    @param url: (string) api url
    @param data : (dict) data to send
    @param headers: (dict) header info
     @param authdata: (dict) 'type' is the compulsory key, containse auth type e.g. 'basic', 'digest' etc. other keys are as per auth  type, if type=basic or type=digest, other keys 'username' and 'password' must be there
    
    @return: content, response. returns 2 items, content in in JSON format and the response object
    """
    if https is True:
        https = certifi.where()
    resp = requests.get(url, headers=headers, params=data, verify=https, auth=prepauth(authdata))
    
    try:
        return json.loads(resp.text), resp
    except:
        return resp.text, resp

def delete(url, data, headers, authdata = None):
    """
    Delete request to api
    @param url: (string) api url
    @param data : (dict) data to send
    @param headers: (dict) header info
    @param authdata: (dict) 'type' is the compulsory key, containse auth type e.g. 'basic', 'digest' etc. other keys are as per auth  type, if type=basic or type=digest, other keys 'username' and 'password' must be there
    
    @return: content, response. returns 2 items, content in in JSON format and the response object
    """
    if headers.get('Content-Type', "") == 'application/json':
        resp = requests.delete(url, json=data, headers=headers, auth=prepauth(authdata))
    else:
        headers['Content-Type'] = 'application/x-www-form-urlencoded'
        resp = requests.delete(url, data=data, headers=headers, auth=prepauth(authdata))

    try:
        return json.loads(resp.text), resp
    except:
        return resp.text, resp
