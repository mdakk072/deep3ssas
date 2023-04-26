import os
import json
import base64
from flask import Flask, request, jsonify
import requests
HOST='http://127.0.0.1'
HOST='http://mdakk072.pythonanywhere.com'

app = Flask(__name__)

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

infos = load_infos()

@app.route('/parking_structure', methods=['GET'])
def get_parking_structure():
    with open('parking_structure.json', 'r') as f:
        parking_structure = json.load(f)
    return jsonify(parking_structure)

@app.route('/status', methods=['GET'])
def get_status():
    response = jsonify(infos)
    response.headers.add('Access-Control-Allow-Origin', '*')

    return response

@app.route('/status', methods=['POST'])
def update_status():
    global infos
    my_dict = request.get_json()

    for outer_key, inner_dict in my_dict['parkings'].items():
        if inner_dict.get('image') is not None:
            base64_image = inner_dict['image']
            image_data = base64.b64decode(base64_image)
            script_path = os.path.abspath(__file__)
            images_directory = os.path.join(os.path.dirname(script_path), "static", "images")
        if not os.path.exists(images_directory):
            os.makedirs(images_directory)

        with open(f"static/images/camera_{outer_key}.jpg", "wb") as f:
            f.write(image_data)
            inner_dict['image'] = f"{HOST}/static/images/camera_{outer_key}.jpg"            
            print( inner_dict['image'] )


    infos['parkings'] = my_dict['parkings']
    infos["current_parking_id"] = my_dict["current_parking_id"]
    infos["number_of_parkings"] = len(my_dict['parkings'])
    infos["test"] = my_dict["test"]

    save_infos(infos)
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
