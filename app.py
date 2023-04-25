import json
import base64
import os
import argparse
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

def load_infos():
    if os.path.exists('infos.json'):
        with open('infos.json', 'r') as f:
            return json.load(f)
    else:
        return {}
infos = load_infos()

def save_infos(infos):
    with open('infos.json', 'w') as f:
        json.dump(infos, f)
    load_infos()

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
            images_directory = "/static/images/"
        if not os.path.exists(images_directory):
            os.makedirs(images_directory)

        # Save the image
        with open(f"static/images/camera_{outer_key}.jpg", "wb") as f:
            f.write(image_data)
            inner_dict['image'] = f"/images/camera_{outer_key}.jpg"
    infos['parkings'] = my_dict['parkings'].copy()
    infos["current_parking_id"] = my_dict["current_parking_id"]
    infos["number_of_parkings"] = len(my_dict['parkings'])
    infos["test"] = my_dict["test"]

    save_infos(infos)
    infos=load_infos()

    return jsonify({'message': 'Status updated successfully'})

@app.route('/', methods=['GET'])
def index():
    if infos:
        return render_template('index.html', my_dict=infos)
    else:
        return jsonify({'message': 'No infos'})
@app.route('/map', methods=['GET'])
def map():
    if infos:
        return render_template('map.html', my_dict=infos)
    else:
        return jsonify({'message': 'No infos'})

@app.route('/status/<parking_id>', methods=['GET'])
def get_parking_status_by_id(parking_id):
    parkings = infos.get('parkings', {})
    if parking_id in parkings:
        response = jsonify(parkings[parking_id])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    else:
        return jsonify({'message': f'No parking found with ID {parking_id}'})

@app.route('/currentID', methods=['POST', 'GET'])
def handle_parking_id():
    if request.method == 'POST':
        current_parking_id = request.json.get("current_parking_id")
        if current_parking_id is not None:
            infos["current_parking_id"] = current_parking_id
            save_infos(infos)
            return jsonify({'message': 'Current parking ID updated successfully'})
        else:
            return jsonify({'message': 'Invalid data provided'}), 400
    elif request.method == 'GET':
        current_parking_id = infos.get("current_parking_id")
        if current_parking_id is not None:
            response = jsonify({"current_parking_id": current_parking_id})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            return jsonify({'message': 'Current parking ID not found'}), 404

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='0.0.0.0', help='The host to bind to')
    parser.add_argument('--port', type=int, default=80, help='The port to listen on')
    args = parser.parse_args()
    port = int(os.environ.get('WEBSITE_PORT', args.port))
    app.run(host=args.host, port=port, debug=True)

if __name__ == '__main__':
    main()
