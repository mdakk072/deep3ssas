import json
from flask import Flask, jsonify, request
from detection_module import DetectionModule,NumpyEncoder
import threading
import argparse
import os
app = Flask(__name__)
# Initialiser le module de détection
detection_module = DetectionModule()
# Fonction pour exécuter le module de détection dans un thread séparé
def run_detection_module():
    detection_module.runRemoteSource()

# Démarrer un thread pour exécuter le module de détection
detection_thread = threading.Thread(target=run_detection_module)
detection_thread.start()

@app.route('/current_parking_id', methods=['GET'])
def get_current_parking_id():
    return jsonify({"current_parking_id": detection_module.currentParkingID})

@app.route('/ready_to_send', methods=['GET'])
def get_ready_to_send():
    return jsonify({"ready_to_send": detection_module.readyToSend})

@app.route('/parking_structure', methods=['GET'])
def get_parking_structure():
    with open('parking_structure.json', 'r') as f:
        parking_structure = json.load(f)
    return jsonify(parking_structure)

@app.route('/detection_module_info', methods=['GET'])
def get_detection_module_info():
    module_info = {
        "fps_start": detection_module.fps_start,
        "frame_count": detection_module.frame_count,
        "colorStates": detection_module.colorStates,
        "strStates": detection_module.strStates,
        "readyToSend": detection_module.readyToSend,
        "proccess": detection_module.proccess,
        "frameTosend": detection_module.frameTosend,
        "currentParkingID": detection_module.currentParkingID,
        "test": detection_module.test,
    }
    return jsonify(module_info)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='0.0.0.0', help='The host to bind to')
    parser.add_argument('--port', type=int, default=80, help='The port to listen on')
    parser.add_argument('--mode', type=str, default='production', help='Run mode: development or production')
    args = parser.parse_args()
    port = int(os.environ.get('WEBSITE_PORT', args.port))

    if args.mode == 'development':
        app.config['ENV'] = 'development'
        app.config['DEBUG'] = True
    else:
        app.config['ENV'] = 'production'
        app.config['DEBUG'] = False

    app.run(host=args.host, port=port)


if __name__ == '__main__':
    main()
