@echo off
pyinstaller "_main.py" --hidden-import=_cffi_backend --add-data "__icon.ico;./"  --add-data "lang/ui.ja.yml;./lang/" --add-data "lang/var.ja.yml;./lang/" --add-data "lang/ui.zh.yml;./lang/" --add-data "lang/var.zh.yml;./lang/" --add-data "lang/ui.en.yml;./lang/" --add-data "lang/var.en.yml;./lang/" --onefile --icon "__icon.ico" --name "ONScripter_Multi_Converter.exe"

