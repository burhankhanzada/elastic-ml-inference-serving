import asyncio

class Dispatcher:
    async def __init__(self):
        pass
    
    
    async def get_requests():
        """
        This function receives requests from the load balancer and puts them in a queue using asyncio.
        """
        # This queue is going to hold inference requests:
        request_queue = asyncio.Queue()

        pass

