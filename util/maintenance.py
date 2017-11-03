# -*- coding: utf-8 -*-

import time
import hashlib
import requests

urlDemand = "http://dsp.optaim.com/api/picture/getautoimagedemand"
urlUpdate = "http://dsp.optaim.com/api/picture/updatestatus"

def updatePtu(id):
    timestamp = str(int(time.time()))
    authoration = hashlib.md5("zlkjdix827fhx_adfe" + timestamp).hexdigest()
    headers = {'Authorization': authoration, 'Timestamp': timestamp}

    parameters = {'id': id, 'status': 1}
    requests.get(urlUpdate, headers=headers, params=parameters)


if __name__ == '__main__':
    updatePtu(247)
