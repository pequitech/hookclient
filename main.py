import sys
import json
import socket
import urllib2
from urllib2 import urlopen
import sqlite3
import time
import datetime


HOOKATHON_URL='hookathon.herokuapp.com'
HOOKATHON_PORT='80'

#HOOKATHON_URL='127.0.0.1'
#HOOKATHON_PORT=8000

#Retrieve all the inputs from user
email = sys.argv[1]
password = sys.argv[2]
myBin = sys.argv[3]
targetHost = sys.argv[4]
if(int(sys.argv[5])>120):
    looptime = int(sys.argv[5])
else:
    looptime=int(120)

def installation():
    # conectando...
    conn = sqlite3.connect('redirects.db')
    # definindo um cursor
    cursor = conn.cursor()
    # criando a tabela (schema)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS redirects (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            uid TEXT NOT NULL,
            target_host TEXT NOT NULL
    );
    """)

    # print('Table created with success!')
    # desconectando...
    conn.close()

def shouldRedirectRequest(rq_uid,tg_host):
    conn = sqlite3.connect('redirects.db')
    # definindo um cursor
    cursor = conn.cursor()
    cursor.execute("""
    SELECT count(uid) AS count FROM redirects WHERE uid = ? AND target_host = ?
    """, (rq_uid, tg_host))
    result = cursor.fetchall()[0][0]
    conn.close()
    # print(result)
    if result:
        return False
    else:
        return True

def registerRedirectedRequest(rq_uid,tg_host):
    conn = sqlite3.connect('redirects.db')
    # definindo um cursor
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO redirects (uid, target_host) VALUES (?, ?)
    """, (rq_uid, tg_host))
    conn.commit()
    conn.close()


def getRequests(myBin):
    url = "http://" + HOOKATHON_URL + ":" + HOOKATHON_PORT + "/api/bins/" + myBin + "/requests"
    response = urllib2.urlopen(url)
    data = json.loads(response.read())
    return data

def dispatchRequest(targetHost, request):

    url = targetHost
    contentType = request['header']['content_type'] or ''
    method = request['header']['method'] or 'GET'
    # print("Method: "+method+"\nContent-Type: "+contentType)


    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(url, data=request['body'])
    request.add_header('Content-Type', contentType)
    request.get_method = lambda: method
    url = opener.open(request)

    # print url.read()
    return True

def verifyRedirects(newRequests):
    conn = sqlite3.connect('redirects.db')
    for i in range(0, len(newRequests)):
        if shouldRedirectRequest(newRequests[i]['uid'],targetHost):
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S %d-%m-%Y')
            print(st+": Redirected Request ID " + str(newRequests[i]['id']) +" to "+targetHost)
            dispatchRequest(targetHost, newRequests[i])
            registerRedirectedRequest(newRequests[i]['uid'],targetHost)

            # print("dont send: " + str(newRequests[i]['id']))
    conn.close()

#Configure context to app
installation()

while True:
    #Request from remoteServer
    requestsOnRemoteServer = getRequests(myBin)
    #Find the differences and Update on targetHost
    verifyRedirects(requestsOnRemoteServer)
    #delay
    time.sleep(float(looptime))
