import requests

url = 'http://localhost:5000/upload'  # URL of your Flask endpoint
files = {'file': open('D:/HCMUT_Workspace/HK241/Computer-Networks/Assignment-1/torrent-like-application/src/test/torrent_reader.py', 'rb')}  # Replace 'yourfile.txt' with your file's path
response = requests.post(url, files=files)

print(response.text)  # Prints the response from the server
