import asyncio
import uvicorn
import io

from fastapi import FastAPI, UploadFile
from PIL import Image

class Dispatcher:
    def __init__(self):
        
        # This queue is going to hold inference requests:
        self.request_queue = asyncio.Queue()
        self.request = None
        self.queue_size = None

    
    async def qsize(self, queue):
        
        self.queue_size = queue.qsize()
        return self.queue_size


    async def store_requests(self, request):
        """
        This function receives requests from the load balancer and puts them in a queue using asyncio.
        
        1. Load tester will send 'workload/sec' (workload = number of requests) 
        2. I need to see how these requests are actually sent and then store them in the asyncio Queue.
        """

        image_bytes = await request.read() # The reqeuest is basically the image sent by the load tester.
        image = Image.open(io.BytesIO(image_bytes))
        self.request = image
        await self.request_queue.put(self.request) # This basically stores the images in the queue

        return list(self.request_queue._queue), self.request_queue

    async def round_robin(self,):
        pass
