"""
Custom load tester
Author: Muhammad Ozair

"""

import glob
import random 
import requests
from typing import List, Tuple
import os
import json
from barazmoon import BarAzmoon


# class MyLoadTester(BarAzmoon):
#     def get_request_data(self) -> Tuple[str, str]:
#         return sending_data_id, sending_data

#     def process_response(self, sent_data_id: str, response: json):
#         do_sth(response, sent_data_id)


# workload = [7, 12, 0, 31, ...]  # each item of the list is the number of request for a second
# tester = MyLoadTester(workload=workload, endpoint="http://IP:PORT/PATH", http_method="post")
# tester.start()

API_ENDPOINT = "http://127.0.0.1:8000/predict"


class MyLoadTester(BarAzmoon):
    def __init__(self, *, workload, endpoint, http_method="get", **kwargs):
        super().__init__(workload=workload, endpoint=endpoint, http_method=http_method, **kwargs)

        self.image_path = "/home/shwifty/SOSE25/cloud_computing/ml_serving/test_images"
        self.image_paths = glob.glob(f"{self.image_path}/*.JPEG")



    def get_request_data(self) -> Tuple [str, str]:
        image_path = random.choice(self.image_paths)
        image_id = os.path.basename(self.image_path).split(".")[0].split("_")[0]

        return image_id, image_path
        

    def get_prediction(self,):
        image_id, image_path = self.get_request_data(self.image_paths)
        try:
            with open(image_path, "rb") as f:
                img_data = f.read()
                files = {"image": ("image.jpg", img_data)}

                response = requests.post(API_ENDPOINT, files=files)
                print(response)
        
        except Exception as e:
            print(f"the problem is here: {e}")

        prediction_class, confidence = self.process_response(image_id, response)
        
        return prediction_class, confidence

    def process_response(self, sent_data_id, response):
        
        prediction_json = response.json()
        prediction_class, confidence = prediction_json['prediction'].split(":")[0], float(prediction_json['prediction'].split(":")[1][:-1])

        return prediction_class, confidence

    


workload = [7, 12, 0, 31]  # each item of the list is the number of request for a second
tester = MyLoadTester(workload=workload, endpoint=API_ENDPOINT, http_method="post")
tester.start()