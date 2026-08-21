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
from google_play_scraper import app as ah
import blackboxprotobuf

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# ========== Global Variables ==========
UA = "GarenaMSDK/4.0.32 (iPhone9,3;ios - 15.8.2;en-US;US;app v1.123.1 2019120273)"

def get_version_info():
    """الحصول على معلومات الإصدار من متجر اللعب"""
    try:
        data = ah("com.dts.freefireth", lang="fr", country="CA")
        version = data["version"]
        x = requests.get(
            f"https://version.ggwhitehawk.com/live/ver.php"
            f"?version={version}&lang=en&device=android&channel=android"
            f"&appsttore=googleplay&region=en&whitelist_version=1.3.0"
            f"&whitelist_sp_version=1.0.0&device_name=google%20G011A"
            f"&device_CPU=ARMv7%20VFPv3%20NEON%20VMH"
            f"&device_GPU=Adreno%20(TM)%20640&device_mem=1993"
        ).json()
        login_url = x.get("server_url")
        ob = x.get("latest_release_version")
        verr = x.get("remote_version")
        host = login_url.split('https://')[1].split('/')[0]
        return login_url, ob, verr, host
    except Exception as e:
        print(f"Error getting version info: {e}")
        return "https://loginbp.ggblueshark.com", "OB54", "1.118.2", "loginbp.ggblueshark.com"

LOGIN_URL, OB_VERSION, REMOTE_VERSION, HOST = get_version_info()

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

def EncodeVarint(value):
    """تشفير قيمة إلى Varint للـ Protobuf"""
    result = []
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        result.append(byte)
        if not value:
            break
    return bytes(result)

def BuildProto(fields):
    """بناء رسالة Protobuf من قاموس"""
    packet = bytearray()
    for field, value in fields.items():
        if isinstance(value, dict):
            nested = BuildProto(value)
            packet.extend(EncodeVarint((field << 3) | 2))
            packet.extend(EncodeVarint(len(nested)))
            packet.extend(nested)
        elif isinstance(value, int):
            packet.extend(EncodeVarint(field << 3))
            packet.extend(EncodeVarint(value))
        elif isinstance(value, str):
            data = value.encode()
            packet.extend(EncodeVarint((field << 3) | 2))
            packet.extend(EncodeVarint(len(data)))
            packet.extend(data)
        elif isinstance(value, bytes):
            packet.extend(EncodeVarint((field << 3) | 2))
            packet.extend(EncodeVarint(len(value)))
            packet.extend(value)
    return bytes(packet)

def ParseProto(data):
    """تحليل رسالة Protobuf"""
    return blackboxprotobuf.decode_message(data)[0]

def remove_color_tags(text):
    """إزالة علامات الألوان من النص"""
    if not text:
        return text
    
    text = re.sub(r'\[[a-fA-F0-9]{6}\]', '', text)
    text = re.sub(r'\[\/[a-z]\]', '', text)
    text = re.sub(r'\[[a-z]\]', '', text)
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

def encrypt_update(data_bytes):
    """تشفير بيانات التحديث باستخدام AES-CBC"""
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(pad(data_bytes, AES.block_size))
    return encrypted_data

# ========== Token Functions (NEW METHOD) ==========

def GetToken(uid, pwd):
    """جلب التوكن من Garena باستخدام الطريقة الجديدة"""
    url = "https://100067.connect.garena.com/api/v2/oauth/guest/token:grant"
    payload = {
        "source": 1,
        "password": pwd,
        "uid": int(uid),
        "response_type": "token",
        "client_type": 1,
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067"
    }
    headers = {
        "User-Agent": UA,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Language": "en-US,en;q=0.9"
    }
    r = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
    return r.json()

def EncodePyl(data):
    """تشفير البيانات باستخدام AES-CBC"""
    KEY = b'Yg&tc%DEuh6%Zc^8'
    IV = b'6oyZDr22E3ychjM%'
    return AES.new(KEY, AES.MODE_CBC, IV).encrypt(pad(data, AES.block_size))

def BuildLogin(open_id, access_token):
    """بناء رسالة Protobuf للتسجيل"""
    payload = {
        3: str(datetime.now())[:-7],
        4: "free fire",
        5: 2,
        7: REMOTE_VERSION,
        8: "Android OS 9 / API-28 (PQ3B.190801.10101846/G9650ZHU2ARC6)",
        9: "Handheld",
        10: "Verizon",
        11: "WIFI",
        12: 1920,
        13: 1080,
        14: "280",
        15: "ARM64 FP ASIMD AES VMH | 2865 | 4",
        16: 3003,
        17: "Adreno (TM) 640",
        18: "OpenGL ES 3.1 v1.46",
        19: "Google|34a7dcdf-a7d5-4cb6-8d7e-3b0e448a0c57",
        20: "223.191.51.89",
        21: "ar",
        22: open_id,
        23: "3",
        24: "Handheld",
        25: "iPhone10,1",
        29: access_token,
        30: 1,
        41: "Verizon",
        42: "WIFI",
        57: "7428b253defc164018c604a1ebbfebdf",
        60: 36235,
        61: 31335,
        62: 2519,
        63: 703,
        64: 25010,
        65: 26628,
        66: 32992,
        67: 36235,
        70: 1,
        73: 1,
        74: "/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/lib/arm64",
        76: 1,
        77: "5b892aaabd688e571f688053118a162b|/data/app/com.dts.freefireth-YPKM8jHEwAJlhpmhDhv5MQ==/base.apk",
        78: 2,
        79: 2,
        81: "64",
        83: "2019118695",
        85: 3,
        86: "OpenGLES2",
        87: 16383,
        88: 4,
        90: "Tunis",
        91: "11",
        92: 13564,
        93: "android",
        94: "KqsHTymw5/5GB23YGniUYN2/q47GATrq7eFeRatf0NkwLKEMQ0PK5BKEk72dPflAxUlEBir6Vtey83XqF593qsl8hwY=",
        95: 110009,
        97: 1,
        98: 1,
        99: "4",
        100: "4",
        102: b'\x10\x01D@W\r\x04\x01\x18S[AYYD\t\x16lYY\\x06\x04(RPw[V\x08;\x0eS8'
    }
    return BuildProto(payload)

def MajorLogin(proto_data):
    """إرسال طلب التسجيل الرئيسي والحصول على التوكن الكامل"""
    headers = {
        "Authorization": "Bearer",
        "Connection": "Keep-Alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": HOST,
        "ReleaseVersion": OB_VERSION,
        "User-Agent": UA,
        "X-GA": "v1 1",
        "X-Unity-Version": "2018.4.11f1"
    }
    encrypted_data = EncodePyl(proto_data)
    response = requests.post(
        f"https://{HOST}/MajorLogin",
        headers=headers,
        data=encrypted_data,
        verify=False,
        timeout=10
    )
    return response

def get_final_token(uid, password):
    """الحصول على التوكن النهائي الكامل باستخدام الطريقة الجديدة"""
    try:
        # الخطوة 1: جلب التوكن من Garena
        token_data = GetToken(uid, password)
        
        if "data" not in token_data:
            print("Failed to get token from Garena")
            return None
            
        access_token = token_data["data"]["access_token"]
        open_id = token_data["data"]["open_id"]
        
        # الخطوة 2: بناء رسالة Protobuf للتسجيل
        proto_data = BuildLogin(open_id, access_token)
        
        # الخطوة 3: إرسال طلب التسجيل الرئيسي
        response = MajorLogin(proto_data)
        
        # الخطوة 4: تحليل الاستجابة باستخدام Protobuf
        parsed_data = ParseProto(response.content)
        
        # استخراج التوكن من الحقل 8
        result = parsed_data.get("8")
        
        if result is None:
            print("Token not found in response")
            return None
            
        # تحويل إلى نص إذا كان bytes
        if isinstance(result, bytes):
            result = result.decode("utf-8", errors="replace")
            
        return result
        
    except Exception as e:
        print(f"Error getting final token: {e}")
        return None

# ========== Main API Routes ==========

@app.route('/update_bio', methods=['GET'])
def update_bio():
    """API لتغيير البايو لحساب واحد"""
    try:
        uid = request.args.get('uid')
        password = request.args.get('password')
        bio = request.args.get('bio')
        
        if not uid or not password or not bio:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters. Please provide uid, password, and bio.',
                'example': '/update_bio?uid=4311549098&password=BNGX_IP6XZZPJIT5&bio=Hello+World'
            }), 400
        
        bio = urllib.parse.unquote(bio)
        
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
        
        # بناء رسالة Protobuf للتحديث
        data_msg = Data()
        data_msg.field_2 = 17
        data_msg.field_5.CopyFrom(EmptyMessage())
        data_msg.field_6.CopyFrom(EmptyMessage())
        data_msg.field_8 = bio
        data_msg.field_9 = 1
        data_msg.field_11.CopyFrom(EmptyMessage())
        data_msg.field_12.CopyFrom(EmptyMessage())

        # تشفير البيانات
        data_bytes = data_msg.SerializeToString()
        encrypted_data = encrypt_update(data_bytes)

        # إرسال طلب التحديث
        url = "https://clientbp.ggblueshark.com/UpdateSocialBasicInfo"
        headers = {
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)',
            'Connection': 'Keep-Alive',
            'Expect': '100-continue',
            'Authorization': f'Bearer {token}',
            'X-Unity-Version': '2018.4.11f1',
            'X-GA': 'v1 1',
            'ReleaseVersion': OB_VERSION,
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
    """API لجلب التوكن الكامل باستخدام الطريقة الجديدة"""
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
                'token_length': len(token),
                'message': 'Token generated successfully using new method'
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
    """API للتحقق من صحة البايو فقط"""
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
        'version': '3.0',
        'author': 'BNGX',
        'token_method': 'NEW (Full Token via Protobuf Parse)',
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
                'description': 'جلب التوكن الكامل (طريقة جديدة)',
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
            'البايو يجب أن يكون مشفر URL (URL encoded)',
            'طريقة جلب التوكن جديدة تستخدم ParseProto لاستخراج التوكن الكامل'
        ]
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 FreeFire Bio Changer API V3 (طريقة جلب توكن كاملة)")
    print("=" * 60)
    print(f"🌐 Server URL: http://localhost:65450")
    print(f"📱 Version: {OB_VERSION}")
    print(f"🔄 Token Method: NEW (Full Token via Protobuf Parse)")
    print(f"🎨 يدعم علامات الألوان ولا يحسبها في الطول")
    print("\n🔗 الطرق المتاحة:")
    print("  GET  /                      - توثيق API")
    print("  GET  /update_bio            - تغيير البايو لحساب واحد")
    print("  GET  /get_token             - جلب التوكن الكامل (طريقة جديدة)")
    print("  GET  /check_bio             - التحقق من صحة البايو")
    print("\n📖 مثال الاستخدام:")
    print("  http://localhost:65450/update_bio?uid=4311549098&password=BNGX_IP6XZZPJIT5&bio=%5BFF0000%5DHello%5BFFFFFF%5DWorld")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=65450, debug=False)
