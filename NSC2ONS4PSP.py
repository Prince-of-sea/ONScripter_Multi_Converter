from io import BytesIO
from PIL import Image
import PySimpleGUI as sg
import numpy as np
import subprocess
import shutil
import base64
import json
import math
import stat
import glob
import sys
import os
import re

####################################################################################################
window_title = 'ONScripter Multi Converter for PSP ver.1.2.8'
####################################################################################################

# -memo-
# __file__だとexe化時subprocessの相対パス読み込みﾀﾋぬのでsys.argv[0]使う
# 同じような理由でexit()もsys.exit()にする
# jsonでの作品個別処理何も実装してねぇ... - v1.3.0で実装
# os.path.joinを使わないパスの結合をやめないとマズイ気がする - もう無理限界


# -最新の更新履歴(v1.2.8)- 
# 将来、PillowでのImageの拡大/縮小時の命令が"Resampling."が必要になるっぽいのでつけた
# 変換後の0.txtに本ツールのURLを追記
# 一部のoggファイルで変換時エラーを起こしていたのを修正


# これを読んだあなた。
# どうかこんな可読性の欠片もないクソコードを書かないでください。
# それだけが私の望みです。

debug_mode = 0

######################################## subprocessがexe化時正常に動かんときの対策 ########################################

# 以下のサイトのものをありがたく使わせてもらってます...(メモ含めそのままコピペ)
# https://qiita.com/nonzu/pxs/b4cb0529a4fc65f45463

def subprocess_args(include_stdout=True):
	# The following is true only on Windows.
	if hasattr(subprocess, 'STARTUPINFO'):
		# Windowsでは、PyInstallerから「--noconsole」オプションを指定して実行すると、
		# サブプロセス呼び出しはデフォルトでコマンドウィンドウをポップアップします。
		# この動作を回避しましょう。
		si = subprocess.STARTUPINFO()
		si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
		# Windowsはデフォルトではパスを検索しません。環境変数を渡してください。
		env = os.environ
	else:
		si = None
		env = None

	# subprocess.check_output()では、「stdout」を指定できません。
	#
	#   Traceback (most recent call last):
	#     File "test_subprocess.py", line 58, in <module>
	#       **subprocess_args(stdout=None))
	#     File "C:Python27libsubprocess.py", line 567, in check_output
	#       raise ValueError('stdout argument not allowed, it will be overridden.')
	#   ValueError: stdout argument not allowed, it will be overridden.
	#
	# したがって、必要な場合にのみ追加してください。
	if include_stdout:
		ret = {'stdout': subprocess.PIPE}
	else:
		ret = {}

	# Windowsでは、「--noconsole」オプションを使用してPyInstallerによって
	# 生成されたバイナリからこれを実行するには、
	# OSError例外「[エラー6]ハンドルが無効です」を回避するために
	# すべて（stdin、stdout、stderr）をリダイレクトする必要があります。
	ret.update({'stdin': subprocess.PIPE,
				'stderr': subprocess.PIPE,
				'startupinfo': si,
				'env': env })
	return ret


######################################## GUI表示前の変数設定 ########################################

sg.theme('DarkBlue12')#テーマ設定

if debug_mode:
	#---デバッグモード---
	window_title += ' - !DEBUG MODE!'
	# 注意:これは作者側での開発用です 他人が使うことを想定していません
	os.environ['temp'] = 'D:'#TEMPをDドライブへ(現状C:がSATAでD:がNVMeのため)
	same_hierarchy = 'C:/_software/_zisaku/ONScripter_Multi_Converter'#本来同一階層に置く予定のexeをここから読む
	default_input = ''
	default_output = (os.environ['USERPROFILE'].replace('\\','/') + r'/Desktop')#出力先を自動でデスクトップに
	
else:
	#---通常時処理---
	same_hierarchy = (os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
	default_input = ''
	default_output = ''

try:#ffmpeg存在チェック
	subprocess.run('ffmpeg', **subprocess_args(True))
	subprocess.run('ffprobe', **subprocess_args(True))
except:
	ffmpeg_exist = False
else:
	ffmpeg_exist = True

nsaed_path = os.path.join(same_hierarchy, 'tools', 'nsaed.exe')#nsaed存在チェック
nsaed_exist = os.path.exists(nsaed_path)

smjpeg_path = os.path.join(same_hierarchy, 'tools', 'smjpeg_encode.exe')#smjpeg存在チェック
smjpeg_exist = os.path.exists(smjpeg_path)#ffmpeg非導入時は強制NG

GARbro_path = os.path.join(same_hierarchy, 'tools', 'Garbro_console', 'GARbro.Console.exe')#Garbro存在チェック
GARbro_exist = os.path.exists(GARbro_path)

if not (ffmpeg_exist and nsaed_exist and smjpeg_exist and GARbro_exist):
	errmsg = '以下のものが利用できません'
	errmsg += '' if ffmpeg_exist else '\nffmpeg.exe及びffprobe.exe'
	errmsg += '' if nsaed_exist else '\n./tools/nsaed.exe'
	errmsg += '' if smjpeg_exist else '\n./tools/smjpeg_encode.exe'
	errmsg += '' if GARbro_exist else '\n./tools/Garbro_console/GARbro.Console.exe\n\nGARbroは本ツールの動作に必須です\n終了します...'
	sg.popup(errmsg, title='!')

	if not GARbro_exist:#GARBroがない場合強制終了
		sys.exit()

#-----カーソル画像(容量削減のためpng変換済)をbase64にしたものを入れた辞書作成-----
cur_dictlist = [
	{#ONSforPSP向けカーソル(大)
		'cursor0':r'iVBORw0KGgoAAAANSUhEUgAAAC0AAAAPCAIAAAD/HNHwAAAAj0lEQVQ4y82VyQ7AIAhExw7//8eYHtSm6SK0atTzE15YNMQQCSoUU88GQFUJEnTe8ZP+E2KIRy1IArBro26yeJtk9iCpJaydY4C3XMxTm8wcydtDZhOLlMc6Om06ekulq91tKqSYM3a+WSt+GynmiHnnsY2U6QbvHgMMPu5Lv7j3famT672nfeP++V9W+G93ESCa8D+TnaQAAAAASUVORK5CYII=',
		'cursor1':r'iVBORw0KGgoAAAANSUhEUgAAAC0AAAAPCAIAAAD/HNHwAAAAzklEQVQ4y82VwQ6EMAhEB4b//2Oqh01atUrB3cMS06iY12FoqzRp+IMw+HOSv5ghxzcAJH3+3AG/k1LXneHr8a1u2sdgVpIgrlcsccXXXgpJEenjwoCK7gzfDo9+b7KD4JwlTlx3H1zeKo/4dvVHtbWxg1S1oT04XdG94tuxPgAX00Qk3gVZ3Sv+c1/iqOpe8U996cWdbpJ9SZwiAX/0RTf9JLrD33Bn/2L+6EvtgK/qXvENwNhylcjrzvCtr7hCr/3Nio5DXvxvM9zaKgZ2wdx/zNkKEJkAAAAASUVORK5CYII=',
		'doffcur':r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAWklEQVQoz6XOUQrAMAgD0KS9dkEmvXZlH4Vt6NgqDX6F8JBG60fHQkSkIJMCoElbgQdG3v7lJ3yvc/YHf8Eb9iv/hPdsxzs4bcNo8VSVZOxzNo0W24rqPp45AUToPSOLkQr8AAAAAElFTkSuQmCC',
		'doncur':r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAR0lEQVQoz63MSQoAIAzAwGj//+SKB1Fccak5h3HBBZSTRMRzkweQI1jRB3vHJ7i67+w1X2CLPeNr2Gi3fAfb7cyP8Bd7AQMRI24RSJT2NRMAAAAASUVORK5CYII=',
		'uoffcur':r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAVklEQVQoz6XSQQrAMAhE0Znm4GLIuaWLQCkd02L6cSXyViIYOr13kro/UCm5Hj4AuHtD+74u2BOeKf/DvsMpv2srrPyWvYIffM1mMN7hKzOr2wD0JdJOvKAx3W/Xg8MAAAAASUVORK5CYII=',
		'uoncur':r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAYUlEQVQoz63SwQ6AIAwD0Hbz//+4qwc9oBAVtUcCb00Gi4U+QmYKOh0HZhJDGICkRP5rN1V7/outbtKRf21rfKPl52xuu2TxpkOEoN22/dRm0TbJ6zeZOdd7AeBw/yWGWQE8NSgGtZLCjwAAAABJRU5ErkJggg==',
	},
	{#ONSforPSP向けカーソル(小)
		'cursor0':r'iVBORw0KGgoAAAANSUhEUgAAACcAAAANCAIAAACl9uAyAAAAgUlEQVQ4y8WUUQ6AIAxDi939bzziB2CMwpiguO+XtqNhIYZIUKFYOBsAVSVIsEt7GM+EGOKxJ0kA1t7qYEo+g8muJLVIWbov5ZNLwvTghm7KZzPZt81I9XW63pP5xGjmrFtfaJQRo5h+f6OMfOfn7nVO695ri/n7v85rPbtN6+/wDuhygvG0PdbKAAAAAElFTkSuQmCC',
		'cursor1':r'iVBORw0KGgoAAAANSUhEUgAAACcAAAANCAIAAACl9uAyAAAAqElEQVQ4y8WU0QrDIAxFbxL//4+v28NKqyFelMEWpNAYj+Foa906fh6Of0QDAFYz8R1YMtv1GsGxkACrjU/6E0xPWX/5U8mahcAzVq1Ipo8tR4SZRcSY22eVGkpmm2mcpAkWLhbJO8dqQcls6czcvff+ecq7stffglkbTk6E4cmzNDwyF4Z1DIaTZ2Ulf6+AWLbPyjVrZrt7392PBz5Wk3b6Hxas3QMC3gQZVYcUrNnxAAAAAElFTkSuQmCC',
		'doffcur':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAU0lEQVQoz53OUQrAIAwD0ESvLZQVr23Yh7BJGVIX+hXCoxTVr45tzKwglwKgWdtjA+PE25ATe3dZ75N8sF9eIFfswIOocO5OMpRZj6JCVVHXz2ZuT8c0N4UKKogAAAAASUVORK5CYII=',
		'doncur':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAQUlEQVQoz6XMSQoAIAzAwNj+/8kVD6Ko1D3nMCGGiLFOVYWzBEA3mGFX3pzMWPOdeh5ZsTevJ1vs2SvkgP14HgYkIlcPPtx0t78AAAAASUVORK5CYII=',
		'uoffcur':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAT0lEQVQoz5XQQQrAQAhD0aRzcFHm3NLFQCmRFv24EnkLkUyZiCApywu99G77BuDuC+vvruUd7CTk3HtjlRx6FROy6zGZX9iTmU08APL92g2gESrNuMCtcwAAAABJRU5ErkJggg==',
		'uoncur':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAUklEQVQoz6XQQQrAMAhE0a/m/jce010JWkjazlLhOWhpSYmICKF15pzFOwZICuK/t1Qq5AdPrepCvvX0vL7JU8/S0tI2R90HMOfcegMgKN/vuQCdCxsLwTbFvwAAAABJRU5ErkJggg==',
	},
	{#NScripter付属 公式カーソル
		'cursor0':r'iVBORw0KGgoAAAANSUhEUgAAAEgAAAAYCAMAAABuvUuCAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAArElEQVQ4y62VQRKDIBAEJ9a8wzsv8c08ImfuvCSHaCpxZxcIcMFqanpHy9LH80DGgkUUpBUqAq5qqCsBV+V2VRMIIOV9TKXwu1HFtIrnrlV+V4P5udIqp6udwGbIUd0xO0JdKkKeNsYLvJmnWCtQDkkjvGHRoiE7YG7tpAgwuwJNzV30t+ZXNKH5Fg1pisEMA0VrIDCjuf2a6ws5rbkaDWkgMYNAHnuz05rf0Qsvl2gb7WN46wAAAABJRU5ErkJggg==',
		'cursor1':r'iVBORw0KGgoAAAANSUhEUgAAAEgAAAAYCAMAAABuvUuCAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAA10lEQVQ4y92VuxnDIAyEz/mYw/1NwswMkVo9k6SIeUoCilShM75fpzMYrjd+M17420IBuPvnfEQZSADA1BR3XsrL0EiYib6S52AhAQByLHMyVvIcDCQAABJswnXQSI1GAUVV8hw00qIRIL7zMXnysdcemaJlRDyvlg4aeaKxwULrS0wOGinRGk0s5H2vI2Ks2krurNq4IYt514TroJF+Q3Ivn3cYx45W0WwHPxqlOp5GG5EajZaz76CQfTTa2axo4p9gnoNYJ2T7xfdydSrUca2uo3jcIfABY9pmdCPNuuMAAAAASUVORK5CYII=',
		'doffcur':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAMAAADXqc3KAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAAXklEQVQoz43SwRGAIAxE0YWhNwuhLhvYDlKEPXlAJEpI2OOfebdNF+wVnGZnXgBkVBOIIyxCgSdmQoEv/oSCSHwJBbHQpIFQDPKAWHTSwYZo5AU7AlWDtUj6PscAuAGzRhXOUU3rogAAAABJRU5ErkJggg==',
		'doncur':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAMAAADXqc3KAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAAWElEQVQoz43LsQ2AMAwAwSdiDnrvX3kIlvAkFCFgwNj58qVbduJWtvBL+wE0LASaiIiIkokvESUXbyJKJZ5ElFp40kEpbnKCWgwywITo5AIzAvNgSmAOcACduxSyPiuMsgAAAABJRU5ErkJggg==',
		'uoffcur':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAMAAADXqc3KAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAAYElEQVQoz5XLwRGAMAhE0Y1jb3RAd9tAOrCI9OQhJqISGLmEfOaVBn92sxP1mJ9tAeyBgMofQcCSXLA/k6SCIwySCd7lIomgTZ3Egs+mkgm+o0os+K0qa1Ea3V4DAXEPJ5x3ES+KPfL8AAAAAElFTkSuQmCC',
		'uoncur':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAMAAADXqc3KAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAAXElEQVQoz5XLsRGAQAhE0dWxjs2tZKs3JrcSg/MUlYORBOYzb9oQz+xuUvFjJAiY/ggCntSCbV2kFOyhk0rwLicpBH1qJBd8NlMl+I6mXPBbTWOxRACwNRG7wscB7eQO5yBktpIAAAAASUVORK5CYII=',
	},
]#すとーむ氏に怒られたら消します(爆)

#-----ディレクトリのパスを先に代入-----
result_dir = (os.environ['temp'].replace('\\','/') + r'/_NSC2ONS4PSP/result')
temp_dir = (os.environ['temp'].replace('\\','/') + r'/_NSC2ONS4PSP/tmp')

######################################## GUI表示部分 ########################################
kbps_list = ['128', '112', '96', '64', '56', '48', '32']
Hz_list = ['44100', '22050', '11025']

col = [
	[sg.Text('入力先：'), sg.InputText(k='input_dir', size=(67, 15), default_text=default_input, readonly=True, enable_events=True), sg.FolderBrowse()],
	[sg.Text('出力先：'), sg.InputText(k='output_dir', size=(67, 15), default_text=default_output, readonly=True), sg.FolderBrowse()],
]

frame_1 = sg.Frame('画像', [
	[sg.Text('変換する解像度を指定：')],
	[sg.Radio(text='320x240', group_id='A', k='res_320'),
	 sg.Radio(text='360x270', group_id='A', k='res_360', default=True),
	 sg.Radio(text='640x480', group_id='A', k='res_640')],
	[sg.Text('JPG品質：'), sg.Slider(range=(100,1), default_value=95, k='jpg_quality', pad=((0,0),(0,0)), orientation='h')],
	[sg.Checkbox('無透過BMPをJPGに変換&拡張子偽装', k='jpg_mode', default=True)],
	[sg.Checkbox('透過BMPの横解像度を偶数に指定', k='img_even', default=True)],
	[sg.Checkbox('表示が小さすぎる文字を強制拡大', k='sw_txtsize', default=True)],
], size=(300, 205))

frame_2 = sg.Frame('音源', [
	[sg.Checkbox('音源をOGGへ圧縮する', k='ogg_mode', default=ffmpeg_exist, disabled=(not ffmpeg_exist))],
	[sg.Text('BGM：'), sg.Combo(values=(kbps_list), default_value='112', readonly=True, k='BGM_kbps', disabled=(not ffmpeg_exist)), sg.Text('kbps'), 
	 sg.Combo(values=(Hz_list), default_value='44100', readonly=True, k='BGM_Hz', disabled=(not ffmpeg_exist)), sg.Text('Hz'),],
	[sg.Text('SE：'), sg.Combo(values=(kbps_list), default_value='56', readonly=True, k='SE_kbps', disabled=(not ffmpeg_exist)), sg.Text('kbps'), 
	 sg.Combo(values=(Hz_list), default_value='22050', readonly=True, k='SE_Hz', disabled=(not ffmpeg_exist)), sg.Text('Hz'),],
], size=(300, 125), pad=(0,0))

frame_3 = sg.Frame('その他', [
	[sg.Checkbox('smjpeg_encode.exeで動画を変換する', k='vid_flag', default=(smjpeg_exist and ffmpeg_exist), disabled=(not (smjpeg_exist and ffmpeg_exist)))],
	[sg.Checkbox('nsaed.exeで出力ファイルを圧縮する', k='nsa_mode', default=nsaed_exist, disabled=(not nsaed_exist))],
], size=(300, 80), pad=(0,0))

frame_4 = sg.Frame('', [
	[sg.Text(' PSPでの画面表示：'), 
	 sg.Radio(text='拡大しない', group_id='B', k='size_normal', default=True),
	 sg.Radio(text='拡大(比率維持)', group_id='B', k='size_aspect'),
	 sg.Radio(text='拡大(フルサイズ)', group_id='B', k='size_full')],
], size=(530, 40))

frame_5 = sg.Frame('', [
	[sg.Button('convert', pad=(9,6), disabled=True)]
], size=(70, 40))

progressbar = sg.Frame('', [
	[sg.ProgressBar(10000, orientation='h', size=(60, 15), key='progressbar')]
], size=(610, 25))

frame_in_2and3 = sg.Column([[frame_2],[frame_3]])

layout = [
	[col],
	[frame_1,frame_in_2and3],
	[frame_4,frame_5],
	[progressbar]
]

window = sg.Window(window_title, layout, size=(640, 360), element_justification='c', margins=(0,0))#ウインドウを表示


######################################## 関数へ逃しておく処理 ########################################

#-----プログレスバー更新-----
progbar_per = [2,5,3,85,5]#全体の処理のざっくりとした割合([txt置換, arc展開, 動画, 画像音楽, nsa化])
def func_progbar_update(mode, num, nummax):#イマイチ自分でも何書いてんのか分かんないの笑う

	barstart = ( sum(progbar_per[0:mode]) / sum(progbar_per) * 10000 )
	barmax =( (progbar_per[mode]) / sum(progbar_per) * 10000 )
	
	window['progressbar'].UpdateBar(int(barstart + (num + 1) * (barmax / nummax) ))


#-----入出力先未指定/競合時エラー-----
def func_dir_err():
	global err_flag

	if not (values['input_dir']):#output_dirと表記を合わせるためあえてtemp_dir未使用
		sg.popup('入力先が指定されていません', title='!')
		err_flag = True
	elif os.path.exists(values['input_dir']) == False:
		sg.popup('入力先が存在しません', title='!')
		err_flag = True  
	if not (values['output_dir']):
		sg.popup('出力先が指定されていません', title='!')
		err_flag = True
	elif os.path.exists(values['output_dir']) == False:
		sg.popup('出力先が存在しません', title='!')
		err_flag = True
	elif values['input_dir'] in values['output_dir']:
		sg.popup('入出力先が競合しています', title='!')
		err_flag = True


#-----シナリオ復号&コピー周り-----
def func_ext_dec():
	global err_flag
	global text_list

	search_nscript_dat = os.path.join(search_dir, 'nscript.dat')
	search_00_txt = os.path.join(search_dir, '00.txt')
	search_0_txt = os.path.join(search_dir, '0.txt')
	result_0_txt = os.path.join(result_dir, '0.txt')

	if os.path.isfile(search_0_txt) or os.path.isfile(search_00_txt):#0.txtか00.txt
		for num in range(0, 10):#0~9(00~09).txtまでを調べる
			if os.path.isfile(search_00_txt):#二桁連番で配列格納を繰り返す00.txtのばあい
				oldtext = (os.path.join(search_dir, str(num).zfill(2) + '.txt'))#zfillで先頭を0埋め
			else:#一桁連番で配列格納を繰り返す0.txtのばあい
				oldtext = (os.path.join(search_dir, str(num) + '.txt'))
					
			newtext = (os.path.join(result_dir, str(num) + '.txt'))

			if os.path.isfile(oldtext):#txtがあれば
				shutil.copy(oldtext,newtext)#コピー
				os.chmod(path=newtext, mode=stat.S_IWRITE)#念の為読み取り専用を外す
				text_list.append(newtext)#シナリオのパスを配列へ格納

	elif os.path.isfile(search_nscript_dat):#復号化処理を行うnscript.datのばあい
		oldtext = search_nscript_dat
		newtext = result_0_txt
			
		open(newtext, 'w')#復号化後の新規txt作成

		data = open(oldtext,"rb").read()#復号化前のtxt読み込み用変数
		bin_list = []#復号したバイナリを格納する配列の作成
		for b in range(len(data)):#復号 0x84でbitxorしてるんだけどいまいち自分でもよく分かってない
			bin_list.append(bytes.fromhex(str((hex(int(data[b]) ^ int(0x84))[2:].zfill(2)))))

		open(newtext, 'ab').write(b''.join(bin_list))#復号したバイナリをまとめて新規txtへ
			
		text_list.append(newtext)#シナリオのパスを配列へ格納
		
	else:#それ以外(エラー)
		sg.popup('シナリオファイルが見つかりません', title='!')
		err_flag = True


#-----0.txt読み込み時(初回限定)処理-----
def func_txt_zero(text):
	global default_tmode
	global resolution
	global game_mode
	global err_flag
	global per

	newnsc_mode = (r';\$V[0-9]{2,}G([0-9]{2,})S([0-9]{3,}),([0-9]{3,})L[0-9]{2,}')#ONS解像度新表記
	newnsc_search = re.search(newnsc_mode, text)
	oldnsc_mode = (r';mode([0-9]{3})')#ONS解像度旧表記
	oldnsc_search = re.search(oldnsc_mode, text)

	#-解像度抽出(&置換)-
	if newnsc_search:#ONS解像度新表記時
		newnsc_width = int(newnsc_search.group(2))
		newnsc_height = int(newnsc_search.group(3))

		if newnsc_width == (800 or 640 or 400 or 320) and newnsc_width == newnsc_height/3*4:#解像度&比率判定
			if newnsc_width == 640:#PSPでは新表記読めないのでついでに置換処理
				text = re.sub(newnsc_mode, r';value\1', text, 1)#640x480時
			else:
				text = re.sub(newnsc_mode, r';mode\2,value\1', text, 1)#通常時

			game_mode = newnsc_width#作品解像度を代入

		else:
			sg.popup('解像度の関係上このソフトは変換できません', title='!')
			err_flag = True

	elif oldnsc_search:#ONS解像度旧表記時
		game_mode = int(oldnsc_search.group(1))#作品解像度を代入

	else:#ONS解像度無表記時
		game_mode = 640#作品解像度を代入

	if not re.search(r'\*define', text):#*defineがない時
		sg.popup('0.txtの復号化に失敗しました', title='!')
		err_flag = True#シナリオじゃなさそうなのでエラー

	#画像が初期設定でどのような透過指定で扱われるかを代入
	default_tmode= re.findall(r'\n[\t| ]*transmode ([leftup|rightup|copy|alpha])[\t| ]*', text)

	#-解像度指定-
	if values['res_320']:#ラジオボタンから代入
		resolution = 320
	elif values['res_360']:
		resolution = 360
	elif values['res_640']:
		resolution = 640

	if not re.search(r'\n[\t| ]*nsa[\t| ]*', text):#nsa読み込み命令が無い時
		text = text.replace('*define', '*define\nnsa')#*define直下に命令追記(保険)

	per = resolution / game_mode#画像縮小率=指定解像度/作品解像度

	return text


#-----全txtへ行う処理-----
def func_txt_all(text):
	global vid_list_rel
	global immode_var_tup
	global immode_list_tup

	#-PSPで使用できない命令を無効化する-
	text = re.sub(r'([\n|\t| |:])avi "(.+?)",([0|1])', r'\1mpegplay "\2",\3', text)#aviをmpegplayで再生(後に拡張子偽装)
	text = re.sub(r'([\n|\t| |:])okcancelbox %(.+?),', r'\1mov %\2,1 ;', text)#okcancelboxをmovで強制ok
	text = re.sub(r'([\n|\t| |:])yesnobox %(.+?),', r'\1mov %\2,1 ;', text)#yesnoboxをmovで強制yes

	text = text.replace('.NBZ', '.wav')#大文字
	text = text.replace('.nbz', '.wav')#小文字

	if values['sw_txtsize']:#setwindow文字拡大処理

		#-txt内のsetwindow命令を格納-
		#[0]命令文前部分/[2]横文字数/[3]縦文字数/[4]横文字サイズ/[5]縦文字サイズ/[6]横文字間隔/[7]縦文字間隔/[8]命令文後部分
		setwindow_re_tup = re.findall(r'(setwindow3? ([0-9]{1,},){2})([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),([0-9]{1,}),(([0-9]{1,},){3}(.+?)(,[0-9]{1,}){2,4})', text)

		for v in set(setwindow_re_tup):
			txtmin = math.ceil(10 / per)
			nummin = min(int(v[4]), int(v[5]))
			if txtmin > nummin:#表示時10pxを下回りそうな場合 - ちなみに10pxはMSゴシックで漢字が潰れない最低サイズ

				#文字の縦横サイズが違う可能性を考え別に処理 - もちろん縦横比維持
				v4rp = str( int( txtmin * ( int(v[4]) / nummin ) ) )#横文字サイズ(拡大)
				v5rp = str( int( txtmin * ( int(v[5]) / nummin ) ) )#縦文字サイズ(拡大)
				v6rp = str( int( int(v[6]) * ( nummin / int(v4rp) ) ) )#横文字間隔(縮小)
				v7rp = str( int( int(v[7]) * ( nummin / int(v5rp) ) ) )#縦文字間隔(縮小)

				#横に表示できる最大文字数を(文字を大きくした分)減らす - 見切れるのを防ぐため縦はそのまま
				v2rp = str( int( int(v[2]) * ( int(v[4]) + int(v[6]) ) / ( int(v4rp) + int(v6rp) ) ) )

				sw = (v[0] + v[2] +','+ v[3] +','+ v[4] +','+ v[5] +','+ v[6] +','+ v[7] +','+ v[8])
				sw_re = (v[0] + v2rp +','+ v[3] +','+ v4rp +','+ v5rp +','+ v6rp +','+ v7rp +','+ v[8])
				
				text = text.replace(sw, sw_re)


	#-txt内の画像の相対パスを格納-

	#[0]が命令文/[3]が(パスの入っている)変数名/[5]が透過形式/[6]が分割数/[8]が相対パス - [3]か[8]はどちらかのみ代入される
	immode_list_tup += re.findall(r'(ld)[ |\t]+([lcr])[ |\t]*,[ |\t]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")[ |\t]*,[ |\t]*[0-9]+', text)#ld
	immode_list_tup += re.findall(r'((abs)?setcursor)[ |\t]+%?.+?[ |\t]*,[ |\t]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")([ |\t]*,[ |\t]*(([0-9]{1,3})|(%.+?))){1,3}', text)#setcursor系
	immode_list_tup += re.findall(r'(lsp(h)?)[ |\t]+%?.+?[ |\t]*,[ |\t]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")([ |\t]*,[ |\t]*(([0-9]{1,3})|(%.+?))){1,3}', text)#lsp系
	immode_list_tup += re.findall(r'(lsph?2(add|sub)?)[ |\t]+%?.+?[ |\t]*,[ |\t]*((\$?[A-Za-z0-9_]+?)|"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)")(([ |\t]*,[ |\t]*((-?[0-9]{1,3})|(%.+?))){1,6})?', text)#lsp2系

	#[0]が命令文/[1]が変数名/[3]が透過形式/[4]が分割数/[6]が相対パス
	immode_var_tup += re.findall(r'(stralias|mov)[ |\t]*(\$?[A-Za-z0-9_]+?)[ |\t]*,[ |\t]*"(:(.)/?([0-9]+)?(,.+?)?;)?(.+?)"', text)#パスの入ったmov及びstralias

	if values['vid_flag']:#動画変換処理を行う場合
		for a in re.findall(r'mpegplay "(.+?)",([0|1]|%[0-9]+)', text):#txt内の動画の相対パスを格納
			vid_list_rel.append(a[0])

	else:#動画変換処理を行わない場合
		text = re.sub(r'mpegplay "(.+?)",([0|1]|%[0-9]+):', r'', text)#if使用時 - 再生部分を抹消
		text = text.replace('mpegplay ', ';mpegplay ')#再生部分をコメントアウト

	return text


#-----tempフォルダを作り展開&コピー-----
def func_arc_ext():

	#---その他ファイルをコピー---
	shutil.copytree(search_dir, temp_dir, ignore=shutil.ignore_patterns('*.sar', '*.nsa', '*.ns2', '*.exe', '*.dll', '*.txt', '*.dat', '*.sav', 'envdata'))

	#---存在するarcをここで全てリスト化(もちろん上書き順は考慮)---
	temp_arc = []
	temp_arc += sorted(glob.glob(search_dir + r'/*.ns2'))
	temp_arc += reversed(sorted(glob.glob(search_dir + r'/*.nsa')))
	temp_arc += reversed(sorted(glob.glob(search_dir + r'/*.sar')))

	#---↑のリスト順にarcを処理---
	for i,path in enumerate(temp_arc):

		#---展開時競合するファイルを先に削除(GARBroに上書きオプションがないため)---
		#はじめは"input=a text=True"とかで上書き確認へ応答処理しようと思ってたけど
		#どうもinputとpyinstraller -noconsoleって両立できないんだよね...
		
		txtline = subprocess.check_output([GARbro_path, 'l',path,]#展開予定のファイル一覧を取得
					,shell=True, **subprocess_args(False))#check_output時はFalse 忘れずに

		for txt in txtline.decode('cp932', 'ignore').splitlines():#一行ずつ処理 - なぜかtxtlineがbyteなのでデコード(エラー無視)
			arc_path_rel = re.findall(r'\[.+?\] +[0-9]+? +(.+)',txt)#切り出し
			if arc_path_rel:#切り出しに成功した場合
				arc_path = os.path.join(temp_dir, str(arc_path_rel[0]).replace('.nbz', '.wav') )#絶対パスに変換(&nbzをwavに)
				if os.path.exists(arc_path):#ファイルが存在する場合
					os.remove(arc_path)#削除

		subprocess.run([GARbro_path, 'x', '-ca', '-o', temp_dir, path,]#展開
			,shell=True, **subprocess_args(True))
		
		func_progbar_update(1, i, len(temp_arc))#左から順に{種類, 現在の順番, 最大数}


#-----格納されたtxt内の動画の相対パスを処理-----
def func_vid_conv(vid, vid_result):
	vid_result = str(vid_result).replace('\\','/')#文字列として扱いづらいのでとりあえず\置換

	if not os.path.isfile(vid):#パスのファイルが実際に存在するかチェック
		return#なければ終了

	vidtmpdir = (os.path.splitext(vid_result)[0] + '_tmp')
	os.makedirs(vidtmpdir)

	vid_info_txt = subprocess.check_output([#動画情報を代入
		'ffprobe', '-hide_banner',
		'-v', 'error', '-print_format',
		'json', '-show_streams',
		'-i', vid,
	],text=True, shell=True, **subprocess_args(False))#check_output時はFalse 忘れずに
	vid_info = json.loads(vid_info_txt)

	#fpsの上2桁を抽出(fpsが小数点の際たまに暴走して299700fpsとかになるので)& "/1" 削除
	vid_frame = (vid_info['streams'][0]['r_frame_rate'].replace('/1', ''))[:2]

	#(横幅/2の切り上げ)*2でfpsを偶数へ
	vid_frame = math.ceil(int(vid_frame)/2)*2#だって奇数fpsの動画なんてまず無いし...
	vid_codec = (vid_info['streams'][0]['codec_name'])#コーデック取得

	#-展開前にPSPの再生可能形式(MPEG-1か2)へ-
	if vid_codec == 'mpeg2video' or vid_codec == 'mpeg1video':#判定
		shutil.copy(vid,vid_result)#そのまま再生できそうならコピー
		os.chmod(path=vid_result, mode=stat.S_IWRITE)#念の為読み取り専用を外す
	else:
		subprocess.run(['ffmpeg', '-y',#そのまま再生できなそうならエンコード
			'-i', vid,
			'-vcodec', 'mpeg2video',
			'-qscale', '0',
			vid_result,
		], shell=True, **subprocess_args(True))

	#-連番画像展開-
	subprocess.run(['ffmpeg', '-y',
		'-i', vid_result,
		'-s', str(vid_res),
		'-r', str(vid_frame),
		'-qscale', str(int(51-int(values['jpg_quality'])/2)),#JPEG品質指定を動画変換時にも適応
		vidtmpdir + '/%08d.jpg',#8桁連番
	], shell=True, **subprocess_args(True))

	#-音源抽出+16bitPCMへ変換-
	try:
		subprocess.run(['ffmpeg', '-y',
			'-i', vid_result,
			'-f', 's16le',#よく考えるとなんで16bitPCMなんだろう
			'-vn',
			'-ar', str(values['BGM_Hz']),
			'-ac', '2',
			vidtmpdir + '/audiodump.pcm',
		], shell=True, **subprocess_args(True))
	except:
		pass#エラー時飛ばす(無音源動画対策)

	os.remove(vid_result)#変換前動画が変換後動画と競合しないようここで削除

	#-抽出ファイルをsmjpeg_encode.exeで結合-
	subprocess.run([smjpeg_path,
	 '--video-fps', str(vid_frame),#小数点使用不可
	 '--audio-rate', str(values['BGM_Hz']),
	 '--audio-bits', '16',
	 '--audio-channels', '2',
	], shell=True, cwd=vidtmpdir, **subprocess_args(True))

	shutil.move(os.path.join(vidtmpdir, r'output.mjpg'), vid_result)#完成品を移動
	shutil.rmtree(vidtmpdir)#作業用フォルダの削除


#-----シナリオから抽出した画像の状態を整形-----
def func_tmode_img(t):
	global tmode_img_list

	if '#' in t[8]:#変数内に"#"がある(≒パスが入っていない)場合
		return#処理しない

	if not t[8]:#命令文内に変数のあった場合代入元のタプルを変数定義命令の数だけ代入
		vlist = [immode_var_tup[vn] for vn in [i for i, x in enumerate([r[1] for r in immode_var_tup]) if x == t[3]]]
	
	else:#命令文内に変数のなかった場合下記タプルに表記を合わせたダミーのリストを一つ代入
		vlist = [['', '', '', t[5], t[6], '', t[8], ]]

	for v in vlist:

		#相対パスを小文字にして絶対パスへ
		file = ( (temp_dir + '/' + v[6].replace('\\','/')).lower() )

		#-呼び出された命令の種類を代入-
		if t[0] == ('setcursor' or 'abssetcursor'):
			inst = 'cur'
		elif t[0] == 'ld':
			inst = 'ld'
		else:
			inst = 'lsp'

			#-カーソルではない場合もそれっぽい名前の場合カーソル扱い-
			for n in ['cursor', 'offcur', 'oncur']:#たまに「カーソルをsetcursorで呼ばない」作品とかあるのでそれ対策
				if n in os.path.splitext(os.path.basename(file))[0]:
					inst = 'cur'

		#-透過形式-
		if (not inst == 'cur') and (os.path.splitext(file)[1]).lower() == '.png':#カーソルではない&画像がpngなら
			tmode = 'c'#基本無条件でcopy
		elif v[3]:#指定時
			tmode = v[3]
		elif default_tmode:#透過形式なし&txtからモード抽出済
			tmode = default_tmode[0]#0文字目だけ抜いて使ってる
		else:#透過形式なし&txtからモード未抽出
			tmode = 'l'

		#-アニメーション数-
		if v[4]:#指定時
			ani_num = int(v[4])
		else:
			ani_num = 1

		#アルファブレンド画像の場合は画像分割数がアニメーション数x2になるのを
		#「bool型の(tmode == 'a')に+1した数を掛ける」としている(絶望的な可読性)
		part_num = (ani_num * ((tmode == 'a') + 1) )

		#-[カーソルかどうか, 絶対パス, 透過モード, 分割数]を代入
		tmode_img_list.append([inst, file, tmode, part_num])

		if debug_mode:
			pass
			#print([inst, file, tmode, part_num])#Debug


#-----フォーマットチェック-----
def format_check(file):
	with open(file, "rb") as f:
		b = f.read(8)

		if re.match(b'^\xff\xd8', b):
			ff = 'JPEG'

		elif re.match(b'^\x42\x4d', b):
			ff = 'BMP'

		elif re.match(b'^\x89\x50\x4e\x47\x0d\x0a\x1a\x0a', b):
			ff = 'PNG'

		elif re.match(b'^\x52\x49\x46\x46', b):
			ff = 'WAV'

		elif re.match(b'^\x4f\x67\x67\x53', b):
			ff = 'OGG'

		elif re.match(b'^\xff\xf3', b) or re.match(b'^\xff\xfa', b) or re.match(b'^\xff\xfb', b) or re.match(b'^\x49\x44\x33', b) or re.match(b'^\xff\x00\x00', b):
			ff = 'MP3'#ヘッダーについて詳細不明、情報求む

		else:
			ff = False

	return ff


#-----全画像変換処理部分-----
def func_image_conv(file, file_format):

	try:
		img = Image.open(file)#画像を開く
	except:
		return#失敗したら終了

	if img.format == False:#画像ではない場合(=画像のフォーマットが存在しない場合)
		return#終了 - 拡張子偽装対策
	
	#---arc.nsa向けフォルダ分け用処理---
	if values['nsa_mode'] == True:
		#---先にファイル保存用ディレクトリを作成---
		os.makedirs((result_dir_ff.replace(temp_dir,(result_dir + r'/arc' ))), exist_ok=True)
		#---ファイル保存先パス用変数を代入---
		result_dir2 = (result_dir + r'/arc')

	else:#通常時フォルダ分け用処理
		os.makedirs((result_dir_ff.replace(temp_dir,result_dir)), exist_ok=True)#保存先作成
		result_dir2 = result_dir#保存先パス用変数を代入

	file_result = file.replace(temp_dir,result_dir2)#出力先パス用変数の代入

	if ('transparency' in img.info):#αチャンネル付き&非RGBAな画像をRGBAへ変換
		img = img.convert('RGBA')
	
	elif (not img.mode == 'RGB') and (not img.mode == 'RGBA'):#その他RGBじゃない画像をRGB形式に(但しRGBAはそのまま)
		img = img.convert('RGB')	

	result_width = round(img.width*per)#変換後サイズを指定 - 横
	result_height = round(img.height*per)#変換後サイズを指定 - 縦

	#---縦/横幅指定が0以下の時1に---
	if result_width < 1:#流石に1切ると変換できないので
		result_width = 1
	if result_height < 1:
		result_height = 1

	#---画像処理分岐用変数---
	immode_nearest = False#NEARESTで圧縮する(≒LANCZOSで圧縮してはいけない)か
	immode_defcur = False#NScripter付属の標準画像のカーソルかどうか
	immode_cursor = False#(標準かに関わらず)カーソルかどうか
	img_mask = False#カーソル向けマスク画像代入用
	sp_val = 0#縮小時分割枚数

	a_px = (0, 0, 0)#背景画素用仮変数

	#---"tmode_img_list"内にある場合---
	if file.lower() in TIL_path:
		tmode_img = tmode_img_list[TIL_path.index(file.lower())]#リスト逆引き

		sp_val = int(tmode_img[3])

		#leftup/rightupをimmode_nearest
		if tmode_img[2] == ('l' or 'r'):
			immode_nearest = True

		#---カーソル専用処理---
		if tmode_img[0] == 'cur':
			immode_cursor = True

			#---画素比較のためnumpyへ変換---
			np_img = np.array(img.convert('RGB'))

			#---for文で標準画像とそれぞれ比較---
			for k, v in cur_dictlist[2].items():

				img_default = Image.open(BytesIO(base64.b64decode(v)))
				np_img_default = np.array(img_default.convert('RGB'))
				
				#カーソルが公式の画像と同一の時
				if np.array_equal(np_img, np_img_default):
					immode_defcur = k

			#---(leftup/rightupのみ)背景色を抽出しそこからマスク画像を作成---
			if (tmode_img[2] == ('l' or 'r')) and (not immode_defcur) and (not img.mode == 'RGBA'):

				img = img.convert('RGB')#編集のためまず強制RGB化
				img_datas = img.getdata()#画像データを取得

				if tmode_img[2] == 'l':
					a_px = img.getpixel((0, 0))#左上の1pxを背景色に指定
				elif tmode_img[2] == 'r':
					a_px = img.getpixel((img.width-1, 0))#右上の1pxを背景色に指定

				img_mask = Image.new("L", img.size, 0)

				#-ピクセル代入用配列作成-
				px_list = []
				mask_px_list = []
				for px in img_datas:
					if px == a_px:#背景色と一致したら
						px_list.append((128, 128, 128))#灰色に
						mask_px_list.append((0))#マスクは白
					else:#それ以外は
						px_list.append(px)#そのまま
						mask_px_list.append((255))#マスクは黒
					
					img.putdata(px_list)#完了
					img_mask.putdata(mask_px_list)

	#---立ち絵用横幅偶数指定(ld命令で取りこぼした立ち絵対策)---
	elif int(img.width) >= 4 and (not immode_nearest) and values['img_even']:#縦横4px以上&透明部分なし&偶数指定ON

		#---ピクセルの色数を変数に代入---
		chara_mainL = img.getpixel((1, 1))#本画像部分左上1px - 1
		chara_mainR = img.getpixel((img.width/2-1, 1))#本画像部分右上1px - 2
		chara_alphaL = img.getpixel((img.width/2, 1))#透過部分左上1px - 3
		chara_alphaR = img.getpixel((img.width-1, 1))#透過部分右上1px - 4

		if chara_mainL == chara_mainR and chara_alphaL == chara_alphaR == (255,255,255):#1,2が同一&3,4が白	
			sp_val = 2


	#-----処理分岐-----
	if immode_defcur:#デフォルトの画像そのままのカーソル
		if values['res_640']:#解像度640x480時
			#-変更の必要なし→そのまま代入-
			img_resize = img_default

		else:#解像度変更時

			#-読み込んだものと同じカーソルの縮小版を辞書から持ってくる&デコード&代入-
			#  縮小率50%を境にアイコンサイズ(大/小)を決定
			#  bool(T/F)の結果をint(1/0)として使っている
			img_resize = Image.open(BytesIO(base64.b64decode(cur_dictlist[(per < 0.5)][immode_defcur])))


	elif sp_val:#縮小時分割が必要な画像(カーソル含む)
		#---分割する横幅を指定---
		crop_width = int(img.width/sp_val)
		crop_result_width = math.ceil(result_width/sp_val)

		#---切り出し→縮小→再結合---
		img_resize = Image.new(img.mode, (crop_result_width*sp_val, result_height), a_px)#結合用画像
		for i in range(sp_val):#枚数分繰り返す
			img_crop = img.crop((crop_width*i, 0, crop_width*(i+1), img.height))#画像切り出し

			if img_mask:#(専用縮小処理が必要な)カーソルの時
				img_crop = img_crop.resize((crop_result_width-1, result_height-1), Image.Resampling.LANCZOS)

				#画像本体をLANCZOS、透過部分をNEARESTで処理することによってカーソルをキレイに縮小
				img_bg = Image.new(img.mode, (crop_result_width-1, result_height-1), a_px)#ベタ塗りの背景画像を作成
				img_mask_crop = img_mask.crop((crop_width*i, 0, crop_width*(i+1), img.height))#画像切り出し
				img_mask_crop = img_mask_crop.resize((crop_result_width-1, result_height-1), Image.Resampling.NEAREST)#マスク画像はNEARESTで縮小
				img_crop = Image.composite(img_crop, img_bg, img_mask_crop)#上記2枚を利用しimg_cropへマスク

			elif immode_nearest:#背景がボケると困る画像(NEAREST)
				img_crop = img_crop.resize((crop_result_width, result_height), Image.Resampling.NEAREST)

			else:#それ以外の画像(LANCZOS)
				img_crop = img_crop.resize((crop_result_width, result_height), Image.Resampling.LANCZOS)

			img_resize.paste(img_crop, (crop_result_width*i, bool(img_mask)))#結合用画像へ貼り付け - 専用カーソルは上1px空ける

	else:
		img_resize = img.resize((result_width, result_height), Image.Resampling.LANCZOS)

	#-----画像保存-----
	if immode_cursor or file_format == 'PNG':#カーソルか元々PNG
		img_resize.save(file_result, 'PNG')

	elif file_format == 'BMP' and ( immode_nearest or (not values['jpg_mode']) ):#bmpかつLRで呼出またはJPGmode OFF
		img_resize.save(file_result)

	else:#それ以外 - JPGmode ON時のbmp 拡張子偽装
		img_resize.save((file_result), 'JPEG', quality=int(values['jpg_quality']))




#-----全音源変換処理部分-----
def func_music_conv(file):
	#---arc.nsa向けフォルダ分け用処理---
	if values['nsa_mode']:
		#---ディレクトリ名に"bgm"とあるかで判定---
		arc_num_sound = str( bool('bgm' in str(result_dir_ff)) + 1 )

		#---ファイル保存先パス用変数を代入---
		result_dir2 = str(os.path.join(result_dir, 'arc' + arc_num_sound))
		#---先にファイル保存用ディレクトリを作成---
		os.makedirs(os.path.join(result_dir2, os.path.relpath(result_dir_ff, temp_dir)), exist_ok=True)#保存先作成
		
	else:#通常時フォルダ分け用処理
		os.makedirs(os.path.join(result_dir, os.path.relpath(result_dir_ff, temp_dir)), exist_ok=True)#保存先作成
		result_dir2 = result_dir#保存先パス用変数を代入

	#---ogg変換用処理---
	if values['ogg_mode']:
		#---ディレクトリ名に"bgm"とあるかで判定---
		if 'bgm' in str(result_dir_ff):	
			result_kbps = str(values['BGM_kbps']) + 'k'
			result_Hz = str(values['BGM_Hz'])
		else:
			result_kbps = str(values['SE_kbps']) + 'k'
			result_Hz = str(values['SE_Hz'])

	#---出力先パスの代入---
	file_result = os.path.join(result_dir2, os.path.relpath(file, temp_dir))
	file_result_ogg = (os.path.splitext(file_result)[0] + ".ogg")
	
	if values['ogg_mode']:
		subprocess.run(['ffmpeg', '-y',
			'-i', file,
			'-ab', result_kbps,
			'-ar', result_Hz,
			'-ac', '2',	file_result_ogg,
			], shell=True, **subprocess_args(True))

		if not os.path.splitext(file_result)[1] == ".ogg":#元がoggではない場合拡張子偽装を実行
			os.rename(file_result_ogg, file_result)

	else:
		shutil.copy(file,file_result)#コピーするだけ
		os.chmod(path=file_result, mode=stat.S_IWRITE)#念の為読み取り専用を外す



#-----arc.nsa圧縮-----
def func_arc_nsa(arc_num):
	arc_num_dir = (result_dir + r'/' + arc_num)
	if os.path.exists(arc_num_dir) == False:#なければ終了
		return

	try:
		subprocess.call([nsaed_path, arc_num_dir], shell=True, **subprocess_args(True))
	except:#異常終了時
		pass#何もしない
	else:#正常終了時
		shutil.move(same_hierarchy + r"/tools/arc.nsa" , arc_num_dir + '.nsa')#nsa移動
		shutil.rmtree(arc_num_dir)#nsa化前のデータを削除
			


#-----ons.ini作成-----
def func_ons_ini():

	#-解像度拡大-
	if values['size_normal']:#拡大しない
		ini_sur = 'HARDWARE'
		ini_asp = 'OFF'
	elif values['size_aspect']:#アス比維持
		ini_sur = 'SOFTWARE'
		ini_asp = 'ON'
	elif values['size_full']:#フル
		ini_sur = 'SOFTWARE'
		ini_asp = 'OFF'

	#-サンプリングレート(Hz)-
	if values['ogg_mode']:
		ini_rate = str(max(values['BGM_Hz'], values['SE_Hz']))#ogg設定値
	else:
		ini_rate = '44100'#強制44100

	#-ons.ini作成-
	ons_ini= [
		'SURFACE=' + ini_sur + '\n',
		'WIDTH=' + str(resolution) + '\n',
		'HEIGHT=' + str(int(resolution/4*3)) + '\n',
		'ASPECT=' + ini_asp + '\n',
		'SCREENBPP=32\n',
		'CPUCLOCK=333\n',
		'FONTMEMORY=ON\n',
		'ANALOGKEY=ON1\n',
		'CURSORSPEED=10\n',
		'SAMPLINGRATE=' + ini_rate +'\n',
		'CHANNELS=2\n',
		'TRIANGLE=27\n', 'CIRCLE=13\n', 'CROSS=32\n', 'SQUARE=305\n', 'LTRIGGER=111\n', 'RTRIGGER=115\n', 'DOWN=274\n', 'LEFT=273\n', 'UP=273\n', 'RIGHT=274\n', 'SELECT=48\n', 'START=97\n', 'ALUP=276\n', 'ALDOWN=275\n',	
	]
	open(os.path.join(result_dir, 'ons.ini'), 'w').writelines(ons_ini)



######################################## Event Loop ########################################
while True:
	event, values = window.read()
	if event is None or event == 'Exit':
		break


	elif event == 'input_dir':
		err_flag = False

		#'convert'操作無効化
		window['convert'].update(disabled=True)
		window.refresh()

		#-----ディレクトリのパスを先に代入-----
		search_dir = (values['input_dir'])

		#-----入出力先のパスが競合しそうなら勝手に消す-----
		if os.path.exists(result_dir):
			shutil.rmtree(result_dir)

		#-----[関数]シナリオ復号&コピー周り-----
		os.makedirs(result_dir)#出力用のディレクトリを作成
		text_list = []
		func_ext_dec()

		#'convert'操作再度有効化
		if not err_flag:
			window['convert'].update(disabled=False)
			window.refresh()


	elif event == 'convert':
		err_flag = False

		#-----とりあえず真っ先にウインドウの操作無効化-----
		window['convert'].update(disabled=True)
		window.disable()
		window.refresh()

		#-----[関数]入出力先未指定/競合時エラー-----
		func_dir_err()

		#-----特定の機能を利用しない場合プログレスバーの計算からはずす-----
		if values['vid_flag'] == False:
			progbar_per_2 = progbar_per[2]
			progbar_per[2] = 0
		if values['nsa_mode'] == False:
			progbar_per_4 = progbar_per[4]
			progbar_per[4] = 0

		#-----入出力先のパスが競合しそうなら勝手に消す-----
		if os.path.exists(temp_dir):
			shutil.rmtree(temp_dir)

		#-----シナリオ読み込み&置換処理-----
		if err_flag == False:
			vid_list_rel = []#txt内の動画の相対パスを格納するための配列
			immode_var_tup = []
			immode_list_tup = []#txt内の画像(透明指定だけど透過画像じゃないやつ)の相対パスを格納するための配列

			for i,textpath in enumerate(text_list):
				text = open(textpath, 'r', errors="ignore").read()#テキストを読み込み

				if os.path.basename(textpath) == (r'0.txt'):#[関数]0.txt読み込み時(初回限定)処理
					
					#とりあえず変数作成(実際使う値の代入はfunc_txt_zeroで行う)
					default_tmode = ""
					resolution = 0
					game_mode = 0
					per = 1

					text = func_txt_zero(text)

				if err_flag == False:#[関数]全txtへ行う処理
					text = func_txt_all(text)
					text += ('\n\n;\tConverted by "' + window_title + '"\n;\thttps://github.com/Prince-of-sea/ONScripter_Multi_Converter\n')
					open(textpath, mode='w').write(text)#全置換処理終了後書き込み

				func_progbar_update(0, i, len(text_list))#左から順に{種類, 現在の順番, 最大数}


		#-----ココから本処理(エラーメッセージなし)-----
		if err_flag == False:

			#---[関数]tempフォルダを作り展開&コピー---
			func_arc_ext()

			#-----txtから動画再生命令を検知し動画をPSP専用形式へ置換(&拡張子偽装)-----
			if values['vid_flag']:
				vid_res = (str(resolution) + r':' + str(int(resolution/4*3)))#引数用動画解像度代入

				#---[関数]格納されたtxt内の動画の相対パスを処理---
				for i,vid_rel in enumerate(set(vid_list_rel)):#set型で重複削除
					vid = os.path.join(temp_dir, vid_rel)#格納された相対パスを絶対パスへ
					vid_result = os.path.join(result_dir, vid_rel)#処理後の保存先
				
					func_vid_conv(vid, vid_result)
					func_progbar_update(2, i, len(set(vid_list_rel)))#左から順に{種類, 現在の順番, 最大数}


			#-----画像/音源処理-----

			#---画像分割用配列を作成&初期設定済みのものを代入---
			tmode_img_list = [
				['cur', (temp_dir + r'/cursor0.bmp').lower(), 'l', '3'],
				['cur', (temp_dir + r'/cursor1.bmp').lower(), 'l', '3'],
				['cur', (temp_dir + r'/doncur.bmp').lower(), 'l', '1'],
				['cur', (temp_dir + r'/doffcur.bmp').lower(), 'l', '1'],
				['cur', (temp_dir + r'/uoncur.bmp').lower(), 'l', '1'],
				['cur', (temp_dir + r'/uoffcur.bmp').lower(), 'l', '1'],
			]

			#---txtから透過処理のあるスプライト表示命令を検知し分割/透明画像のパスを配列へ格納---
			for t in set(immode_list_tup) :#set型で重複削除
				func_tmode_img(t)

			#---"tmode_img_list"内のパスのみを抽出したリストを作成---
			TIL_path = [r[1] for r in tmode_img_list]#set型にするとindex使えないので


			#---全ファイルのフルパスを配列に代入---
			files_list = []
			for rel_dir, sub_dirs, list_rel in os.walk(temp_dir): #サブフォルダ含めファイル検索
				for name in list_rel:
					files_list.append(os.path.join(rel_dir,name))#パスを代入
					#print(os.path.relpath(os.path.join(rel_dir,name), temp_dir))


			for i,file in enumerate(files_list):

				#フルパスからまたディレクトリ部分切り出し
				result_dir_ff = os.path.dirname(file)#さっきせっかく結合したのに無駄だなぁ
				
				file = str(file).replace('\\','/')#文字列として扱いづらいのでとりあえず\置換
				file_format = format_check(file)

				#-[関数]全画像変換処理部分-
				if file_format in ['JPEG', 'BMP', 'PNG']:
					func_image_conv(file, file_format)

				#-[関数]全音源変換処理部分-
				elif file_format in ['MP3', 'WAV', 'OGG']:
					func_music_conv(file)

				elif debug_mode:#Debug
					print(file)
				
				func_progbar_update(3, i, len(files_list))#左から順に{種類, 現在の順番, 最大数}


			#-----[関数]arc.nsa圧縮------
			if values['nsa_mode']:
				arc_num_list = ['arc', 'arc1', 'arc2']
				for i,arc_num in enumerate(arc_num_list):		
					func_arc_nsa(arc_num)
					func_progbar_update(4, i, len(arc_num_list))

			#-----[関数]ons.ini作成------
			func_ons_ini()

			#-----入出力先のパスが競合しそうなら勝手に消す-----
			if os.path.exists(os.path.join(values['output_dir'],r'result')):
				shutil.rmtree(os.path.join(values['output_dir'],r'result'))

			shutil.move(result_dir, values['output_dir'])#完成品を移動
		
			if debug_mode and os.path.isdir(os.path.join(same_hierarchy, 'result_add')):#Debug
				for f in glob.glob(os.path.join(same_hierarchy, 'result_add', '*')):
					#result_add内のファイルを完成品へ移動
					shutil.copy(f, (os.path.join(values['output_dir'],r'result')))#default.ttfとか入れとく

			#-----tempを削除-----
			shutil.rmtree(os.path.join(os.environ['temp'], '_NSC2ONS4PSP'))
			
			#-----終了メッセージ-----
			sg.popup('処理が終了しました', title='!')
			break


		#-----特定の機能を利用しない場合プログレスバーの計算からはずしてたのを戻す-----
		if values['vid_flag'] == False:
			progbar_per[2] = progbar_per_2
		if values['nsa_mode'] == False:
			progbar_per[4] = progbar_per_4

		#-----プログレスバーのリセット-----		
		window['progressbar'].UpdateBar(0)

		#-----ウインドウの操作再有効化-----
		window['convert'].update(disabled=False)
		window.enable()


	else:
		break

window.Close()