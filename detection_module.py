import base64
import json
import logging
import time
import cv2
import numpy as np
import requests
import torch
from bs4 import BeautifulSoup
import argparse

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

# Create and configure logger
#logging.basicConfig(filename='parking_lot_detector.log', level=#logging.INFO)
# Log the start of the program
#logging.info('Program started.')

class DetectionModule:
    def __init__(self, model_path='best.pt', video_path="", camera=False, cameraid=0, test=False):
        self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        if camera:
            self.cap = cv2.VideoCapture(cameraid)
        elif video_path!="": 
            self.cap = cv2.VideoCapture(video_path)
        self.fps_start = cv2.getTickCount()
        self.frame_count = 0
        self.colorStates = [(0, 0, 255), (0, 255, 0)]
        self.strStates = ['Occupied', 'Free']
        self.readyToSend = True
        self.proccess = True
        self.frameTosend = None
        self.parkings={}
        if video_path!="" or camera:
            self.parkings[0]={
            "id": 0,
            "source": 'Local',
            "detections": {},
            "image": None,
            "freespace": 0,
            "sourceInfos": None
            }
            
        with open('parking_structure.json', 'r') as f:
            self.parkings.update(json.load(f))
        self.parkingsSendCopy = self.parkings.copy()
        self.currentParkingID = 0
        self.test = test  # Add test attribute

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

    def update_API(self,datatosend):
        try:
                    parkings_data = datatosend
                    #logging.info('Sending parkings data to API: {}'.format(parkings_data))
                    #link1 = 'http://127.0.0.1:5000/status'
                    link2 = 'http://mdakk072.pythonanywhere.com/status'
                    json_response = json.dumps(parkings_data, cls=NumpyEncoder)
                    try:
                        r = requests.post(link2, data=json_response, headers={'Content-Type': 'application/json'})
                        self.proccess=True
                        print(r)
                        print('data sent !')
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
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), self.colorStates[state], 2)
                cv2.putText(frame, f"{self.strStates[state]}:{confidence}%", ((xmax + xmin) // 2, (ymin + ymax) // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        frame_resized = cv2.resize(frame, (640, 640))
        img_processed = cv2.GaussianBlur(frame_resized, (5, 5), 0)
        img_processed = cv2.addWeighted(img_processed, 1.5, frame_resized, -0.5, 0)
        results = self.model(img_processed)
        detections = results.pandas().xyxy[0]
        free = (detections['class'] == 1).sum()
        total = len(detections)
        data_to_post = {'full': total - free, 'empty': free, 'places': total}
        draw_detections(frame_resized, detections)
        cv2.rectangle(frame_resized, (260, 10), (530, 40), (0, 255, 0), cv2.FILLED)
        cv2.putText(frame_resized, f"Free Space: {free}/{total}", (280, 30), cv2.FONT_HERSHEY_TRIPLEX, 0.7, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.rectangle(frame_resized, (260, 50), (550, 80), (0, 0, 255), cv2.FILLED)
        cv2.putText(frame_resized, f"Occupied Space: {total - free}/{total}", (265, 70), cv2.FONT_HERSHEY_TRIPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
        return frame_resized, data_to_post

    def get_remote_image(self):
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
        url = self.parkings[self.currentParkingID]['source']
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            self.parkings[self.currentParkingID]["sourceInfos"] = parse_camera_details(soup)
            img_tag = soup.find("img")
            if img_tag:
                img_url = img_tag["src"]
                cap = cv2.VideoCapture(img_url)
                ret, frame = cap.read()
                return frame
            else:
                print("No <img> tag found.")
        else:
            print(f"Error retrieving web page. Status code: {response.status_code}")
            return None

    def runRemoteSource(self):
        start_time = time.time()
        while True:
            try:
                current_time = time.time()
                elapsed_time = current_time - start_time
                for idx, p in enumerate(self.parkings, start=1):
                    time.sleep(0.05)
                    print(f'========== Parking {p}/{len(self.parkings)} ==========')
                    self.currentParkingID = p
                    parking = self.parkings[p]
                    if not self.currentParkingID:
                        ret , frame = self.cap.read()
                    else:
                        print(f'>Getting remote Parking ID {p} from source: {parking["source"]}')
                        try:
                            frame = self.get_remote_image()
                        except:
                            continue
                    print('>Detecting parking spaces in the frame.')
                    parking['image'], parking['detections'] = self.detect_frame(frame)
                    print('Detect OK!')
                    self.frame_count += 1
                    if self.test:continue
                    cv2.imshow('Processed Frame with Detections', parking['image'])
                    print(parking['detections'])
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    time.sleep(1)
                print(f'>Check API ... ')
                if self.readyToSend:
                    print('Preparing parkings data to be sent to the API.')
                    self.parkingsSendCopy = self.prepare_parkings_data(self.parkings)
                    self.update_API(self.parkingsSendCopy)
                else:
                    print(f'>{elapsed_time}s...')
                start_time = current_time
                if self.test  :
                    break
            except KeyboardInterrupt:
                self.readyToSend = -1
                break
            except Exception as e:
                print("!!An exception occurred: {}".format(e))
                self.readyToSend = -1
                self.cap.release()
                cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detection Module")
    parser.add_argument('--model', type=str, default='best.pt', help="Chemin vers le fichier de modèle.")
    parser.add_argument('--video', type=str, default='', help="Chemin vers le fichier vidéo.")
    parser.add_argument('--camera', action='store_true', help="Utiliser la caméra pour la détection.")
    parser.add_argument('--cameraid', type=int, default=1, help="ID de la caméra à utiliser.")
    parser.add_argument('--test', action='store_true', help="Mode test, arrête la boucle principale après un cycle.")  
    args = parser.parse_args()
    p = DetectionModule(model_path=args.model, video_path=args.video, camera=args.camera, cameraid=args.cameraid, test=args.test)
    p.runRemoteSource()
