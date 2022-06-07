# -*- coding:utf-8 -*-
"""This only works on 1.2.0-stable or higher"""

import http.client

usr = ''
psw = ''
connection = http.client.HTTPConnection("0.0.0.0", 80)
connection.request("GET", f"/login?login={usr}:{psw}")
response = connection.getresponse()
print("Status: {} and reason: {}".format(response.status, response.reason))
print(response.read().decode())

connection.close()
