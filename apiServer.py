from flask import Flask
from flask_cors import CORS, cross_origin
from flask import request,jsonify
from flask_mysqldb import MySQL
import os
from PIL import Image
import base64
from io import BytesIO
import cv2
import shutil
from datetime import datetime,date
from training import *
from recognize import *
app = Flask(__name__)

# Apply Flask CORS
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'face_recognition'

mysql = MySQL(app)

def convertBase64ToImage(encoded_data, path, count):
    new_encoded_data = encoded_data[encoded_data.index(",")+1:]
    decoded_data = base64.b64decode((new_encoded_data))

    path_file = str(path + str(count) + '{}.jpg'.format(str(datetime.now())[:-7].replace(":", "-").replace(" ", "-") + str(count)))

    img = Image.open(BytesIO(decoded_data))
    out_jpg = img.convert("RGB")

    out_jpg.save(path_file)


@app.route('/training', methods=['POST'] )
@cross_origin(origin='*')
def training_process():
    dataReq = request.get_json()
    cursor = mysql.connection.cursor()
    sql = "SELECT name,is_training FROM user_informations WHERE user_code='"+dataReq["code"]+"'"
    cursor.execute(sql)
    dataQuery = cursor.fetchone()
    if cursor.rowcount == 0:
        return jsonify(
            message="You have not registered an account with the system",
            status=0,
            data=[]
        )

    if(dataQuery[1] == 0):
        directory = ROOT_DIR+"/dataset/"+str(dataReq["code"])+"/"
        directory_image_face = ROOT_DIR+"/image_face/"+str(dataReq["code"])+"/"

        if (os.path.isdir(directory) == False):
            os.mkdir(directory)
        if (os.path.isdir(directory_image_face) == False):
            os.mkdir(directory_image_face)
        for i, imgBase64 in enumerate(dataReq['image']):
            convertBase64ToImage(imgBase64,directory,i)
            convertBase64ToImage(imgBase64,directory_image_face,i)

        is_trained = trainingFace()
        if(is_trained == 1):
            sql_update = "UPDATE user_informations SET is_training = %s WHERE user_code = %s"
            val_update = (1, str(dataReq["code"]))
            cursor.execute(sql_update, val_update)
            mysql.connection.commit()
            shutil.rmtree(directory)

            cursor.close()
            return jsonify(
                message="Get face recognition successful",
                status=200,
                data=dataQuery[0]
            )
        else:
            shutil.rmtree(directory)
            return jsonify(
                message="Get face recognition fail",
                status=0,
                data=[]
            )
    else:
        return jsonify(
            message="Get face recognition already",
            status=0,
            data=[]
        )

@app.route('/recognition', methods=['POST'] )
@cross_origin(origin='*')
def recognition_process():
    dataReq = request.get_json()
    faceRecognized = recognitionFace(dataReq["image"])
    print(faceRecognized)

    if(faceRecognized == "unknown"):
        return jsonify(
                message="Can not recognition face please try again",
                status=0,
                data=[]
            )
    else:

        cursor = mysql.connection.cursor()
        today = str(date.today())
        datetime_begin = today+" 00:00:00"
        datetime_end = today+" 23:59:59"

        sqlCheckAttendanced = "SELECT * FROM attendances WHERE user_code='" + faceRecognized + "' AND (datetime > '"+datetime_begin+"' AND datetime < '"+datetime_end+"') "

        cursor.execute(sqlCheckAttendanced)
        dataQuery = cursor.fetchone()

        if cursor.rowcount != 0:
            print("You have already attendance")
            return jsonify(
                message="You have already attendance",
                status=0,
                data=[]
            )
        else:
            sqlGetIdUser = "SELECT user_id, user_code, name FROM user_informations WHERE user_code='"+faceRecognized+"'"
            cursor.execute(sqlGetIdUser)
            dataQuery = cursor.fetchone()

            user_id = int(dataQuery[0])
            datetime_now = str(datetime.now())
            datetime_pivot = today+" 08:00:00"
            is_late = 1 if (datetime_now > datetime_pivot) else 0

            sql_insert = "INSERT INTO attendances (user_id, user_code, datetime, is_late, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s)"
            sql_val = (user_id, str(faceRecognized), datetime_now, is_late,datetime_now,datetime_now)

            cursor.execute(sql_insert, sql_val)
            mysql.connection.commit()

            if cursor.lastrowid >= 0:
                print("Attendance successful")

                return jsonify(
                    message="Attendance successful",
                    status=200,
                    data=[
                        {
                            "user_id":dataQuery[0],
                            "user_code":dataQuery[1],
                            "name":dataQuery[2],
                            "datetime":datetime_now
                        }
                    ]
                )
            else:
                print("Attendance fail, Try again")
                return jsonify(
                    message="Attendance fail, Try again",
                    status=0,
                    data=[]
                )
        cursor.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port='9000')