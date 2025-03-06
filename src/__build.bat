@echo off
pyinstaller "_main.py" --hidden-import=_cffi_backend --add-data "__icon.ico;./" --onefile --icon "__icon.ico" --name "ONScripter_Multi_Converter.exe"
