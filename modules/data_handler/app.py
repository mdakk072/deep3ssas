import os
import json
import base64
import sys
from flask import Flask, request, jsonify
import datetime
try:
    from azure_blob_storage import AzureBlobStorage
    import postgresql_handler as postgresql_handler
except:
    sys.path.append('.')
    from modules.data_handler.azure_blob_storage import AzureBlobStorage
    import modules.data_handler.postgresql_handler as postgresql_handler
    
import xml.etree.ElementTree as ET

def load_infos():
    try:
        if os.path.exists('infos.json'):
            with open('infos.json', 'r') as f:
                return json.load(f)
    except:
        with open('infos.json', 'w') as f:
            json.dump({}, f)
        return {}

def save_infos(infos):
    with open('infos.json', 'w') as f:
        json.dump(infos, f)

def convert_to_yolo_format(label, img_width=640, img_height=640):
    class_id = label['class']
    x_center = (label['xmin'] + label['xmax']) / 2
    y_center = (label['ymin'] + label['ymax']) / 2
    width = label['xmax'] - label['xmin']
    height = label['ymax'] - label['ymin']
    x_center /= img_width
    y_center /= img_height
    width /= img_width
    height /= img_height
    return (class_id, x_center, y_center, width, height)

def find_file(filename, default_path=None):
    if default_path is None:
        default_path = os.getcwd()
    file_path = os.path.join(default_path, filename)
    if os.path.isfile(file_path):
        return file_path
    script_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_directory, filename)
    if os.path.isfile(file_path):
        return file_path
    return None

def get_credentials(filename='config.xml'):
    env_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'APIHOSTNAME', 'AZURE_CONNECTION_STRING', ]
    credentials = {var: os.environ.get(var) for var in env_vars}

    config_file = find_file(filename)
    if config_file:
        tree = ET.parse(config_file)
        root = tree.getroot()
        for var in env_vars:
            if credentials[var] is None:
                elem = root.find(var)
                if elem is not None:
                    credentials[var] = elem.text
                else:
                    print(f"Warning: {var} not found in config.xml")

    missing_vars = [var for var in env_vars if credentials[var] is None]
    if missing_vars:
        raise ValueError(f"Missing credentials: {', '.join(missing_vars)}")

    return credentials
credentials=get_credentials()

DB_HOST =                   credentials['DB_HOST']
DB_PORT =                   credentials['DB_PORT']
DB_NAME =                   credentials['DB_NAME']
DB_USER =                   credentials['DB_USER']
DB_PASSWORD =               credentials['DB_PASSWORD']
HOSTNAME=                   credentials['APIHOSTNAME']
AZURE_CONNECTION_STRING =   credentials['AZURE_CONNECTION_STRING']

app = Flask(__name__)

infos = load_infos()

@app.route('/parking_structure', methods=['GET'])
def get_parking_structure():
    with open('parking_structure.json', 'r') as f:
        parking_structure = json.load(f)
    print(postgresql_handler.get_all_parkings())
    return jsonify(parking_structure)

@app.route('/status', methods=['GET'])
def get_status():
    response = jsonify(infos)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
@app.route('/test', methods=['GET'])
def get_status2():
    response = jsonify([HOSTNAME])
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
@app.route('/status', methods=['POST'])
def update_status():
    global infos
    my_dict = request.get_json()
    conn=postgresql_handler.create_connection(database=DB_NAME,user=DB_USER,password=DB_PASSWORD,host=DB_HOST,port=DB_PORT,)
    azure_blob_storage = AzureBlobStorage(AZURE_CONNECTION_STRING)
    for outer_key, inner_dict in my_dict['parkings'].items():
        if inner_dict.get('image') is not None:
            base64_image = inner_dict['image']
            image_data = base64.b64decode(base64_image)
            script_path = os.path.abspath(__file__)
            images_directory = os.path.join(os.path.dirname(script_path), "static", "images")
            labels_directory = os.path.join(os.path.dirname(script_path), "static", "labels")
        if not os.path.exists(images_directory):
            os.makedirs(images_directory)
        if not os.path.exists(labels_directory):
            os.makedirs(labels_directory)
        image_directory = os.path.join(images_directory, f"camera_{outer_key}.jpg")
        label_directory = os.path.join(images_directory, f"camera_{outer_key}.txt")
        with open(image_directory, "wb") as f:
            f.write(image_data)
            inner_dict['image'] = f"{HOSTNAME}/static/images/camera_{outer_key}.jpg"            
        timestamp = datetime.datetime.utcnow()
        timezone_offset = inner_dict["sourceInfos"]["Timezone"]
        hours, minutes = map(int, timezone_offset.split(':'))
        offset = datetime.timedelta(hours=hours, minutes=minutes)
        timestamp = timestamp + offset
        timestamp_str = timestamp.strftime("%Y%m%d-%H%M%S")
        image_name=f"camera_{outer_key}_{timestamp_str}"
        image_dataDB={'image_name':image_name
                    , 'camera_id'                :outer_key
                    , 'date_taken'               :timestamp
                    , 'detection_count'          : inner_dict["detections"]["places"]
                    , 'corrected_detection_count':-1
                    , 'status'                   :"NEW"}
        postgresql_handler.insert_image(conn,image_dataDB)
        with open(label_directory, "w") as f:
            for label in inner_dict['labels']:
                class_id, x_center_norm, y_center_norm, width_norm, height_norm = convert_to_yolo_format(label)
                f.write(" ".join(str(x) for x in (class_id, x_center_norm, y_center_norm, width_norm, height_norm)) + "\n")
                postgresql_handler.insert_detection(conn, {
            "image_name"    : image_name,
            "xminimum"      : label["xmin"],
            "yminimum"      : label["ymin"],
            "xmaximum"      : label["xmax"],
            "ymaximum"      : label["ymax"],
            "x_center_norm" : x_center_norm,
            "y_center_norm" : y_center_norm,
            "width_norm"    : width_norm,
            "height_norm"   : height_norm,
            "confidence"    : label["confidence"],
            "class"         : label["class"]
        })
        postgresql_handler.upsert_parking(conn,inner_dict)
        azure_blob_storage.upload_image(image_directory, f"{image_name}.jpg")
        azure_blob_storage.upload_label(label_directory, f"{image_name}.txt")
    conn.close()
    
    infos['parkings'] = my_dict['parkings']
    infos["current_parking_id"] = my_dict["current_parking_id"]
    infos["number_of_parkings"] = len(my_dict['parkings'])
    infos["test"] = my_dict["test"]
    save_infos(infos)
    del azure_blob_storage
    del conn
    return jsonify({'message': 'Status updated successfully'})

@app.route('/currentID', methods=['POST'])
def update_current_parking_id():
    global infos
    data = request.get_json(force=True)
    infos['current_parking_id'] = data['current_parking_id']
    save_infos(infos)
    return jsonify({'status': 'success'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
