@echo off
cd /d "D:\HCMUT_Workspace\HK241\Computer-Networks\Assignment-1\torrent-like-application\src\tracker"
uvicorn tracker:app --reload
pause