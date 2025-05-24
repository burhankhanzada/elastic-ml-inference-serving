### Todos:
1. Create FastAPI app -> `done`
2. Containerize the app
	1. Create docker files using `docker init` -> `done`
		1. Make a docker file for the FastAPI backend -> `done` 
3. Build your custom load_tester:
	1. Read the images -> `done`
	2. transform them according to the API endpoint 
4. Build your Dispatcher:
	1. I need to store the API post requests from the load_tester in some form of a queue -> `Asyncio` can be another option, simpler than the previous approach also recommended by Salmani.  -> First understand how it works and then devise a plan to implement it in your solution
		-> `Idea: the idea is to get the requests and hold them in a queue and send to a container which is available` : First do this for 1 container and see how it works. 
	2. `REDIS` is an option for doing that because it is fast as it stores the data in memory rather than disk - meaning we will be able to use RAM for fast request processing.
	3.  Then I need to write an algorithm that would dispatch these requests to the actual Resnet_API.
	4. I also need to monitor the metrics of the communication between these components using Prometheus.
	5.  Prometheus -> `https://prometheus.io/docs/guides/cadvisor/` [cAdvisor](https://github.com/google/cadvisor) (short for **c**ontainer **Advisor**) analyzes and exposes resource usage and performance data from running containers. cAdvisor exposes Prometheus metrics out of the box	