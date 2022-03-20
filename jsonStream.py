import json
import asyncio
import logging
from socket import AI_NUMERICHOST
import time
import sys
from logFilenames import consoleFormatter, fileFormatter, getMainLogFilename

log = logging.getLogger('network')
log.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.DEBUG)
consoleHandler.setFormatter(consoleFormatter)

fileHandler = logging.FileHandler(getMainLogFilename())
fileHandler.setLevel(logging.INFO)
fileHandler.setFormatter(fileFormatter)

log.addHandler(consoleHandler)
log.addHandler(fileHandler)

class NotAJSONObject(Exception):
    pass

async def readJSON(reader: asyncio.StreamReader):
    message = ''
    data = ''
    while True:
        chunk = await reader.read(100)
        message += chunk.decode('utf8')
    
        if len(message) > 0 and message[0] != '{':
            raise NotAJSONObject('Received message is not a JSON Object')
        try:
            data = json.loads(message)
            break
        except json.JSONDecodeError:
            pass
    return data

async def writeJSON(writer: asyncio.StreamWriter, obj):
    message = json.dumps(obj)
    if message[0] != '{':
        raise NotAJSONObject('sendJSON support only JSON Object Type')
    message = message.encode('utf8')
    writer.write(message)
    await writer.drain()

class FetchError(Exception):
    pass

async def fetch(client, request, baseTime = 0.25, retries=10):
    try:
        for i in range(retries):
            try:
                coro = asyncio.open_connection(client.ip, client.port)#, happy_eyeballs_delay=0.25)
                reader, writer = await asyncio.wait_for(coro, baseTime*(i+1))
                break
            except asyncio.TimeoutError:
                if i > 4:
                    log.debug('Connection take too long. Retry({})...'.format(i+1))
            except OSError as e:
                if i > 4:
                    log.debug('Connection error: {}. Retry({})...'.format(e, i+1))
        else:
            raise FetchError("Unable to Open Connection to {}:{}".format(client.ip, client.port))
        await writeJSON(writer, request)
        start = time.time()
        response = await readJSON(reader)
        responseTime = time.time() - start
        writer.close()
        await writer.wait_closed()
        return response, responseTime
    except OSError as e:
        raise FetchError(str(e))
