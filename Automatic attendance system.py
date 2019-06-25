# -*- coding: cp949 -*-  #�ѱ������Ϸ��� �ʿ��Ѱ� ��

from flask import Flask, render_template, Response, redirect, url_for, request, send_file

from picamera import PiCamera

import pymysql.cursors
import io
import time
import boto3
import json
import os
from datetime import datetime

camera = PiCamera()

camera.resolution = (640 , 480)

app = Flask(__name__)


def get_frame():

    stream = io.BytesIO()

    camera.capture(stream, 'jpeg', use_video_port=True)

    stream.seek(0)

    return stream.read()


@app.route('/')

def main():

    return render_template('index.html')




def gen():

    while True:

        frame = get_frame()

        yield (b'--frame\r\n'

               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')




@app.route('/video_feed')

def video_feed():

    return Response(gen(),

                    mimetype='multipart/x-mixed-replace; boundary=frame')




@app.route('/index', methods = ['POST', 'GET']) 

def index():
        now = datetime.now() #���� ��¥�� �ð� �����´�.
        
        if request.method == 'GET': #GET�� ������ ����


            time.sleep(1) #1�ʰ� ���
        
            camera.capture('/home/pi/Desktop/image.jpg') #��Ĭ

            time.sleep(1) #1�ʰ� ���

            conn = pymysql.connect(host='localhost',
                    user='phpmyadmin',
                    password='123123',
                    db='phpmyadmin',
                    charset='utf8mb4')  #�����ͺ��̽� ����
            
            fd=open('/home/pi/Desktop/image.jpg', 'rb') #������ ����.
            byteBuffer = bytearray(fd.read()) #����Ʈ�迭�� �޾ƹ�����.
            fd.close() #������ �ݴ´�.

            bucket='asd123123'

            for i in range(1, 7 ,1): #��ø for�� -- �Ʒ� < for faceMatch in response['FaceMatches'] > ����
                    targetFile= str(i)+".jpg" 
                    #print targetFile -->> 1.jpg 2.jpg ....

                    client=boto3.client('rekognition','us-east-2')

                    try:
                        response=client.compare_faces(SimilarityThreshold=70,      #�󱼺��Ѵ�.
                              SourceImage={'Bytes': byteBuffer}, #�̹����� ����Ʈ�迭�� �޴´�.
                              TargetImage={'S3Object':{'Bucket':bucket,'Name':targetFile}})
                        
                    except:
                        return render_template('fail.html')  #���ΰ��� �� Ű�� �ڵ�

                    

                    for faceMatch in response['FaceMatches']: 
                        #confidence = str(faceMatch['Face']['Confidence']) #���ڿ��� �ٲٴ� �ǵ� ������ ���� ������ �ʴ´�.
                        confidence = faceMatch['Face']['Confidence'] #�ؿ��� ������ float������ �޾ƾ� �Ѵ�.
                        if confidence>95:
                            image = str(i)+".jpg"
                                
                            print(image) #S3�� �ִ� ������ ���� Ȯ��
                            print(("%.2f" % confidence) + '%' + " ��ġ") #�Ҽ��� 2�ڸ����� ��Ÿ������ �����ߴ�.
                            try:     #�����ͺ��̽� ���ǹ�
                                with conn.cursor() as cursor:
                                    sql = 'UPDATE aws SET attendent = %s WHERE picture = %s' # attendent / picture �Ѵ� ���ڿ���
                                    sql2 = "select * from aws where picture = %s"
                   
                                    cursor.execute(sql, (now, 'https://s3.us-east-2.amazonaws.com/asd123123/' + str(i) +'.jpg')) #������ ������ ���� �̾Ƴ��� ���ÿ� �⼮���� attendent ĭ��
                                    cursor.execute(sql2, 'https://s3.us-east-2.amazonaws.com/asd123123/' + str(i) +'.jpg')

                                    conn.commit()      # X (�⼮ ����) ���� �ð� ��� (�⼮ ����) ���� ����ȴ�.

                                    rows = cursor.fetchall() #������� �迭�� ����.
                                            
                            finally:
                                conn.close()
                                return render_template('result.html',a='https://s3.us-east-2.amazonaws.com/asd123123/'+image,b=rows)  #�񱳰�� �� Ű�� �ڵ�

            return render_template('fail.html')  #���ΰ��� �� Ű�� �ڵ�                    

       
        
    #return redirect('http://192.168.0.12:5001/aws') #�⼮�� �� Ű�� �ڵ�


@app.route('/capture')  #�Կ��� �̹����� ���� ���� �Լ�

def capture():

    #camera.capture('/home/pi/Desktop/image.jpg')

    return send_file('/home/pi/Desktop/image.jpg')



@app.route('/result') #���â �� ���ִ� �Լ�

def result():

    return render_template('result.html')



@app.route('/aws') #�⼮�� �� ���ִ� �Լ�

def aws():

    # MySQL Connection ����
    conn = pymysql.connect(host='localhost', user='phpmyadmin', password='123123',
                           db='phpmyadmin', charset='utf8')
    # Connection ���κ��� Cursor ����
    curs = conn.cursor()
     
    # SQL�� ����
    sql = "select * from aws"
    curs.execute(sql)
     
    # ����Ÿ Fetch
    rows = curs.fetchall() #������� �迭�� ����.
     
    # Connection �ݱ�
    conn.close()

    return render_template('aws.html',a=rows)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, threaded=True)  #debug=True


