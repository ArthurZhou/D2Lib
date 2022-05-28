"""THIS ONLY WORK FOR 1.2.0-beta2 OR LOWER"""

import http.client

connection = http.client.HTTPConnection("0.0.0.0", 80)
connection.request("GET", "/", headers={"API-Auth": "root:root"})
response = connection.getresponse()
print("Status: {} and reason: {}".format(response.status, response.reason))
print(response.read().decode())

connection.close()
