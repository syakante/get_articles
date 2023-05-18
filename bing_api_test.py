import json
from pprint import pprint
#import requests
import asyncio
from aiohttp import ClientSession

with open('bing_headers.json') as f:
    bing_headers = json.load(f)

subscription_key = bing_headers['subscription_key']
endpoint = bing_headers['endpoint']
headers = { 'Ocp-Apim-Subscription-Key': subscription_key }

async def send_request(params, queue: asyncio.Queue):
    async with ClientSession() as session:
        async with session.get(endpoint, headers=headers, params=params) as response:
            response.raise_for_status()
            responseJSON = await response.json()
            pprint(responseJSON)
            await queue.put(responseJSON)
    '''
    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()

        print("\nHeaders:\n")
        print(response.headers)

        print("\nJSON Response:\n")
        pprint(response.json())
    except Exception as ex:
        raise ex
    '''


async def main(queries_path='queries.txt', freq='Week', count=5):

    with open(queries_path) as f:
        queryList = f.read().split('\n')
    
    myParams = { 'mkt': 'en-US' ,
               'freshness': freq,
               'count': count,
               'q': ''}
    
    results = []
    #not sure whether to use queue or gather... or wait...
    #it seems like there's lots of ways you can do this?? Let's just do queue for now since I've written it anyway
    queue = asyncio.Queue()
    async with asyncio.TaskGroup() as group:
        for i in range(len(queryList)):
            myParams['q'] = queryList[i] + " -msn"
            group.create_task(send_request(myParams, queue))
    while not queue.empty():
        results.append(await queue.get())
    print(json.dumps(results))

asyncio.run(main(freq='Month', count=2))
