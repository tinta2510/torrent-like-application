import requests
import random
import hashlib
from pathlib import Path
import os


# URL của server Flask
server_url = 'http://127.0.0.1:5000'


# Hàm gửi GET yêu cầu kiểm tra server


# Hàm gửi POST yêu cầu gửi JSON đến server
class Client:
    def __init__(self):
        pass
    def download(self, hasd_id):
        pass

    def publish(self, filepath):
        def get_file_md5(file_path):
            # Tính MD5
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                # Đọc từng khối để tránh tiêu tốn bộ nhớ với tệp lớn
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)

            # Trả về MD5 dưới dạng chuỗi hex
            return md5_hash.hexdigest()
        
        length= os.path.getsize(filepath)
        md5= get_file_md5(filepath)
        data={
            "length": length,
            "md5": md5
        }

        response = requests.post(f"{server_url}/submit", json=data)
        if(response.status_code==200):
            print('Your file has been published')
            response_data= response.json()
            if response_data['status'] == "Had":
                print('Your file is new')
            else:
                print('Your file has been published')

    def exit(self):
        pass


    def start(self):
        while True:
            print('Please input the option')
            print('1.Publish')
            print('2. Download')
            print('3. Exit')

            state = input("Input: ")
            match state:
                case '2':
                    hash_id= input('Please input a hash id')
                    self.download(hash_id)
                case '1':
                    while True:
                        file_name=input("Input a file name")
                        absolute_path = Path(file_name).resolve()
                        if absolute_path.exists():
                            self.publish(absolute_path)
                            break
                        else:
                            print('File not exist')
                            option=input('Do you want to continue? Y(1)/ N(other character)')
                            if option=='Y':
                                continue
                            break
                case '3':
                    self.exit()
                    break
if __name__ == '__main__':


