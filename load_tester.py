import os
import random
import re
from typing import Tuple
from aiohttp import FormData, ClientTimeout
from barazmoon import BarAzmoon
import asyncio


class ImageLoadTester(BarAzmoon):
    def __init__(self, *, workload, endpoint, image_dir, http_method="post", **kwargs):
        super().__init__(workload=workload, endpoint=endpoint, http_method=http_method, **kwargs)
        self.image_dir = image_dir
        
        # Load all image paths
        self.image_paths = []
        for filename in os.listdir(image_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.image_paths.append(os.path.join(image_dir, filename))
        
        if not self.image_paths:
            raise ValueError(f"No images found in {image_dir}")
            
        print(f"Found {len(self.image_paths)} images for testing")
        
        # Statistics tracking
        self.class_counts = {}
        self.average_confidence = 0
        self.total_confidence = 0
        self.processed_count = 0
        
        # FIXED: Aligned timeout configuration - Give workers time to finish
        # self.request_timeout = ClientTimeout(total=80)  # Longer than processing time
        
    def get_request_data(self) -> Tuple[str, str]:
        # Select a random image from our directory
        image_path = random.choice(self.image_paths)
        image_id = os.path.basename(image_path)
        
        # We'll return the path to the file, not the file content
        # The actual file will be read and sent in the predict method
        return image_id, image_path
    
    async def predict(self, delay, session):
        await asyncio.sleep(delay)
        image_id, image_path = self.get_request_data()
        
        file_handle = None
        try:
            # Open file and create form data
            file_handle = open(image_path, 'rb')
            form_data = FormData()
            form_data.add_field('image', 
                               file_handle,
                               filename=os.path.basename(image_path),
                               content_type='image/jpeg')  # Adjust content type if needed
            
            # Send the request with the file upload and timeout
            async with session.post(self.endpoint, 
                                  data=form_data, 
                                  ) as response:
                response_json = await response.json(content_type=None)
                is_success = self.process_response(image_id, response_json)
                return 1 if is_success else 0
                
        except asyncio.TimeoutError:
            print(f"Timeout error with image {image_id}: Request took longer than {self.request_timeout.total}s")
            return 0
        except Exception as exc:
            print(f"Error with image {image_id}: {str(exc)}")
            return 0
        finally:
            # Ensure file handle is closed
            if file_handle:
                file_handle.close()
    
    
    def process_response(self, image_id: str, response: dict) -> bool:
        try:
            print(response)
            # Check if the response has the expected format
            if 'prediction' not in response:
                print(f"Error for image {image_id}: Invalid response format")
                return False
                
            # Parse the prediction string (format: "class: confidence%")
            prediction_str = response['prediction']
            match = re.match(r"([^:]+):\s*([\d.]+)%", prediction_str)
            
            if not match:
                print(f"Error for image {image_id}: Unable to parse prediction '{prediction_str}'")
                return False
                
            class_name = match.group(1).strip()
            confidence = float(match.group(2))
            
            # Update statistics
            if class_name not in self.class_counts:
                self.class_counts[class_name] = 0
            self.class_counts[class_name] += 1
            
            # Update confidence average
            self.total_confidence += confidence
            self.processed_count += 1
            self.average_confidence = self.total_confidence / self.processed_count
            
            print(f"Image {image_id}: Classified as '{class_name}' with {confidence}% confidence")
            return True
                
        except Exception as e:
            print(f"Error processing response for image {image_id}: {str(e)}")
            return False
    
    def display_results(self):
        """Display test results after completion"""
        print("\n----- Test Results -----")
        print(f"Total image requests: {self._BarAzmoon__counter}")
        print(f"Successful classifications: {self._BarAzmoon__success_counter.value}")
        print(f"Average confidence: {self.average_confidence:.1f}%")
        
        if self.processed_count > 0:
            print(f"\nClassification breakdown:")
            for class_name, count in sorted(self.class_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / self._BarAzmoon__success_counter.value) * 100 if self._BarAzmoon__success_counter.value > 0 else 0
                print(f"  {class_name}: {count} ({percentage:.1f}%)")


# Example usage
if __name__ == "__main__":
    # Define your load pattern - gradual ramp up
    experiment_workload = []
    negative_workload = []
    stress_workload = []

    with open('workload.txt', 'r') as f:
        workload_pattern = f.read().split(' ')

        count = 0
        neg_count = 0
        stress_count = 0
        for item in workload_pattern:
            item = int(item)
            
            if item < 20:
                negative_workload.append(item)
                neg_count += item
            else:
                stress_workload.append(item)
                stress_count += item
            
            experiment_workload.append(item)
            count += item
    # list(map(lambda r: int(r / 2), negative_workload))[:]
    # Initialize and run the tester
    tester = ImageLoadTester(
        # workload= list(map(lambda r: int(r / 2), negative_workload))[:] ,
        workload= [4] * 100,
        endpoint="http://127.0.0.1:41191/add_to_queue",
        #path for home-desktop: /home/shwifty/D-Essential/Msc RCSE/Third Semester/Cloud Computing/ml-elastic-serving/elastic-ml-inference-serving/imagenet-sample-images
        #path for laptop: /home/shwifty/SOSE25/cloud_computing/ml_serving/test_images
        image_dir="/home/shwifty/SOSE25/cloud_computing/ml_serving/test_images",
        timeout=30 # FIXED: Longer than request timeout to allow processing completion
    )
    
    # Run the test
    total_requests, successful_requests = tester.start()

    # Display detailed results
    tester.display_results()
    
    # Summary
    success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
    print(f"\nSummary: {successful_requests}/{total_requests} successful requests ({success_rate:.1f}%)")