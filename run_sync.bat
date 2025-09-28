@echo off
cd /d D:\python\mvc-shopping
call venv\Scripts\activate.bat
flask sync-pending-orders
