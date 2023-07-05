from flask import Flask, render_template, request, redirect, url_for, session
import ibm_db
import json
import requests
import os
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import webbrowser


conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=b1bc1829-6f45-4cd4-bef4-10cf081900bf.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=32304;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=dns98308;PASSWORD=ywkNIOD357Fmbzc9", " "," ")
print(conn)

app=Flask(__name__)


slight = ["slight_scratch","slight_deformation","car_light_crack","sdie_mirror_scratch","side_mirror_crack","side_mirror_drop_off"]
moderate = ["fender/headlight_damage","fender/bumper_damage","car_light_severe_crack","car_light_damage","windshield_damage"]
severe = ["severe_scratch","medium_deformation","severe_deformation","crack_and_hole",]

#default home page or route
@app.route('/')
def index():
    return render_template('index.html')



@app.route('/hero')
def home():
    return render_template("index.html")


#login page
@app.route('/login1')
def login():
    return render_template('login1.html')

@app.route('/hero')
def hom11():
    return render_template('index.html')

@app.route('/about')
def home2():
    return render_template('index.html')

# Registration page routing

@app.route('/chk',methods=['POST'])
def register():
    x = [x for x in request.form.values()]
    print(x)
    name=x[0]
    email=x[1]
    password=x[2]
    sql = "SELECT * FROM register WHERE email =?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt,1,email)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    print(account)
    if account:
        return render_template('login1.html', pred="You are already a member, please login using your details")
    else:
        insert_sql = "INSERT INTO  REGISTER VALUES (?, ?, ?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, name)
        ibm_db.bind_param(prep_stmt, 2, email)
        ibm_db.bind_param(prep_stmt, 3, password)
        ibm_db.execute(prep_stmt)
        return render_template('login1.html', pred="Registration Successful, please login using your details")
       
          
    
@app.route('/login1',methods=['POST'])
def loginpage():
    email = request.form['email']
    pswd = request.form['pswd']
    sql = "SELECT * FROM login WHERE email =? AND password=?"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt,1,email)
    ibm_db.bind_param(stmt,2,pswd)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    print (account)
    print(email,pswd)
    if account:
            return render_template('login1.html', pred="Login unsuccessful")
    else:
        return render_template('login1.html', pred="Login unsuccessful. Incorrect username / password !") 
      

@app.route('/test')
def prediction():
    return render_template('test.html')

@app.route('/result',methods = ['POST'])
def abcd():
    if request.method=="POST":
       f=request.files['image']
       basepath=os.path.dirname(__file__) #getting the current path i.e where app.py is present
       #print("current path",basepath)
       filepath=os.path.join(basepath,'uploads',f.filename) #from anywhere in the system we can give image but we want that image later  to process so we are saving it to uploads folder for reusing
       #print("upload folder is",filepath)
       f.save(filepath)
    # connecting with cloud object storage
    
       COS_ENDPOINT = "https://s3.ams03.cloud-object-storage.appdomain.cloud"
       COS_API_KEY_ID = "dPpdD7OBa3PUMHEAul9MHASfMlwJgpd2nsJmmTf2cg34"
       COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/d019e61ab9df47e1b2be8c12bc196f34:78bb793d-f985-443c-90bc-fe0c8bf2f469::"
       cos = ibm_boto3.client("s3",ibm_api_key_id=COS_API_KEY_ID,ibm_service_instance_id=COS_INSTANCE_CRN, config=Config(signature_version="oauth"),endpoint_url=COS_ENDPOINT)
       cos.upload_file(Filename= filepath,Bucket='srikanthtest',Key='test.jpg')
       
       url = "https://vehicle-damage-assessment.p.rapidapi.com/run"

       payload = {"draw_result": True,"image": "https://srikanthtest.s3.ams03.cloud-object-storage.appdomain.cloud/test.jpg"}
       headers = {"content-type": "application/json","X-RapidAPI-Key": "080d896cfemsh8f31dd900f9473bp1b1177jsncbe24a43d48b","X-RapidAPI-Host": "vehicle-damage-assessment.p.rapidapi.com"}

       response = requests.request("POST", url, json=payload, headers=headers)
       output = response.json() 
       print(output)
       url = output['output_url']
  
# then call the default open method described above
       
       
       webbrowser.open(url)
       cos.upload_file(Filename= "result/test.jpg",Bucket='srikanthtest',Key='result.jpg')
       a =0
       b=0
       c=0
       l=[]
       for i in range(0,len(output['output']["elements"])):
           d = output['output']["elements"][i]["damage_category"]
           l.append(d)
       for i in range(0,len(l)):
           for j in range(0,len(slight)):
               if l[i]==slight[j]:
                   a = a+1
       for i in range(0,len(l)):
           for j in range(0,len(moderate)):
               if l[i]==moderate[j]:
                   b = b+1
       for i in range(0,len(l)):
           for j in range(0,len(severe)):
               if l[i]==severe[j]:
                   c = c+1
       percentage = (a*30 + b*50 + c*80)/(a+b+c)
       damage_parts = set()
       for i in range(0,len(output['output']["elements"])):
           d = output['output']["elements"][i]["damage_location"]
           damage_parts.add(d)
       damage_parts
       damage_parts = list(damage_parts)
       if percentage<30:
           result = "Estimated cost is" +" " + "20" +"-" + "30" + "% "+ " "  + "of total cost of the parts displayed in the image"
       elif percentage<50:
           result = "Estimated cost is" +" " + "30" +"-" + "50" + "% "+ " "  + "of total cost of the parts displayed in the image"
       else:
           result = "Estimated cost is" +" " + "55" +"-" + "80" + "% "+ " "  + "of total cost of the parts displayed in the image"
       print(result)
       
    return  render_template('result.html',pred = result)
     

@app.route('/')
def home31():
    return render_template('index.html')


@app.route('/about')
def home4():
    return render_template('index.html')

@app.route('/logout')
def logout():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)
