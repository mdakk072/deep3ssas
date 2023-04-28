import json
import os
import argparse
import requests
import time
from flask import Flask, jsonify , render_template

DATA_HANDLER_URL = "http://127.0.0.1"
DATA_HANDLER_URL = "https://deep3ssasapi.azurewebsites.net"
#DATA_HANDLER_URL = "https://mdakk072.pythonanywhere.com"
WAIT_TIME = 60#s
app = Flask(__name__)
last_refresh_time = time.time()



def load_infos():
    try:
        response = requests.get(f"{DATA_HANDLER_URL}/status")
        if response.status_code == 200:
            return response.json()
        else:
            return {}
    except Exception as e:
        print(f"Error fetching data from DataHandler: {e}")
        if os.path.exists('infos.json'):
            with open('infos.json', 'r') as f:
                return json.load(f)
        else:
            return {}

def save_infos(infos):
    with open('infos.json', 'w') as f:
        json.dump(infos, f)

def update_infos():
    global infos
    infos = load_infos()
    infos['last_update']=int(-1)

    save_infos(infos)


infos = load_infos()
update_infos()


@app.route('/status', methods=['GET'])
def get_status():
    global infos
    global last_refresh_time

    if time.time() - last_refresh_time >= WAIT_TIME:
        update_infos()
        #print(time.time() - last_refresh_time)
        last_refresh_time = time.time()
    infos['last_update']=int(time.time() - last_refresh_time)
    
        
    response = jsonify(infos)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/', methods=['GET'])
def index():
    global infos
    global last_refresh_time

    print(time.time() - last_refresh_time)

    if time.time() - last_refresh_time >= WAIT_TIME:
        print(time.time() - last_refresh_time)
        update_infos()

        last_refresh_time = time.time()
    infos['last_update']=int(time.time() - last_refresh_time)
    
    if infos:
        return render_template('index.html', my_dict=infos)
    else:
        return jsonify({'message': 'No infos'})

@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@app.route('/map', methods=['GET'])
def map():
    global infos
    global last_refresh_time
    if time.time() - last_refresh_time >= WAIT_TIME:
        
        update_infos()
        print(time.time() - last_refresh_time)

        last_refresh_time = time.time()
    infos['last_update']=int(time.time() - last_refresh_time)
    
    if infos:
        return render_template('map.html', my_dict=infos)
    else:
        return jsonify({'message': 'No infos'})

@app.route('/parkings', methods=['GET'])
def parkings():
    global infos
    global last_refresh_time
    if time.time() - last_refresh_time >= WAIT_TIME:
        update_infos()
        last_refresh_time = time.time()
    infos['last_update'] = int(time.time() - last_refresh_time)

    if infos:
        return render_template('parkings.html', my_dict=infos)
    else:
        return jsonify({'message': 'No infos'})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, default='0.0.0.0', help='The host to bind to')
    parser.add_argument('--port', type=int, default=80, help='The port to listen on')
    args = parser.parse_args()
    port = int(os.environ.get('WEBSITE_PORT', args.port))
    app.run(host=args.host, port=port, )



if __name__ == '__main__':

    

    main()
