# app.py - الإصدار المصحح لـ Railway
import requests, os, sys, jwt, pickle, json, binascii, time, urllib3, base64, datetime, re, socket, threading
import asyncio
import logging
from protobuf_decoder.protobuf_decoder import Parser
from byte import *
from byte import xSendTeamMsg
from byte import Auth_Chat
from xHeaders import *
from datetime import datetime
from google.protobuf.timestamp_pb2 import Timestamp
from concurrent.futures import ThreadPoolExecutor
from threading import Thread
from flask import Flask, request, jsonify

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  

# قاموس لتخزين جميع العملاء المتصلين
connected_clients = {}
connected_clients_lock = threading.Lock()

# قاموس لتخزين أهداف السبام النشطة
active_spam_targets = {}
active_spam_lock = threading.Lock()

# إعدادات Flask API
app = Flask(__name__)

class SimpleAPI:
    def __init__(self):
        self.running = True
        
    def process_spam_command(self, target_id, duration_minutes=None):
        """معالجة أمر السبام"""
        try:
            # التحقق من صحة user_id
            if not ChEck_Commande(target_id):
                return {"status": "error", "message": "❌ user_id غير صالح"}
                
            # بدء السبام
            with active_spam_lock:
                if target_id not in active_spam_targets:
                    active_spam_targets[target_id] = {
                        'active': True,
                        'start_time': datetime.now(),
                        'duration': duration_minutes
                    }
                    threading.Thread(target=spam_worker, args=(target_id, duration_minutes), daemon=True).start()
                    message = f"✅ تم بدء السبام على المستخدم: {target_id}"
                    if duration_minutes:
                        message += f" لمدة {duration_minutes} دقيقة"
                    logger.info(message)
                    return {"status": "success", "message": message}
                else:
                    return {"status": "error", "message": f"⚠️ السبام يعمل بالفعل على المستخدم: {target_id}"}
                    
        except Exception as e:
            logger.error(f"Error in process_spam_command: {e}")
            return {"status": "error", "message": f"❌ خطأ في معالجة الأمر: {str(e)}"}
            
    def process_stop_command(self, target_id):
        """معالجة أمر الإيقاف"""
        try:
            # إيقاف السبام
            with active_spam_lock:
                if target_id in active_spam_targets:
                    del active_spam_targets[target_id]
                    message = f"🛑 تم إيقاف السبام على المستخدم: {target_id}"
                    logger.info(message)
                    return {"status": "success", "message": message}
                else:
                    return {"status": "error", "message": f"ℹ️ لا يوجد سبام نشط على المستخدم: {target_id}"}
                    
        except Exception as e:
            logger.error(f"Error in process_stop_command: {e}")
            return {"status": "error", "message": f"❌ خطأ في معالجة الأمر: {str(e)}"}
            
    def get_status(self):
        """الحصول على الحالة"""
        try:
            with active_spam_lock:
                active_targets = list(active_spam_targets.keys())
                active_targets_info = []
                for target_id in active_targets:
                    info = active_spam_targets[target_id]
                    duration_info = ""
                    if info['duration']:
                        elapsed = datetime.now() - info['start_time']
                        remaining = info['duration'] * 60 - elapsed.total_seconds()
                        if remaining > 0:
                            duration_info = f" ({int(remaining/60)} دقيقة متبقية)"
                    active_targets_info.append(f"{target_id}{duration_info}")
                    
            with connected_clients_lock:
                accounts_count = len(connected_clients)
                accounts_list = list(connected_clients.keys())
                
            status_data = {
                "active_targets_count": len(active_targets),
                "active_targets": active_targets_info,
                "connected_accounts_count": accounts_count,
                "connected_accounts": accounts_list
            }
            
            return {"status": "success", "data": status_data}
            
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            return {"status": "error", "message": f"❌ خطأ في الحصول على الحالة: {str(e)}"}

def spam_worker(target_id, duration_minutes=None):
    """دالة العمل لإرسال سبام إلى هدف معين"""
    logger.info(f"🚀 بدء السبام على الهدف: {target_id}" + (f" لمدة {duration_minutes} دقيقة" if duration_minutes else ""))
    
    start_time = datetime.now()
    
    while True:
        with active_spam_lock:
            if target_id not in active_spam_targets:
                logger.info(f"⏹️ توقف السبام على الهدف: {target_id}")
                break
                
            # التحقق من انتهاء المدة إذا كانت محددة
            if duration_minutes:
                elapsed = datetime.now() - start_time
                if elapsed.total_seconds() >= duration_minutes * 60:
                    logger.info(f"⏰ انتهت مدة السبام على الهدف: {target_id}")
                    del active_spam_targets[target_id]
                    break
                
        try:
            send_spam_from_all_accounts(target_id)
            time.sleep(0.1)  # وقت انتظار قصير بين كل دورة سبام
        except Exception as e:
            logger.error(f"❌ خطأ في السبام على {target_id}: {e}")
            time.sleep(1)

def send_spam_from_all_accounts(target_id):
    """إرسال سبام من جميع الحسابات المتصلة"""
    with connected_clients_lock:
        for account_id, client in connected_clients.items():
            try:
                # التحقق من أن العميل لديه اتصال نشط
                if (hasattr(client, 'CliEnts2') and client.CliEnts2 and 
                    hasattr(client, 'key') and client.key and 
                    hasattr(client, 'iv') and client.iv):
                    
                    # إرسال السبام من الحساب
                    for i in range(5):  # تقليل عدد المحاولات لتجنب الأخطاء
                        try:
                            client.CliEnts2.send(SEnd_InV(1, target_id, client.key, client.iv))                           
                            client.CliEnts2.send(OpEnSq(client.key, client.iv))                            
                            client.CliEnts2.send(SPamSq(target_id, client.key, client.iv))
                        except (BrokenPipeError, ConnectionResetError, OSError) as e:
                            logger.warning(f"🔌 خطأ اتصال للحساب {account_id}: {e}")
                            break
                        except Exception as e:
                            logger.warning(f"⚠️ خطأ في الإرسال من الحساب {account_id}: {e}")
                            break
                else:
                    logger.warning(f"🔴 اتصال الحساب {account_id} غير نشط")
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال السبام من الحساب {account_id}: {e}")

# تعريف routes للـ API
api = SimpleAPI()

@app.route('/spam', methods=['GET'])
def start_spam():
    """بدء السبام على user_id معين"""
    target_id = request.args.get('user_id')
    duration = request.args.get('duration', type=int)
    
    if not target_id:
        return jsonify({"status": "error", "message": "⚠️ يرجى إدخال الـ user_id"})
    
    result = api.process_spam_command(target_id, duration)
    return jsonify(result)

@app.route('/stop', methods=['GET'])
def stop_spam():
    """إيقاف السبام على user_id معين"""
    target_id = request.args.get('user_id')
    
    if not target_id:
        return jsonify({"status": "error", "message": "⚠️ يرجى إدخال الـ user_id"})
    
    result = api.process_stop_command(target_id)
    return jsonify(result)

@app.route('/status', methods=['GET'])
def get_status():
    """الحصول على حالة النظام"""
    result = api.get_status()
    return jsonify(result)

@app.route('/accounts', methods=['GET'])
def get_accounts():
    """الحصول على قائمة الحسابات المتصلة"""
    try:
        with connected_clients_lock:
            accounts_count = len(connected_clients)
            accounts_list = list(connected_clients.keys())
            
        accounts_data = {
            "connected_accounts_count": accounts_count,
            "connected_accounts": accounts_list
        }
        
        return jsonify({"status": "success", "data": accounts_data})
        
    except Exception as e:
        logger.error(f"Error in get_accounts: {e}")
        return jsonify({"status": "error", "message": f"❌ خطأ في الحصول على الحسابات: {str(e)}"})

@app.route('/health', methods=['GET'])
def health_check():
    """فحص صحة التطبيق"""
    try:
        with connected_clients_lock:
            accounts_count = len(connected_clients)
        with active_spam_lock:
            spam_count = len(active_spam_targets)
            
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "accounts_connected": accounts_count,
            "active_spam_targets": spam_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return """
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🎯 نظام إدارة السبام</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            .endpoint {
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
            .method {
                font-weight: bold;
                color: #007bff;
            }
            .url {
                color: #28a745;
                word-break: break-all;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 نظام إدارة السبام</h1>
            <p>Endpoints المتاحة:</p>
            
            <div class="endpoint">
                <span class="method">GET</span> 
                <span class="url">/spam?user_id=123456789&amp;duration=5</span>
                <p>بدء السبام على user_id معين (duration اختياري - بالدقائق)</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> 
                <span class="url">/stop?user_id=123456789</span>
                <p>إيقاف السبام على user_id معين</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> 
                <span class="url">/status</span>
                <p>الحصول على حالة النظام</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> 
                <span class="url">/accounts</span>
                <p>الحصول على قائمة الحسابات المتصلة</p>
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> 
                <span class="url">/health</span>
                <p>فحص صحة التطبيق</p>
            </div>
        </div>
    </body>
    </html>
    """

def run_api():
    """تشغيل API"""
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"🌐 بدء تشغيل API على {host}:{port}...")
    
    # استخدام waitress للإنتاج بدلاً من Flask development server
    try:
        from waitress import serve
        logger.info("🚀 Using Waitress production server")
        serve(app, host=host, port=port)
    except ImportError:
        logger.warning("⚠️ Waitress not available, using Flask development server")
        app.run(host=host, port=port, debug=False)

def AuTo_ResTartinG():
    """إعادة التشغيل التلقائي"""
    time.sleep(6 * 60 * 60)  # 6 ساعات
    logger.info('🔄 إعادة التشغيل التلقائي للبوت...')
    ResTarT_BoT()
       
def ResTarT_BoT():
    """إعادة تشغيل البوت"""
    logger.info('🔄 إعادة تشغيل البوت...')
    python = sys.executable
    os.execl(python, python, *sys.argv)

def GeT_Time(timestamp):
    """الحصول على الوقت المنقضي"""
    last_login = datetime.fromtimestamp(timestamp)
    now = datetime.now()
    diff = now - last_login   
    d = diff.days
    h , rem = divmod(diff.seconds, 3600)
    m , s = divmod(rem, 60)    
    return d, h, m, s

def Time_En_Ar(t): 
    """تحويل الوقت من الإنجليزية إلى العربية"""
    return ' '.join(t.replace("Day","يوم").replace("Hour","ساعة").replace("Min","دقيقة").replace("Sec","ثانية").split(" - "))
    
# قراءة الحسابات من ملف accs.txt
ACCOUNTS = []

def load_accounts_from_file(filename="accs.txt"):
    """تحميل الحسابات من ملف"""
    accounts = []
    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith("#"):  # تجاهل الأسطر الفارغة والتعليقات
                    # افتراض أن التنسيق هو token:user_id أو user_id:token
                    if ":" in line:
                        parts = line.split(":")
                        if len(parts) >= 2:
                            # افتراض أن الجزء الأول هو user_id والثاني هو token/password
                            account_id = parts[0].strip()
                            password = parts[1].strip()
                            accounts.append({'id': account_id, 'password': password})
                    else:
                        # إذا لم يكن هناك :، افتراض أن السطر كله هو user_id فقط
                        accounts.append({'id': line.strip(), 'password': ''})
        logger.info(f"✅ تم تحميل {len(accounts)} حساب من {filename}")
    except FileNotFoundError:
        logger.error(f"❌ ملف {filename} غير موجود!")
    except Exception as e:
        logger.error(f"❌ حدث خطأ أثناء قراءة الملف: {e}")
    
    return accounts

# تحميل الحسابات من الملف
ACCOUNTS = load_accounts_from_file()

class FF_CLient():
    """فئة العميل الرئيسية"""

    def __init__(self, id, password):
        self.id = id
        self.password = password
        self.key = None
        self.iv = None
        self.Get_FiNal_ToKen_0115()     
            
    def Connect_SerVer_OnLine(self , Token , tok , host , port , key , iv , host2 , port2):
        """الاتصال بالخادم الثانوي"""
        try:
            self.AutH_ToKen_0115 = tok    
            self.CliEnts2 = socket.create_connection((host2 , int(port2)))
            self.CliEnts2.send(bytes.fromhex(self.AutH_ToKen_0115))                  
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال الثانوي: {e}")
            pass        
            
        while True:
            try:
                self.DaTa2 = self.CliEnts2.recv(99999)
                if '0500' in self.DaTa2.hex()[0:4] and len(self.DaTa2.hex()) > 30:	         	    	    
                    self.packet = json.loads(DeCode_PackEt(f'08{self.DaTa2.hex().split("08", 1)[1]}'))
                    self.AutH = self.packet['5']['data']['7']['data']
            except Exception as e:
                logger.debug(f"⚠️ خطأ في استقبال البيانات الثانوية: {e}")
                pass    	
                                                            
    def Connect_SerVer(self , Token , tok , host , port , key , iv , host2 , port2):
        """الاتصال بالخادم الرئيسي"""
        self.AutH_ToKen_0115 = tok    
        try:
            self.CliEnts = socket.create_connection((host , int(port)))
            self.CliEnts.send(bytes.fromhex(self.AutH_ToKen_0115))  
            self.DaTa = self.CliEnts.recv(1024)
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال الرئيسي: {e}")
            time.sleep(5)
            self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)
            return
                
        threading.Thread(target=self.Connect_SerVer_OnLine, args=(Token , tok , host , port , key , iv , host2 , port2), daemon=True).start()
        self.Exemple = xMsGFixinG('12345678')
        
        # تخزين المفتاح و IV للاستخدام لاحقاً
        self.key = key
        self.iv = iv
        
        # تسجيل العميل في القائمة العالمية
        with connected_clients_lock:
            connected_clients[self.id] = self
            logger.info(f"✅ تم تسجيل الحساب {self.id} في القائمة العالمية، عدد الحسابات الآن: {len(connected_clients)}")
        
        while True:      
            try:
                self.DaTa = self.CliEnts.recv(1024)   
                if len(self.DaTa) == 0 or (hasattr(self, 'DaTa2') and len(self.DaTa2) == 0):	            		
                    try:            		    
                        self.CliEnts.close()
                        if hasattr(self, 'CliEnts2'):
                            self.CliEnts2.close()
                        self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)                    		                    
                    except:
                        try:
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)
                        except:
                            self.CliEnts.close()
                            if hasattr(self, 'CliEnts2'):
                                self.CliEnts2.close()
                            ResTarT_BoT()	            
                                      
                if '/pp/' in self.input_msg[:4]:
                    self.target_id = self.input_msg[4:]	 
                    self.Zx = ChEck_Commande(self.target_id)
                    if True == self.Zx:	            		     
                        # إرسال السبام من جميع الحسابات
                        threading.Thread(target=send_spam_from_all_accounts, args=(self.target_id,), daemon=True).start()
                        time.sleep(2.5)    			         
                        self.CliEnts.send(xSEndMsg(f'\n[b][c][{ArA_CoLor()}] SuccEss Spam To {xMsGFixinG(self.target_id)} From All Accounts\n', 2 , self.DeCode_CliEnt_Uid , self.DeCode_CliEnt_Uid , key , iv))
                        time.sleep(1.3)
                        self.CliEnts.close()
                        if hasattr(self, 'CliEnts2'):
                            self.CliEnts2.close()
                        self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)	            		      	
                    elif False == self.Zx: 
                        self.CliEnts.send(xSEndMsg(f'\n[b][c][{ArA_CoLor()}] - PLease Use /pp/<id>\n - Ex : /pp/{self.Exemple}\n', 2 , self.DeCode_CliEnt_Uid , self.DeCode_CliEnt_Uid , key , iv))	
                        time.sleep(1.1)
                        self.CliEnts.close()
                        if hasattr(self, 'CliEnts2'):
                            self.CliEnts2.close()
                        self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)	            		

            except Exception as e:
                logger.error(f"❌ خطأ في الاتصال الرئيسي: {e}")
                try:
                    self.CliEnts.close()
                    if hasattr(self, 'CliEnts2'):
                        self.CliEnts2.close()
                except:
                    pass
                time.sleep(5)
                self.Connect_SerVer(Token , tok , host , port , key , iv , host2 , port2)
                                    
    def GeT_Key_Iv(self , serialized_data):
        """الحصول على المفتاح و IV"""
        my_message = xKEys.MyMessage()
        my_message.ParseFromString(serialized_data)
        timestamp , key , iv = my_message.field21 , my_message.field22 , my_message.field23
        timestamp_obj = Timestamp()
        timestamp_obj.FromNanoseconds(timestamp)
        timestamp_seconds = timestamp_obj.seconds
        timestamp_nanos = timestamp_obj.nanos
        combined_timestamp = timestamp_seconds * 1_000_000_000 + timestamp_nanos
        return combined_timestamp , key , iv    

    def Guest_GeneRaTe(self , uid , password):
        """إنشاء token ضيف"""
        self.url = "https://100067.connect.garena.com/oauth/guest/token/grant"
        self.headers = {
            "Host": "100067.connect.garena.com",
            "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "close",
        }
        self.dataa = {
            "uid": f"{uid}",
            "password": f"{password}",
            "response_type": "token",
            "client_type": "2",
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
            "client_id": "100067",
        }
        try:
            self.response = requests.post(self.url, headers=self.headers, data=self.dataa, timeout=30).json()
            self.Access_ToKen , self.Access_Uid = self.response['access_token'] , self.response['open_id']
            time.sleep(0.2)
            logger.info('🚀 بدء تشغيل البوت الرسمي!')
            logger.info(f'📱 Uid: {uid}')
            logger.info(f'🔑 Password: {password}')
            logger.info(f'🎫 Access Token: {self.Access_ToKen[:20]}...')
            logger.info(f'🆔 Access Id: {self.Access_Uid}')
            return self.ToKen_GeneRaTe(self.Access_ToKen , self.Access_Uid)
        except Exception as e: 
            logger.error(f"❌ خطأ في Guest_GeneRaTe: {e}")
            time.sleep(10)
            return self.Guest_GeneRaTe(uid, password)
                                        
    def GeT_LoGin_PorTs(self , JwT_ToKen , PayLoad):
        """الحصول على منافذ الاتصال"""
        self.UrL = 'https://clientbp.ggblueshark.com/GetLoginData'
        self.HeadErs = {
            'Expect': '100-continue',
            'Authorization': f'Bearer {JwT_ToKen}',
            'X-Unity-Version': '2022.3.47f1',
            'X-GA': 'v1 1',
            'ReleaseVersion': 'OB51',
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Host': 'clientbp.ggblueshark.com',
            'Connection': 'close',
            'Accept-Encoding': 'deflate, gzip',
        }        
        try:
            self.Res = requests.post(self.UrL , headers=self.HeadErs , data=PayLoad , verify=False, timeout=30)
            self.BesTo_data = json.loads(DeCode_PackEt(self.Res.content.hex()))  
            address , address2 = self.BesTo_data['32']['data'] , self.BesTo_data['14']['data'] 
            ip , ip2 = address[:len(address) - 6] , address2[:len(address) - 6]
            port , port2 = address[len(address) - 5:] , address2[len(address2) - 5:]             
            logger.info(f"🌐 منافذ الاتصال: {ip}:{port}, {ip2}:{port2}")
            return ip , port , ip2 , port2          
        except requests.RequestException as e:
            logger.error(f"❌ خطأ في الطلب: {e}")
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على المنافذ: {e}")
        return None, None, None, None
        
    def ToKen_GeneRaTe(self , Access_ToKen , Access_Uid):
        """إنشاء token رئيسي"""
        self.UrL = "https://loginbp.ggblueshark.com/MajorLogin"
        self.HeadErs = {
            'X-Unity-Version': '2022.3.47f1',
            'ReleaseVersion': 'OB51',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-GA': 'v1 1',
            'Content-Length': '928',
            'User-Agent': 'UnityPlayer/2022.3.47f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)',
            'Host': 'loginbp.ggblueshark.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'deflate, gzip',
        }   
        
        # البيانات الثابتة مع استبدال القيم الديناميكية
        self.dT = bytes.fromhex('1a13323032352d31302d33312030353a31383a3235220966726565206669726528013a07312e3131382e344232416e64726f6964204f532039202f204150492d3238202850492f72656c2e636a772e32303232303531382e313134313333294a0848616e6468656c64520c4d544e2f537061636574656c5a045749464960800a68d00572033234307a2d7838362d3634205353453320535345342e3120535345342e32204156582041565832207c2032343030207c20348001e61e8a010f416472656e6f2028544d292036343092010d4f70656e474c20455320332e329a012b476f6f676c657c36323566373136662d393161372d343935622d396631362d303866653964336336353333a2010d3137362e32382e3133352e3233aa01026172b201203433303632343537393364653836646134323561353263616164663231656564ba010134c2010848616e6468656c64ca010d4f6e65506c7573204135303130ea014034653739616666653331343134393031353434656161626562633437303537333866653638336139326464346335656533646233333636326232653936363466f00101ca020c4d544e2f537061636574656cd2020457494649ca03203161633462383065636630343738613434323033626638666163363132306635e003b5ee02e803ff8502f003af13f803840780048c95028804b5ee0290048c95029804b5ee02b00404c80401d2043d2f646174612f6170702f636f6d2e6474732e667265656669726574682d66705843537068495636644b43376a4c2d574f7952413d3d2f6c69622f61726de00401ea045f65363261623933353464386662356662303831646233333861636233333439317c2f646174612f6170702f636f6d2e6474732e667265656669726574682d66705843537068495636644b43376a4c2d574f7952413d3d2f626173652e61706bf00406f804018a050233329a050a32303139313139303236a80503b205094f70656e474c455332b805ff01c00504e005c466ea05093372645f7061727479f80583e4068806019006019a060134a2060134b2062211541141595f58011f53594c59584056114a5f535a525c6b5c04096e595c3b000e61')
        
        # استبدال القيم الديناميكية
        current_time = str(datetime.now())[:-7].encode()
        self.dT = self.dT.replace(b'2025-10-29 02:14:58', current_time)        
        self.dT = self.dT.replace(b'4e79affe31414901544eaabebc4705738fe683a92dd4c5ee3db33662b2e9664f', Access_ToKen.encode())
        self.dT = self.dT.replace(b'4306245793de86da425a52caadf21eed', Access_Uid.encode())
        
        try:
            hex_data = self.dT.hex()
            encoded_data = EnC_AEs(hex_data)
            
            # التحقق من أن الناتج هو hex صالح
            if not all(c in '0123456789abcdefABCDEF' for c in encoded_data):
                logger.warning("⚠️ ترميز غير صالح، استخدام الترميز البديل")
                encoded_data = hex_data  # استخدام البيانات الأصلية كحل بديل
            
            self.PaYload = bytes.fromhex(encoded_data)
        except Exception as e:
            logger.error(f"❌ خطأ في الترميز: {e}")
            self.PaYload = self.dT
        
        try:
            self.ResPonse = requests.post(self.UrL, headers=self.HeadErs, data=self.PaYload, verify=False, timeout=30)        
            if self.ResPonse.status_code == 200 and len(self.ResPonse.text) > 10:
                try:
                    self.BesTo_data = json.loads(DeCode_PackEt(self.ResPonse.content.hex()))
                    self.JwT_ToKen = self.BesTo_data['8']['data']           
                    self.combined_timestamp , self.key , self.iv = self.GeT_Key_Iv(self.ResPonse.content)
                    ip , port , ip2 , port2 = self.GeT_LoGin_PorTs(self.JwT_ToKen , self.PaYload)            
                    return self.JwT_ToKen , self.key , self.iv, self.combined_timestamp , ip , port , ip2 , port2
                except Exception as e:
                    logger.error(f"❌ خطأ في تحليل الاستجابة: {e}")
                    time.sleep(5)
                    return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
            else:
                logger.error(f"❌ خطأ في ToKen_GeneRaTe، الحالة: {self.ResPonse.status_code}")
                time.sleep(5)
                return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
        except Exception as e:
            logger.error(f"❌ خطأ في الطلب: {e}")
            time.sleep(5)
            return self.ToKen_GeneRaTe(Access_ToKen, Access_Uid)
      
    def Get_FiNal_ToKen_0115(self):
        """الحصول على الـ token النهائي"""
        try:
            result = self.Guest_GeneRaTe(self.id , self.password)
            if not result:
                logger.error("❌ فشل في الحصول على tokens، إعادة المحاولة...")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            token , key , iv , Timestamp , ip , port , ip2 , port2 = result
            
            if not all([ip, port, ip2, port2]):
                logger.error("❌ فشل في الحصول على المنافذ، إعادة المحاولة...")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            self.JwT_ToKen = token        
            try:
                self.AfTer_DeC_JwT = jwt.decode(token, options={"verify_signature": False})
                self.AccounT_Uid = self.AfTer_DeC_JwT.get('account_id')
                self.EncoDed_AccounT = hex(self.AccounT_Uid)[2:]
                self.HeX_VaLue = DecodE_HeX(Timestamp)
                self.TimE_HEx = self.HeX_VaLue
                self.JwT_ToKen_ = token.encode().hex()
                logger.info(f'✅ تم معالجة Uid: {self.AccounT_Uid}')
            except Exception as e:
                logger.error(f"❌ خطأ في Token: {e}")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            try:
                self.Header = hex(len(EnC_PacKeT(self.JwT_ToKen_, key, iv)) // 2)[2:]
                length = len(self.EncoDed_AccounT)
                self.__ = '00000000'
                if length == 9: self.__ = '0000000'
                elif length == 8: self.__ = '00000000'
                elif length == 10: self.__ = '000000'
                elif length == 7: self.__ = '000000000'
                else:
                    logger.warning('⚠️ طول غير متوقع')                
                self.Header = f'0115{self.__}{self.EncoDed_AccounT}{self.TimE_HEx}00000{self.Header}'
                self.FiNal_ToKen_0115 = self.Header + EnC_PacKeT(self.JwT_ToKen_ , key , iv)
            except Exception as e:
                logger.error(f"❌ خطأ في الـ Token النهائي: {e}")
                time.sleep(5)
                return self.Get_FiNal_ToKen_0115()
                
            self.AutH_ToKen = self.FiNal_ToKen_0115
            self.Connect_SerVer(self.JwT_ToKen , self.AutH_ToKen , ip , port , key , iv , ip2 , port2)        
            return self.AutH_ToKen , key , iv
            
        except Exception as e:
            logger.error(f"❌ خطأ في Get_FiNal_ToKen_0115: {e}")
            time.sleep(10)
            return self.Get_FiNal_ToKen_0115()

def start_account(account):
    """دالة لبدء تشغيل حساب واحد"""
    try:
        logger.info(f"🚀 بدء تشغيل الحساب: {account['id']}")
        FF_CLient(account['id'], account['password'])
    except Exception as e:
        logger.error(f"❌ خطأ في بدء الحساب {account['id']}: {e}")
        time.sleep(5)
        start_account(account)  # إعادة المحاولة

def StarT_SerVer():
    """الدالة الرئيسية لبدء تشغيل جميع الحسابات وAPI"""
    logger.info("🚀 بدء تشغيل الخادم...")
    
    # بدء تشغيل API في خيط منفصل
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    
    # بدء إعادة التشغيل التلقائي في خيط منفصل
    restart_thread = threading.Thread(target=AuTo_ResTartinG, daemon=True)
    restart_thread.start()
    
    # انتظار بدء API
    time.sleep(3)
    
    # بدء الحسابات
    threads = []
    
    for account in ACCOUNTS:
        thread = threading.Thread(target=start_account, args=(account,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
        time.sleep(5)  # تأخير أطول بين بدء كل حساب
    
    logger.info(f"✅ تم بدء {len(threads)} حساب")
    
    # الحفاظ على التشغيل الرئيسي
    try:
        while True:
            time.sleep(60)
            # تحديث الحالة كل دقيقة
            with connected_clients_lock:
                active_accounts = len(connected_clients)
            with active_spam_lock:
                active_spam = len(active_spam_targets)
            
            logger.info(f"📊 الحالة: {active_accounts} حساب نشط، {active_spam} سبام نشط")
    except KeyboardInterrupt:
        logger.info("⏹️ إيقاف الخادم...")
    except Exception as e:
        logger.error(f"❌ خطأ في الخادم الرئيسي: {e}")

if __name__ == "__main__":
    StarT_SerVer()