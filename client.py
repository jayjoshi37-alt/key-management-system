import requests
import uuid
import platform

# YOUR API KEY

API_KEY = "JMQD-NZKP-UI0T-VHWH"


# MAC ADDRESS

mac_address = hex(uuid.getnode())


# DEVICE INFO

device_info = platform.platform()


# DATA

data = {

    "api_key": API_KEY,
    "mac_address": mac_address,
    "device_info": device_info

}


# SEND REQUEST

response = requests.post(

    "http://127.0.0.1:5000/verify-key",

    json=data

)


# OUTPUT

print(response.json())