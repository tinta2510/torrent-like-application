from flask import Flask, request

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part in the request", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    # Save the file or perform any processing
    print(file.filename)
    file.save('D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/src/' + file.filename)
    return "File uploaded successfully", 200

if __name__ == '__main__':
    app.run(debug=True)
