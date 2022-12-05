from flask import Flask
from flask_cors import CORS, cross_origin
from flask import request
import os
from PIL import Image
import base64
from io import BytesIO
import cv2
from datetime import datetime
# from training import *
app = Flask(__name__)

# Apply Flask CORS
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def convertBase64ToImage(encoded_data, path, count):
    new_encoded_data = encoded_data[encoded_data.index(",")+1:]
    decoded_data = base64.b64decode((new_encoded_data))

    path_file = str(path + str(count) + '{}.jpg'.format(str(datetime.now())[:-7].replace(":", "-").replace(" ", "-") + str(count)))

    img = Image.open(BytesIO(decoded_data))
    out_jpg = img.convert("RGB")

    out_jpg.save(path_file)


@app.route('/add', methods=['POST'] )
@cross_origin(origin='*')
def add_process():
    dataReq = request.get_json()

    directory = ROOT_DIR+"/dataset/"+str(dataReq['name'])+"/"
    if (os.path.isdir(directory) == False):
        os.mkdir(directory)
    for i, imgBase64 in enumerate(dataReq['image']):
        convertBase64ToImage(imgBase64,directory,i)

    return ""

if __name__ == '__main__':
    app.run(host='127.0.0.1', port='9000')