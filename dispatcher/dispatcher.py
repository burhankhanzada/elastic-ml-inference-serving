import asyncio


REQUEST_QUEUE = asyncio.Queue()

class Dispatcher:
    def __init__(self, REQUEST_QUEUE):
        
        # This queue is going to hold inference requests:
        self.request_queue = REQUEST_QUEUE

    
    
    async def get_requests():
        """
        This function receives requests from the load balancer and puts them in a queue using asyncio.
        
        1. Load tester will send 'workload/sec' (workload = number of requests) 
        2. I need to see how these requests are actually sent and then store them in the asyncio Queue.
        """

        pass

