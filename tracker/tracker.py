from flask import Flask, request, jsonify
from scipy.sparse.csgraph import johnson
import os
app = Flask(__name__)


# Route GET để kiểm tra tình trạng server
hashid_list={}
# store hash_id : IP, length, md5
@app.route('/status', methods=['GET'])
def status():
    return jsonify({"message": "Server is running"}), 200


# Route POST nhận JSON và trả về JSON với xử lý lỗi
@app.route('/submit', methods=['POST'])
def submit_data():
    def check_file_exist(md5, length) :
        for key, data in hashid_list:
            data['md5'] = md5
            data['length'] = length
            return key
        return None

    try:

        ip=request.remote_addr
        data= request.get_json()
        if data is None:
            return jsonify({"error": "No JSON data found"}), 400

        md5=data['md5']
        length=data['length']
        data_respond = {
            "status_file" : "Had",
            "hash_id":""
        }
        hash_id_file = check_file_exist(md5, length)
        if hash_id_file is None:
            new_hash_id=os.urandom(20).hex()
            data_respond["status"] = "New"
            data_respond["hash_id"] = new_hash_id
            hashid_list[new_hash_id]={
                "md5":md5,
                "length":length,
                "ip":[ip]
            }
        else:
            hashid_list[hash_id_file][ip].append(ip)

        return jsonify(data_respond), 200

    except Exception as e:
        # Xử lý lỗi nội bộ server
        return jsonify({"error": "Server encountered an error", "details": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
