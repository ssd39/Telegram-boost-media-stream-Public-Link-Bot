from flask import Flask
from flask import request
from telethon import TelegramClient
import time
import threading
import requests
import os
import string
import random
import boto3
from telethon.tl.types import DocumentAttributeFilename
import asyncio
import shutil

bot=None
#following all credentials are dummy
heroku_url="https://xyz.herokuapp.com/ping"
#telegram api
api_id = 122323424324
api_hash = '123455454545'
phone_number='+9199999999999'
#bot_usernmae
username='xyz_bot'
bucket="your aws bucket name"
os.environ["AWS_ACCESS_KEY_ID"] = "your aws access key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your aws secret key"
bot_token="12324234234:dsfjbsdfbsdjfbhjsdjbdfbjsdfj"
#telegram bot api with access token
telegram_bot_url="https://api.telegram.org/bot12324234234:dsfjbsdfbsdjfbhjsdjbdfbjsdfj/"
#first time coversion of bot with main telegram account
account_id=153212534

download_progess=[]
download_pending_queue=[]
upload_progres=[]
upload_pending_queue=[]
app = Flask(__name__)
s3 = boto3.client('s3')


def id_generator(size=6, chars=string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))

def telegram_new_session():
    global bot
    try:
        new_sess_db="mybot_"+id_generator()
        shutil.copy("mybot_.session",new_sess_db+".session")
        botx = TelegramClient(new_sess_db, api_id, api_hash)
        botx.loop.run_until_complete(botx.connect())
        if not botx.loop.run_until_complete(botx.is_user_authorized()):
            botx.loop.run_until_complete(botx.send_code_request(phone_number))
            botx.loop.run_until_complete(botx.sign_in(phone_number, input('Enter code: ')))
        botx.start()
        return botx
    except Exception as e:
        print("While creating new session",e)
        return bot


class MediaUploader:
    def __init__(self,filename):
        self.filename=filename
        self.key=self.id_generator(8)+"/"+self.id_generator()+"."+filename.split(".")[-1]
        self.last=0
        self.last_time=time.time()
        self.upload_speed="0 kb/s"
        self.percentage="0%"
        self.last_ping=time.time()
        self.total=int(os.path.getsize(filename))
        self.url="https://{}.s3.amazonaws.com/{}".format(bucket,self.key)

    def id_generator(self,size=6, chars=string.ascii_lowercase +string.ascii_uppercase+ string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    def __call__(self, current):
        now=time.time()
        if now-self.last_ping>=120:
            self.last_ping=now
            try:
                requests.get(heroku_url)
            except:
                pass
        td=now-self.last_time
        bd=int(current)
        self.last+=int(current)
        self.last_time=now
        self.upload_speed=str(round((bd/td)/1000))+" kb/s"
        self.percentage=str(round((self.last*100)/self.total))+"%"
        print("Upload Progress:",self.filename,self.upload_speed,self.percentage)

    def upload(self):
        try:
            s3.upload_file(self.filename, bucket, self.key,ExtraArgs={'ACL': 'public-read'},Callback=self)
            print(self.url)
        except Exception as e:
            print(e)


class MediaDownloader:
    def __init__(self,file_name,bot,message):
        self.file_name=file_name
        self.bot=bot
        self.message=message
        self.last=0
        self.last_time=time.time()
        self.download_speed="0 kb/s"
        self.percentage="0%"
        self.last_ping=time.time()

    def progress(self,current,total):
        now=time.time()
        if now-self.last_ping>=120:
            self.last_ping = now
            try:
                requests.get(heroku_url)
            except:
                pass
        td=now-self.last_time
        bd=current-self.last
        self.last=current
        self.last_time=now
        self.download_speed=str(round((bd/td)/1000))+" kb/s"
        self.percentage=str(round((current*100)/total))+"%"
        print("Download Progress:",self.file_name,self.download_speed,self.percentage)

    def download(self):
        self.bot.loop.run_until_complete(self.bot.download_media(message=self.message,progress_callback=self.progress))

def upload_task(fwd_id,file_name):
    if len(upload_progres) <5:
        up=MediaUploader(file_name)
        upload_progres.append({"file_name": file_name, "class": up})
        up.upload()
        upload_progres.remove({"file_name": file_name, "class": up})
        os.remove(file_name)
        try:
            requests.get(telegram_bot_url+"sendMessage?chat_id={}&text={}".format(fwd_id,file_name+"\n"+up.url))
        except:
            pass
        if len(upload_pending_queue)>=1:
            d=upload_pending_queue.pop(0)
            t1 = threading.Thread(target=upload_task, args=(d["fwd_id"],d["file_name"],))
            t1.start()
    else:
        upload_pending_queue.append({"file_name":file_name,"fwd_id":fwd_id})

def download_task(bot,event_loop,fwd_id,message):
    print("NEW THREAD")
    asyncio.set_event_loop(event_loop)
    if not bot:
        bot=telegram_new_session()
    if len(download_progess)<5:
        file_name=""
        for d in message.media.document.attributes:
            if type(d)==DocumentAttributeFilename:
                file_name=d.file_name
                break
        md=MediaDownloader(file_name,bot,message)
        download_progess.append({"class":md,"message":message})
        md.download()
        download_progess.remove({"class":md,"message":message})
        if len(download_pending_queue)>=1:
            dk=download_pending_queue.pop(0)
            t = threading.Thread(target=download_task, args=(bot,event_loop,dk["fwd_id"],dk["message"],))
            t.start()
        t1 = threading.Thread(target=upload_task, args=(fwd_id,file_name,))
        t1.start()
    else:
        download_pending_queue.append({"fwd_id":fwd_id,"message":message})

def telegram_login():
    global bot
    bot = TelegramClient('mybot_', api_id, api_hash)
    bot.loop.run_until_complete(bot.connect())
    if not bot.loop.run_until_complete(bot.is_user_authorized()):
        bot.loop.run_until_complete(bot.send_code_request(phone_number))
        bot.loop.run_until_complete(bot.sign_in(phone_number, input('Enter code: ')))
    bot.start()



def telegram_read_chat(username):
    messages=bot.loop.run_until_complete(bot.get_messages(username, limit=1))
    return messages[0]



def telegram_send_message(username,message):
    entity = bot.loop.run_until_complete(bot.get_entity(username))
    bot.loop.run_until_complete(bot.send_message(entity=entity, message=message))

def telegram_test():
    #testing telegram connection
    bot.loop.run_until_complete(bot.send_message('me', 'Hello, myself!'))

@app.route('/ping')
def ping():
    return "pong"

@app.route('/')
def home():
    return "Hello World!"

@app.route('/webhook', methods=["POST"])
def webhook():
    try:
        data=request.get_json()
        if data["message"]["from"]["id"]==account_id:
            pass
        else:
            r=requests.get(telegram_bot_url+"forwardMessage?chat_id={}&from_chat_id={}&message_id={}".format(account_id,data["message"]["from"]["id"],data["message"]["message_id"]))
            print(r.text)
            message = telegram_read_chat(username)
            if message.media:
                event_loop=asyncio.new_event_loop()
                t = threading.Thread(target=download_task, args=(None,event_loop,data["message"]["from"]["id"],message,))
                t.start()
    except Exception as e:
        print(e)
    return "True"

if __name__ == '__main__':
    telegram_login()
    app.run(host='0.0.0.0',port=os.environ.get('PORT') or 8080)



