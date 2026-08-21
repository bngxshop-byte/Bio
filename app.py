from flask import Flask, request, jsonify
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib3
import urllib.parse
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
import re

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

def get_token_from_api(uid, password):
    """جلب التوكن من API الخارجي فقط"""
    try:
        url = f"http://78.154.103.18:11844/get?uid={uid}&pw={password}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # محاولة استخراج التوكن من الرد
            if 'token' in data:
                return data['token']
            elif 'access_token' in data:
                return data['access_token']
            elif 'data' in data:
                return data['data']
            else:
                # إذا كان الرد نصاً عادياً
                return response.text.strip()
        else:
            return None
            
    except Exception as e:
        print(f"Error getting token from API: {e}")
        return None

# ========== Main API Route ==========
@app.route('/update_bio', methods=['GET'])
def update_bio():
    """
    API لتغيير البايو
    
    المعاملات المطلوبة:
    - uid: معرف الحساب
    - password: كلمة المرور
    - bio: البايو الجديد
    """
    try:
        uid = request.args.get('uid')
        password = request.args.get('password')
        bio = request.args.get('bio')
        
        if not uid or not password or not bio:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: uid, password, bio',
                'example': '/update_bio?uid=4311549098&password=BNGX_IP6XZZPJIT5&bio=Hello+World'
            }), 400
        
        bio = urllib.parse.unquote(bio)
        
        # التحقق من طول البايو
        length_info = validate_bio_length(bio)
        if not length_info['is_valid']:
            return jsonify({
                'status': 'error',
                'message': f'Bio too long ({length_info["clean_length"]}/180 chars)',
                'length_info': length_info
            }), 400
        
        # جلب التوكن من API الخارجي
        token = get_token_from_api(uid, password)
        if not token:
            return jsonify({
                'uid': uid,
                'status': 'error',
                'message': 'Failed to get token from external API'
            }), 401
        
        # إنشاء رسالة Protobuf
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
                'length_info': length_info
            })
        else:
            return jsonify({
                'status': 'error',
                'uid': uid,
                'message': f'HTTP {resp.status_code}: {resp.text[:100]}',
                'length_info': length_info
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/get_token', methods=['GET'])
def get_token_api():
    """
    جلب التوكن من API الخارجي فقط
    
    المعاملات:
    - uid: معرف الحساب
    - password: كلمة المرور
    """
    try:
        uid = request.args.get('uid')
        password = request.args.get('password')
        
        if not uid or not password:
            return jsonify({
                'status': 'error',
                'message': 'Missing uid or password',
                'example': '/get_token?uid=4311549098&password=BNGX_IP6XZZPJIT5'
            }), 400
        
        token = get_token_from_api(uid, password)
        
        if token:
            return jsonify({
                'status': 'success',
                'uid': uid,
                'token': token
            })
        else:
            return jsonify({
                'status': 'error',
                'uid': uid,
                'message': 'Failed to get token from external API'
            }), 400
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/check_bio', methods=['GET'])
def check_bio():
    """
    التحقق من صحة البايو فقط
    
    المعاملات:
    - bio: البايو للتحقق
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
            'valid': length_info['is_valid']
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/')
def home():
    """الصفحة الرئيسية"""
    return jsonify({
        'api_name': 'FreeFire Bio Changer',
        'version': '2.0',
        'description': 'يستخدم API خارجي لجلب التوكنات',
        'token_api': 'http://78.154.103.18:11844/get',
        'endpoints': {
            '/update_bio': {
                'method': 'GET',
                'params': ['uid', 'password', 'bio'],
                'example': '/update_bio?uid=4311549098&password=BNGX_IP6XZZPJIT5&bio=Hello'
            },
            '/get_token': {
                'method': 'GET',
                'params': ['uid', 'password'],
                'example': '/get_token?uid=4311549098&password=BNGX_IP6XZZPJIT5'
            },
            '/check_bio': {
                'method': 'GET',
                'params': ['bio'],
                'example': '/check_bio?bio=[FF0000]Hello'
            }
        },
        'notes': [
            'يدعم ألوان [FF0000] ولا تحسب في الطول',
            'الحد الأقصى 180 حرف',
            'التوكنات تجلب من API خارجي'
        ]
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 FreeFire Bio Changer API (باستخدام API خارجي)")
    print("=" * 60)
    print("🔗 External Token API: http://78.154.103.18:11844/get")
    print("📌 الطرق المتاحة:")
    print("  GET  /")
    print("  GET  /update_bio?uid=&password=&bio=")
    print("  GET  /get_token?uid=&password=")
    print("  GET  /check_bio?bio=")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=1041, debug=False)
