from flask import Flask, request, jsonify
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

app = Flask(__name__)

# ... إعدادات Protocol Buffer (كما هي) ...

@app.route('/update_bio', methods=['GET'])
def update_bio():
    uid = request.args.get('uid')
    password = request.args.get('password')
    bio = request.args.get('bio')

    if not uid or not password or not bio:
        return jsonify({"error": "uid, password, and bio are required"}), 400

    if len(bio) >= 180:
        return jsonify({"error": "Bio must be less than 180 characters"}), 400

    # جلب التوكن
    token_url = f"http://78.154.103.18:11844/get?uid={uid}&pw={password}"
    try:
        token_response = requests.get(token_url)
        token_response.raise_for_status()
        token_data = token_response.json()
        token = token_data.get('token')
        if not token:
            return jsonify({"error": "Failed to get token from external API"}), 500
    except requests.RequestException as e:
        return jsonify({"error": f"Error fetching token: {str(e)}"}), 500

    # إعدادات التشفير
    key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
    iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

    # إنشاء وملء رسالة البيانات
    data = Data()
    data.field_2 = 17
    data.field_5.CopyFrom(EmptyMessage())
    data.field_6.CopyFrom(EmptyMessage())
    data.field_8 = bio
    data.field_9 = 1
    data.field_11.CopyFrom(EmptyMessage())
    data.field_12.CopyFrom(EmptyMessage())

    # تشفير البيانات
    data_bytes = data.SerializeToString()
    padded_data = pad(data_bytes, AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(padded_data)
    formatted_encrypted_data = ' '.join([f"{byte:02X}" for byte in encrypted_data])

    # إرسال البيانات المشفرة إلى API التحديث
    url = "https://clientbp.ggpolarbear.com/UpdateSocialBasicInfo"
    data_hex = formatted_encrypted_data
    data_bytes = bytes.fromhex(data_hex.replace(" ", ""))

    headers = {
        "Expect": "100-continue",
        "Authorization": f"Bearer {token}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "OB54",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-A305F Build/RP1A.200720.012)",
        "Host": "clientbp.ggblueshark.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    }

    try:
        response = requests.post(url, headers=headers, data=data_bytes)
        response.raise_for_status()
        return jsonify({
            "status_code": response.status_code,
            "encrypted_data": formatted_encrypted_data,
            "token_used": token[:10] + "..."  # إخفاء جزء من التوكن للأمان
        })
    except requests.RequestException as e:
        return jsonify({"error": f"Error updating bio: {str(e)}"}), 500

# عند النشر على Vercel
handler = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
