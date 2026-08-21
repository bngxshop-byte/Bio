from flask import Flask, request, jsonify
from datetime import datetime
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import urllib3
import json
import urllib.parse
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import re
import urllib.parse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ========== Protobuf Definitions ==========
_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data_pb2', _globals)

Data = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

# ========== Helper Functions ==========
def remove_color_tags(text):
    """إزالة علامات الألوان من النص"""
    if not text:
        return text
    
    # إزالة علامات الألوان السداسية [FFFFFF]
    text = re.sub(r'\[[a-fA-F0-9]{6}\]', '', text)
    
    # إزالة علامات الإغلاق [/b] [/i] إلخ
    text = re.sub(r'\[\/[a-z]\]', '', text)
    
    # إزالة علامات التنسيق [b] [i] [c] إلخ
    text = re.sub(r'\[[a-z]\]', '', text)
    
    # إزالة المسافات الكورية (ㅤ) إذا كانت تعتبر أحرفًا
    text = text.replace('ㅤ', ' ')
    
    return text.strip()

def validate_bio_length(bio):
    """التحقق من طول البايو مع تجاهل علامات الألوان"""
    clean_bio = remove_color_tags(bio)
    raw_length = len(bio)
    clean_length = len(clean_bio)
    
    return {
        'raw_length': raw_length,
        'clean_length': clean_length,
        'is_valid': clean_length <= 180,
        'color_tags_count': raw_length - clean_length
    }

def encrypt_api(plain_text):
    """تشفير البيانات باستخدام AES-CBC"""
    plain_text = bytes.fromhex(plain_text)
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

def get_garena_token(uid, password):
    """جلب التوكن من Garena"""
    try:
        url = "https://100067.connect.garena.com/oauth/guest/token/grant"
        headers = {
            "Host": "100067.connect.garena.com",
            "User-Agent": "GarenaMSDK/4.0.19P4(G011A ;Android 9;en;US;)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "close",
        }
        data = {
            "uid": uid,
            "password": password,
            "response_type": "token",
            "client_type": "2",
            "client_secret": "",
            "client_id": "100067",
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response_data = response.json()
        
        if "access_token" in response_data and "open_id" in response_data:
            return {
                'access_token': response_data['access_token'],
                'open_id': response_data['open_id']
            }
        else:
            return None
            
    except Exception as e:
        return None

def TOKEN_MAKER(OLD_ACCESS_TOKEN, NEW_ACCESS_TOKEN, OLD_OPEN_ID, NEW_OPEN_ID, uid):
    """إنشاء التوكن النهائي"""
    try:
        now = datetime.now()
        now = str(now)[:len(str(now)) - 7]
        data = bytes.fromhex('3a07312e3131382e32aa01026172b201203838656362666563643661636466633261646664633564323032323632663364ba010134ea014062613536623334653466373266323066353732386436653964386262666461393730323865613930393163616334636438313464313063656436616632383632ca032037343238623235336465666331363430313863363034613165626266656264669a060134a2060134')
        
        data = data.replace(OLD_OPEN_ID.encode(), NEW_OPEN_ID.encode())
        data = data.replace(OLD_ACCESS_TOKEN.encode(), NEW_ACCESS_TOKEN.encode())
        d = encrypt_api(data.hex())
        Final_Payload = bytes.fromhex(d)
        
        headers = {
            "Host": "loginbp.ggblueshark.com",
            "X-Unity-Version": "2018.4.11f1",
            "Accept": "*/*",
            "Authorization": "Bearer",
            "ReleaseVersion": "OB54",
            "X-GA": "v1 1",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(Final_Payload)),
            "User-Agent": "Free%20Fire/2019118692 CFNetwork/3826.500.111.2.2 Darwin/24.4.0",
            "Connection": "keep-alive"
        }
        
        URL = "https://loginbp.ggblueshark.com/MajorLogin"
        RESPONSE = requests.post(URL, headers=headers, data=Final_Payload, verify=False, timeout=10)
        
        if RESPONSE.status_code == 200:
            if len(RESPONSE.text) < 10:
                return None
                
            BASE64_TOKEN = RESPONSE.text[RESPONSE.text.find("eyJhbGciOiJIUzI1NiIsInN2ciI6IjEiLCJ0eXAiOiJKV1QifQ"):-1]
            second_dot_index = BASE64_TOKEN.find(".", BASE64_TOKEN.find(".") + 1)
            BASE64_TOKEN = BASE64_TOKEN[:second_dot_index + 44]
            return BASE64_TOKEN
        else:
            return None
            
    except Exception as e:
        return None

def get_final_token(uid, password):
    """الحصول على التوكن النهائي للحساب"""
    try:
        # الحصول على التوكن من Garena
        garena_data = get_garena_token(uid, password)
        if not garena_data:
            return None
            
        NEW_ACCESS_TOKEN = garena_data['access_token']
        NEW_OPEN_ID = garena_data['open_id']
        
        # التوكنات القديمة الثابتة
        OLD_ACCESS_TOKEN = "a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890"
        OLD_OPEN_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
        
        # إنشاء التوكن النهائي
        final_token = TOKEN_MAKER(OLD_ACCESS_TOKEN, NEW_ACCESS_TOKEN, OLD_OPEN_ID, NEW_OPEN_ID, uid)
        return final_token
        
    except Exception as e:
        return None

# ========== Main API Route ==========
@app.route('/update_bio', methods=['GET'])
def update_bio():
    """
    API لتغيير البايو لحساب واحد
    
    المعاملات المطلوبة:
    - uid: معرف الحساب
    - password: كلمة المرور
    - bio: البايو الجديد
    
    مثال:
    /update_bio?uid=4311549098&password=BNGX_IP6XZZPJIT5&bio=Hello+World
    """
    try:
        # الحصول على المعاملات من الرابط
        uid = request.args.get('uid')
        password = request.args.get('password')
        bio = request.args.get('bio')
        
        # التحقق من وجود جميع المعاملات المطلوبة
        if not uid or not password or not bio:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters. Please provide uid, password, and bio.',
                'example': '/update_bio?uid=4311549098&password=BNGX_IP6XZZPJIT5&bio=Hello+World'
            }), 400
        
        # فك تشفير البايو إذا كان مشفرًا URL
        bio = urllib.parse.unquote(bio)
        
        # التحقق من طول البايو (بدون الألوان)
        length_info = validate_bio_length(bio)
        
        if not length_info['is_valid']:
            return jsonify({
                'status': 'error',
                'message': f'Bio too long ({length_info["clean_length"]}/180 chars without colors)',
                'length_info': length_info
            }), 400
        
        # الحصول على التوكن
        token = get_final_token(uid, password)
        if not token:
            return jsonify({
                'uid': uid,
                'status': 'error',
                'message': 'Failed to get authentication token'
            }), 401
        
        # إنشاء رسالة Protobuf
        data_msg = Data()
        data_msg.field_2 = 17
        data_msg.field_5.CopyFrom(EmptyMessage())
        data_msg.field_6.CopyFrom(EmptyMessage())
        data_msg.field_8 = bio  # إرسال البايو الكامل مع الألوان
        data_msg.field_9 = 1
        data_msg.field_11.CopyFrom(EmptyMessage())
        data_msg.field_12.CopyFrom(EmptyMessage())

        # تشفير البيانات
        data_bytes = data_msg.SerializeToString()
        padded_data = pad(data_bytes, AES.block_size)
        
        key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
        iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_data = cipher.encrypt(padded_data)

        # إرسال الطلب لتغيير البايو
        url = "https://clientbp.ggpolarbear.com/UpdateSocialBasicInfo"
        headers = {
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)',
            'Connection': 'Keep-Alive',
            'Expect': '100-continue',
            'Authorization': f'Bearer {token}',
            'X-Unity-Version': '2018.4.11f1',
            'X-GA': 'v1 1',
            'ReleaseVersion': 'OB54',
            'Content-Type': 'application/octet-stream',
        }

        resp = requests.post(url, headers=headers, data=encrypted_data, timeout=10)
        
        if resp.status_code == 200:
            return jsonify({
                'status': 'success',
                'uid': uid,
                'message': 'Bio updated successfully',
                'bio': bio,
                'length_info': length_info,
                'response_status': resp.status_code
            })
        else:
            return jsonify({
                'status': 'error',
                'uid': uid,
                'message': f'HTTP {resp.status_code}: {resp.text[:100]}',
                'length_info': length_info,
                'response_status': resp.status_code
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get_token', methods=['GET'])
def get_token_api():
    """
    API لجلب التوكن فقط
    
    المعاملات المطلوبة:
    - uid: معرف الحساب
    - password: كلمة المرور
    
    مثال:
    /get_token?uid=4311549098&password=BNGX_IP6XZZPJIT5
    """
    try:
        uid = request.args.get('uid')
        password = request.args.get('password')
        
        if not uid or not password:
            return jsonify({
                'status': 'error',
                'message': 'Missing uid or password parameter',
                'example': '/get_token?uid=4311549098&password=BNGX_IP6XZZPJIT5'
            }), 400
        
        token = get_final_token(uid, password)
        
        if token:
            return jsonify({
                'status': 'success',
                'uid': uid,
                'token': token,
                'message': 'Token generated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'uid': uid,
                'message': 'Failed to generate token'
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/check_bio', methods=['GET'])
def check_bio():
    """
    API للتحقق من صحة البايو فقط (بدون تغييره)
    
    المعاملات المطلوبة:
    - bio: البايو المطلوب التحقق منه
    
    مثال:
    /check_bio?bio=[FF0000]Hello[FFFFFF]World
    """
    try:
        bio = request.args.get('bio')
        
        if not bio:
            return jsonify({
                'status': 'error',
                'message': 'Missing bio parameter',
                'example': '/check_bio?bio=[FF0000]Hello[FFFFFF]World'
            }), 400
        
        bio = urllib.parse.unquote(bio)
        length_info = validate_bio_length(bio)
        
        return jsonify({
            'status': 'success',
            'bio': bio,
            'length_info': length_info,
            'message': f'Bio is {"valid" if length_info["is_valid"] else "invalid"} ({length_info["clean_length"]}/180 chars)'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/')
def home():
    """الصفحة الرئيسية مع توثيق API"""
    return jsonify({
        'api_name': 'FreeFire Bio Changer API',
        'version': '1.0',
        'author': 'BNGX',
        'endpoints': [
            {
                'endpoint': '/update_bio',
                'method': 'GET',
                'parameters': ['uid', 'password', 'bio'],
                'description': 'تغيير البايو لحساب واحد',
                'example': '/update_bio?uid=4311549098&password=BNGX_IP6XZZPJIT5&bio=[FF0000]Hello[FFFFFF]World'
            },
            {
                'endpoint': '/get_token',
                'method': 'GET',
                'parameters': ['uid', 'password'],
                'description': 'جلب التوكن فقط',
                'example': '/get_token?uid=4311549098&password=BNGX_IP6XZZPJIT5'
            },
            {
                'endpoint': '/check_bio',
                'method': 'GET',
                'parameters': ['bio'],
                'description': 'التحقق من صحة البايو',
                'example': '/check_bio?bio=[FF0000]Hello[FFFFFF]World'
            }
        ],
        'notes': [
            'يدعم علامات الألوان مثل [FF0000] ولا تحسب في عدد الأحرف',
            'الحد الأقصى 180 حرف بدون الألوان',
            'البايو يجب أن يكون مشفر URL (URL encoded)'
        ]
    })

# ========== Main Function ==========
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 FreeFire Bio Changer API (مع دعم الألوان)")
    print("=" * 60)
    print(f"🌐 Server URL: http://localhost:65450")
    print(f"🎨 يدعم علامات الألوان ولا يحسبها في الطول")
    print("\n🔗 الطرق المتاحة:")
    print("  GET  /                      - توثيق API")
    print("  GET  /update_bio            - تغيير البايو لحساب واحد")
    print("  GET  /get_token             - جلب التوكن فقط")
    print("  GET  /check_bio             - التحقق من صحة البايو")
    print("\n📖 مثال الاستخدام:")
    print("  http://localhost:65450/update_bio?uid=4311549098&password=BNGX_IP6XZZPJIT5&bio=%5BFF0000%5DHello%5BFFFFFF%5DWorld")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=1041, debug=False)
