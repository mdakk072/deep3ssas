import base64
import json
import logging
import os
from threading import Thread
import time
import cv2
import numpy as np
import requests
import torch
from bs4 import BeautifulSoup
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyEncoder, self).default(obj)

class DetectionModule:
    def __init__(self, model_path='best.pt', video_path="", camera=False, cameraid=0, test=False,APIurl="http://localhost",timeout=45):
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=os.path.join("modules", "detection", model_path))
        self.colorStates = [(0, 0, 255), (0, 255, 0)]
        self.readyToSend = True
        self.parkings={}
        self.APIurl=APIurl
        self.currentParkingID = 0
        self.test = test  
        self.timeout=timeout
        self.cache = {} 
        if camera or video_path:
            print(camera)
            print(video_path)
            self.cap = cv2.VideoCapture(cameraid) if camera else cv2.VideoCapture(video_path)
            self.parkings[0]={
            "id": 0,
            "source": 'Local',
            "detections": {},
            "image": None,
            "freespace": 0,
            "sourceInfos": None
            }
        else:                       
            self.cap=None
        with open('parking_structure.json', 'r') as f:
            self.parkings.update(json.load(f))
        
    def getLocalisation(self):
        try:
            ip_address = requests.get('https://api.ipify.org').text
            url = f'http://ip-api.com/json/{ip_address}'
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception if the status code is not 200
            location = response.json()
            location_keys = ['country', 'city', 'lat', 'lon', 'regionName', 'timezone', 'zip', 'countryCode']
            locationInfos = {key: location.get(key, f'None ({key} Error)') for key in location_keys}
            return locationInfos
        except requests.exceptions.RequestException as e:
            print(f"Impossible d'obtenir votre localisation. Erreur: {e}")
            error_dict = {key: f'None ({key} Error)' for key in location_keys}
            return error_dict

    def prepare_parkings_data(self, data):
        def convert_image_to_base64(image):
            if image is not None:
                retval, buffer = cv2.imencode('.jpg', image)
                return base64.b64encode(buffer).decode('utf-8')
            return None
        parkings_copy = {
            key: {**parking, 'image': convert_image_to_base64(parking['image'])}
            for key, parking in data.items()
        }
        return parkings_copy

    def update_API(self, datatosend, current_parking_id, test):
        try:
            data_to_send = {
                'parkings': datatosend,
                'current_parking_id': current_parking_id,
                'test': test
            }
            #logging.info('Sending parkings data to API: {}'.format(parkings_data))
            url = f'{self.APIurl}/status'
            json_response = json.dumps(data_to_send, cls=NumpyEncoder)
            try:
                r = requests.post(url, data=json_response, headers={'Content-Type': 'application/json'})
                return r
            except Exception as e:
                #logging.error('Error occurred while sending data to API: {}'.format(e))
                print('Error occurred while sending data to API: {}'.format(e))
            # Reset the readyToSend flag
            self.readyToSend = True
        except Exception as e:
            #logging.error('Error occurred while sending data to API: {}'.format(e))
            print(f'>Erreur API:  {e}')

    def detect_frame(self, frame):
        def draw_detections(frame, detections):
            for _, detection in detections.iterrows():
                xmin, ymin, xmax, ymax = map(int, detection[['xmin', 'ymin', 'xmax', 'ymax']].tolist())
                confidence, state = round(float(detection['confidence']), 2), int(detection['class'])
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), self.colorStates[state], 1)
        frame_resized = cv2.resize(frame, (640, 640))
        img_processed = cv2.GaussianBlur(frame_resized, (5, 5), 0)
        img_processed = cv2.addWeighted(img_processed, 1.5, frame_resized, -0.5, 0)
        results = self.model(img_processed)
        detections = results.pandas().xyxy[0]
        free = (detections['class'] == 1).sum()
        total = len(detections)
        data_to_post = {'full': total - free, 'empty': free, 'places': total}
        draw_detections(frame_resized, detections)
        return frame_resized, data_to_post ,detections.to_dict(orient='records')

    def get_remote_image(self):
        def is_valid_image(image):
            return image is not None and len(image.shape) == 3 and image.shape[2] == 3


        def parse_camera_details(soup):
            camera_details = soup.find("div", class_="camera-details")
            if camera_details:
                details_dict = {}
                for row in camera_details.find_all("div", class_="camera-details__row"):
                    cells = row.find_all("div", class_="camera-details__cell")
                    if len(cells) == 2:
                        key = cells[0].get_text(strip=True).rstrip(":")
                        value = cells[1].get_text(strip=True)
                        details_dict[key] = value
                return details_dict
            return None

        def capture_remote_image(image_url, result):
            cap = cv2.VideoCapture(image_url)
            if cap.isOpened():  # Vérifie si la capture d'image est ouverte et fonctionne correctement
                ret, frame = cap.read()
                result.append(frame)
            else:
                result.append(None)  # Ajoute 'None' au résultat si la capture d'image échoue
            cap.release()


        def save_image_to_cache(image, cache_file):
            cached_images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cached_images")
            if not os.path.exists(cached_images_path):
                os.makedirs(cached_images_path)
            cv2.imwrite(os.path.join(cached_images_path, cache_file), image)

        def load_image_from_cache(cache_file):
            cached_images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cached_images")
            if os.path.exists(os.path.join(cached_images_path, cache_file)):
                return cv2.imread(os.path.join(cached_images_path, cache_file))
            return None

        cache_file = f"cached_image_{self.currentParkingID}.jpg"
        max_retries = 3
        retry_count = 0
        while retry_count <= max_retries:
            url = self.parkings[self.currentParkingID]['source']
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                self.parkings[self.currentParkingID]["sourceInfos"] = parse_camera_details(soup)
                img_tag = soup.find("img")
                if img_tag:
                    img_url = img_tag["src"]
                    result = []
                    image_thread = Thread(target=capture_remote_image, args=(img_url, result))
                    image_thread.start()
                    image_thread.join(timeout=self.timeout)  # Set the timeout in seconds

                    if image_thread.is_alive():
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f"[{timestamp}] > Timeout reached for camera {self.currentParkingID}, stopping image capture from: {img_url}.")
                        cached_image = load_image_from_cache(cache_file)
                        if cached_image is not None:
                            return cached_image
                        return None
                    else:
                        captured_image = result[0] if result else None
                        if captured_image is not None :
                            save_image_to_cache(captured_image, cache_file)
                        return captured_image
                else:
                    print("No <img> tag found.")
            else:
                print(f"Error retrieving web page. Status code: {response.status_code}")
                cached_image = load_image_from_cache(cache_file)
                if cached_image is not None :
                    return cached_image
                return None
            retry_count += 1
        cached_image = load_image_from_cache(cache_file)
        if cached_image is not None:
            return cached_image
        return None
 
    def load_image_from_cache(self,cache_file):
            cached_images_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cached_images")
            if os.path.exists(os.path.join(cached_images_path, cache_file)):
                return cv2.imread(os.path.join(cached_images_path, cache_file))
            return None

    def runRemoteSource(self):
        start_time = time.time()
        while True:
            try:
                
                for idx, p in enumerate(self.parkings, start=1):
                    time.sleep(0.05)
                    #print(f'========== Parking {p}/{len(self.parkings)} ==========')
                    self.currentParkingID = p
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    print(f"[{timestamp}] > Current parking ID {self.currentParkingID}/{len(self.parkings)}          " ,end='\r')
                    parking = self.parkings[p]
                    if not self.currentParkingID and self.cap != None:
                        ret, frame = self.cap.read()
            
                    else:
                        try:
                            frame = self.get_remote_image()
                            self.cache[self.currentParkingID] = frame
                        except Exception as e:
                            cache_file = f"cached_image_{self.currentParkingID}.jpg"
                            frame=self.load_image_from_cache(cache_file)
                            print(f"Failed to get remote image:\n {e}")
                            print(f'Loading {cache_file}')
            
                    #print('>Detecting parking spaces in the frame.')
                    try:
                        parking['image'], parking['detections'] , parking['labels'] = self.detect_frame(frame)
                        #print('Detect OK!')
                    except Exception as e:
                        parking['image'], parking['detections'] , parking['labels'] = frame , {'full': 0, 'empty': 0, 'places': 0}, []

                        print(f">! Failed to detect parking spaces: \n{e}")
                    
                current_time = time.time()
                elapsed_time = current_time - start_time
                if self.readyToSend and not self.test:
                    try:
                        response= self.update_API(self.prepare_parkings_data(self.parkings), self.currentParkingID, self.test)
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f"[{timestamp}] > Update API ({self.APIurl}) : {response} {round(elapsed_time,2)}s")
                    except Exception as e:
                        print(f">! Failed to update API: {e}")
                        continue
                start_time = current_time
                if self.test:
                    print(f'API url : {self.APIurl}/status')

                    break
            except KeyboardInterrupt:
                self.readyToSend = -1
                break
            except Exception as e:
                print(">! An exception occurred: {}".format(e))
                self.readyToSend = -1
                if self.cap != None:
                    self.cap.release()

def find_file(filename, default_path=None):
    if default_path is None:
        default_path = os.getcwd()  # Set default path to current working directory if not provided

    # Check if the file exists in the default path
    file_path = os.path.join(default_path, filename)
    if os.path.isfile(file_path):
        return file_path

    # Check if the file exists in the same directory as the Python script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, filename)
    if os.path.isfile(file_path):
        return file_path

    return None

if __name__ == "__main__":
    # Add logging configuration
    print('================== Deep3ssas ==================')
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.xml", help="Path to the configuration file")
    args = parser.parse_args()
    configFile=find_file(args.config)
    tree = ET.parse(configFile)
    
    root = tree.getroot()
    model_path = root.find("model_path").text
    video_path = root.find("video_path").text
    timeout = int(root.find("timeout").text)
    APIurl = root.find("API_url").text
    camera = root.find("camera").text.lower() == "true"
    cameraid = int(root.find("cameraid").text)
    test = root.find("test").text.lower() == "true"
    print(f'>Deep3ssas Detection module using {args.config} : ')

    print()
    print(f'>> model : {model_path}')
    print(f'>> API   :  {APIurl}')
    print(f'>> Timeout   :  {timeout}s')
    if camera : 
        print(f'>> camera ID : {cameraid}')
    elif video_path:
        print(f'>> Video : {video_path}')
    elif test:
        print(f'>> *** Test mode (1 iteration) *** ')
    print('\n===============================================')
    

        


    p = DetectionModule(model_path=model_path, video_path=video_path, camera=camera, cameraid=cameraid, test=test,APIurl=APIurl,timeout=timeout)
    p.runRemoteSource()