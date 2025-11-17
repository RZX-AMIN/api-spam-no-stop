import requests , time , binascii , json , urllib3 , random
from datetime import datetime
from Black import *
from multiprocessing.dummy import Pool as ThreadPool

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def Ua():
    TmP = "GarenaMSDK/4.0.13 ({}; {}; {};)"
    return TmP.format(random.choice(["iPhone 13 Pro", "iPhone 14", "iPhone XR", "Galaxy S22", "Note 20", "OnePlus 9", "Mi 11"]) , 
                     random.choice(["iOS 17", "iOS 18", "Android 13", "Android 14"]) , 
                     random.choice(["en-SG", "en-US", "fr-FR", "id-ID", "th-TH", "vi-VN"]))

def xGeT(u, p):
    """الدالة المعدلة لاستخدام UID و PW مباشرة من السكريبت الرئيسي"""
    print(f"جاري توليد التوكن لـ UID: {u}")
    try:
        r = requests.Session().post(
            "https://100067.connect.garena.com/oauth/guest/token/grant",
            headers={
                "Host": "100067.connect.garena.com",
                "User-Agent": Ua(),
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "close"
            },
            data={
                "uid": u,
                "password": p,
                "response_type": "token",
                "client_type": "2",
                "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
                "client_id": "100067"
            },
            verify=False
        )
        
        if r.status_code == 200:
            T = r.json()
            print("تم الحصول على التوكن بنجاح من Garena")
            a, o = T["access_token"], T["open_id"]
            jwt_token = xJwT(a, o)
            if jwt_token:
                print("تم توليد JWT بنجاح")
                return jwt_token
            else:
                print("فشل في توليد JWT")
                return None
        else:
            print(f"خطأ في الاستجابة من Garena: {r.status_code}")
            return None
    except Exception as e:
        print(f"حدث خطأ في xGeT: {str(e)}")
        return None

def xJwT(a, o):
    """دالة توليد JWT باستخدام التوكن المباشر"""
    try:
        dT = bytes.fromhex('1a13323032352d30372d33302031343a31313a3230220966726565206669726528013a07322e3131342e324234416e64726f6964204f53203133202f204150492d33332028545031412e3232303632342e3031342f3235303531355631393737294a0848616e6468656c6452094f72616e676520544e5a0457494649609c1368b80872033438307a1d41524d3634204650204153494d4420414553207c2032303030207c20388001973c8a010c4d616c692d473532204d433292013e4f70656e474c20455320332e322076312e72333270312d3031656163302e32613839336330346361303032366332653638303264626537643761663563359a012b476f6f676c657c61326365613833342d353732362d346235622d383666322d373130356364386666353530a2010e3139362e3138372e3132382e3334aa0102656eb201203965373166616266343364383863303662373966353438313034633766636237ba010134c2010848616e6468656c64ca0115494e46494e495820496e66696e6978205836383336ea014063363231663264363231343330646163316137383261306461623634653663383061393734613662633732386366326536623132323464313836633962376166f00101ca02094f72616e676520544ed2020457494649ca03203161633462383065636630343738613434323033626638666163363132306635e003dc810ee803daa106f003ef068004e7a5068804dc810e9004e7a5069804dc810ec80403d2045b2f646174612f6170702f7e7e73444e524632526357313830465a4d66624d5a636b773d3d2f636f6d2e6474732e66726565666972656d61782d4a534d4f476d33464e59454271535376587767495a413d3d2f6c69622f61726d3634e00402ea047b61393862306265333734326162303061313966393737633637633031633266617c2f646174612f6170702f7e7e73444e524632526357313830465a4d66624d5a636b773d3d2f636f6d2e6474732e66726565666972656d61782d4a534d4f476d33464e59454271535376587767495a413d3d2f626173652e61706bf00402f804028a050236349a050a32303139313135363537a80503b205094f70656e474c455333b805ff7fc00504d20506526164c3a873da05023133e005b9f601ea050b616e64726f69645f6d6178f2055c4b71734854346230414a3777466c617231594d4b693653517a6732726b3665764f38334f306f59306763635a626457467a785633483564454f586a47704e3967476956774b7533547a312b716a36326546673074627537664350553d8206147b226375725f72617465223a5b36302c39305d7d8806019006019a060134a2060134b20600')
        
        # تحديث البيانات الديناميكية
        dT = dT.replace(b'2025-07-30 14:11:20', str(datetime.now())[:-7].encode())
        dT = dT.replace(b'c621f2d621430dac1a782a0dab64e6c80a974a6bc728cf2e6b1224d186c9b7af', a.encode())
        dT = dT.replace(b'9e71fabf43d88c06b79f548104c7fcb7', o.encode())
        
        PyL = bytes.fromhex(EnC_AEs(dT.hex()))
        r = requests.Session().post(
            "https://loginbp.common.ggbluefox.com/MajorLogin",
            headers={
                "Expect": "100-continue",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "ReleaseVersion": "OB50",
                "Authorization": "Bearer ",
                "Host": "loginbp.common.ggbluefox.com"
            },
            data=PyL,
            verify=False
        )
        
        if r.status_code == 200:
            response_data = json.loads(DeCode_PackEt(binascii.hexlify(r.content).decode('utf-8')))
            return response_data['8']['data']
        else:
            print(f"خطأ في MajorLogin: {r.status_code}")
            return None
    except Exception as e:
        print(f"حدث خطأ في xJwT: {str(e)}")
        return None