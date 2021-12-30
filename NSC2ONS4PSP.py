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
import sys
import os
import re

####################################################################################################
window_title = 'ONScripter Multi Converter for PSP ver.1.01'
####################################################################################################

# -memo-
# __file__だとexe化時subprocessの相対パス読み込みﾀﾋぬのでsys.argv[0]使う
# BGMとSEの区別もうちょいマシな方法ないか模索中
# jsonでの作品個別処理何も実装してねぇ...
# もうopencv使うのは諦めよう


# -最新の更新履歴(v1.0.1)- 
# txt読み込み時の文字コード指定を削除
# cursor.xxxが.bmp以外の場合に対応
# フォントのON/OFFを削除
# 動画変換を"その他"欄へ移動
# "カーソルを標準の画像へ強制上書き"実装
# デフォルトでチェック入っている項目をいくつか変更
# 初回のエラー表示にテーマが反映されてなかったのを修正

# これを読んだあなた。
# どうかこんな可読性の欠片もないクソコードを書かないでください。
# それだけが私の望みです。

######################################## subprocessがexe化時正常に動かんときの対策 ########################################

# 以下のサイトのものをありがたく使わせてもらってます...(メモ含めそのままコピペ)
# https://qiita.com/nonzu/items/b4cb0529a4fc65f45463

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

#-----ffmpeg存在チェック-----
try:
	subprocess.run('ffmpeg', **subprocess_args(True))
	subprocess.run('ffprobe', **subprocess_args(True))
except:
	ffmpeg_exist = False
	sg.popup('ffmpegが利用できません', title='!')
else:
	ffmpeg_exist = True

#-----nsaed存在チェック-----
nsaed_path = ((os.path.dirname(sys.argv[0])) + r'/tools/nsaed.exe')
if os.path.exists(nsaed_path):
	nsaed_exist = True
else:
	nsaed_exist = False
	sg.popup('./tools/nsaed.exeが利用できません', title='!')

#-----smjpeg存在チェック(ffmpeg非導入時は強制NG)-----
smjpeg_path = ((os.path.dirname(sys.argv[0])) + r'/tools/smjpeg_encode.exe')
if ffmpeg_exist == True and os.path.exists(smjpeg_path):
	smjpeg_exist = True
else:
	smjpeg_exist = False
	sg.popup('./tools/smjpeg_encode.exeが利用できません', title='!')


#-----カーソル画像(容量削減のためpng変換済)をbase64にしたものを入れた辞書作成-----
cur_dictlist = [
	{#ONSforPSP向けカーソル(大)
		'cursor0.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAC0AAAAPCAIAAAD/HNHwAAAAj0lEQVQ4y82VyQ7AIAhExw7//8eYHtSm6SK0atTzE15YNMQQCSoUU88GQFUJEnTe8ZP+E2KIRy1IArBro26yeJtk9iCpJaydY4C3XMxTm8wcydtDZhOLlMc6Om06ekulq91tKqSYM3a+WSt+GynmiHnnsY2U6QbvHgMMPu5Lv7j3famT672nfeP++V9W+G93ESCa8D+TnaQAAAAASUVORK5CYII=',
		'cursor1.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAC0AAAAPCAIAAAD/HNHwAAAAzklEQVQ4y82VwQ6EMAhEB4b//2Oqh01atUrB3cMS06iY12FoqzRp+IMw+HOSv5ghxzcAJH3+3AG/k1LXneHr8a1u2sdgVpIgrlcsccXXXgpJEenjwoCK7gzfDo9+b7KD4JwlTlx3H1zeKo/4dvVHtbWxg1S1oT04XdG94tuxPgAX00Qk3gVZ3Sv+c1/iqOpe8U996cWdbpJ9SZwiAX/0RTf9JLrD33Bn/2L+6EvtgK/qXvENwNhylcjrzvCtr7hCr/3Nio5DXvxvM9zaKgZ2wdx/zNkKEJkAAAAASUVORK5CYII=',
		'doffcur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAWklEQVQoz6XOUQrAMAgD0KS9dkEmvXZlH4Vt6NgqDX6F8JBG60fHQkSkIJMCoElbgQdG3v7lJ3yvc/YHf8Eb9iv/hPdsxzs4bcNo8VSVZOxzNo0W24rqPp45AUToPSOLkQr8AAAAAElFTkSuQmCC',
		'doncur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAR0lEQVQoz63MSQoAIAzAwGj//+SKB1Fccak5h3HBBZSTRMRzkweQI1jRB3vHJ7i67+w1X2CLPeNr2Gi3fAfb7cyP8Bd7AQMRI24RSJT2NRMAAAAASUVORK5CYII=',
		'uoffcur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAVklEQVQoz6XSQQrAMAhE0Znm4GLIuaWLQCkd02L6cSXyViIYOr13kro/UCm5Hj4AuHtD+74u2BOeKf/DvsMpv2srrPyWvYIffM1mMN7hKzOr2wD0JdJOvKAx3W/Xg8MAAAAASUVORK5CYII=',
		'uoncur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAA8AAAAPCAIAAAC0tAIdAAAAYUlEQVQoz63SwQ6AIAwD0Hbz//+4qwc9oBAVtUcCb00Gi4U+QmYKOh0HZhJDGICkRP5rN1V7/outbtKRf21rfKPl52xuu2TxpkOEoN22/dRm0TbJ6zeZOdd7AeBw/yWGWQE8NSgGtZLCjwAAAABJRU5ErkJggg==',
	},
	{#ONSforPSP向けカーソル(小)
		'cursor0.bmp':r'iVBORw0KGgoAAAANSUhEUgAAACcAAAANCAIAAACl9uAyAAAAgUlEQVQ4y8WUUQ6AIAxDi939bzziB2CMwpiguO+XtqNhIYZIUKFYOBsAVSVIsEt7GM+EGOKxJ0kA1t7qYEo+g8muJLVIWbov5ZNLwvTghm7KZzPZt81I9XW63pP5xGjmrFtfaJQRo5h+f6OMfOfn7nVO695ri/n7v85rPbtN6+/wDuhygvG0PdbKAAAAAElFTkSuQmCC',
		'cursor1.bmp':r'iVBORw0KGgoAAAANSUhEUgAAACcAAAANCAIAAACl9uAyAAAAqElEQVQ4y8WU0QrDIAxFbxL//4+v28NKqyFelMEWpNAYj+Foa906fh6Of0QDAFYz8R1YMtv1GsGxkACrjU/6E0xPWX/5U8mahcAzVq1Ipo8tR4SZRcSY22eVGkpmm2mcpAkWLhbJO8dqQcls6czcvff+ecq7stffglkbTk6E4cmzNDwyF4Z1DIaTZ2Ulf6+AWLbPyjVrZrt7392PBz5Wk3b6Hxas3QMC3gQZVYcUrNnxAAAAAElFTkSuQmCC',
		'doffcur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAU0lEQVQoz53OUQrAIAwD0ESvLZQVr23Yh7BJGVIX+hXCoxTVr45tzKwglwKgWdtjA+PE25ATe3dZ75N8sF9eIFfswIOocO5OMpRZj6JCVVHXz2ZuT8c0N4UKKogAAAAASUVORK5CYII=',
		'doncur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAQUlEQVQoz6XMSQoAIAzAwNj+/8kVD6Ko1D3nMCGGiLFOVYWzBEA3mGFX3pzMWPOdeh5ZsTevJ1vs2SvkgP14HgYkIlcPPtx0t78AAAAASUVORK5CYII=',
		'uoffcur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAT0lEQVQoz5XQQQrAQAhD0aRzcFHm3NLFQCmRFv24EnkLkUyZiCApywu99G77BuDuC+vvruUd7CTk3HtjlRx6FROy6zGZX9iTmU08APL92g2gESrNuMCtcwAAAABJRU5ErkJggg==',
		'uoncur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAIAAAD9iXMrAAAAUklEQVQoz6XQQQrAMAhE0a/m/jce010JWkjazlLhOWhpSYmICKF15pzFOwZICuK/t1Qq5AdPrepCvvX0vL7JU8/S0tI2R90HMOfcegMgKN/vuQCdCxsLwTbFvwAAAABJRU5ErkJggg==',
	},
	{#NScripter付属 公式カーソル
		'cursor0.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAEgAAAAYCAMAAABuvUuCAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAArElEQVQ4y62VQRKDIBAEJ9a8wzsv8c08ImfuvCSHaCpxZxcIcMFqanpHy9LH80DGgkUUpBUqAq5qqCsBV+V2VRMIIOV9TKXwu1HFtIrnrlV+V4P5udIqp6udwGbIUd0xO0JdKkKeNsYLvJmnWCtQDkkjvGHRoiE7YG7tpAgwuwJNzV30t+ZXNKH5Fg1pisEMA0VrIDCjuf2a6ws5rbkaDWkgMYNAHnuz05rf0Qsvl2gb7WN46wAAAABJRU5ErkJggg==',
		'cursor1.bmp':r'iVBORw0KGgoAAAANSUhEUgAAAEgAAAAYCAMAAABuvUuCAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAA10lEQVQ4y92VuxnDIAyEz/mYw/1NwswMkVo9k6SIeUoCilShM75fpzMYrjd+M17420IBuPvnfEQZSADA1BR3XsrL0EiYib6S52AhAQByLHMyVvIcDCQAABJswnXQSI1GAUVV8hw00qIRIL7zMXnysdcemaJlRDyvlg4aeaKxwULrS0wOGinRGk0s5H2vI2Ks2krurNq4IYt514TroJF+Q3Ivn3cYx45W0WwHPxqlOp5GG5EajZaz76CQfTTa2axo4p9gnoNYJ2T7xfdydSrUca2uo3jcIfABY9pmdCPNuuMAAAAASUVORK5CYII=',
		'doffcur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAMAAADXqc3KAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAAXklEQVQoz43SwRGAIAxE0YWhNwuhLhvYDlKEPXlAJEpI2OOfebdNF+wVnGZnXgBkVBOIIyxCgSdmQoEv/oSCSHwJBbHQpIFQDPKAWHTSwYZo5AU7AlWDtUj6PscAuAGzRhXOUU3rogAAAABJRU5ErkJggg==',
		'doncur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAMAAADXqc3KAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAAWElEQVQoz43LsQ2AMAwAwSdiDnrvX3kIlvAkFCFgwNj58qVbduJWtvBL+wE0LASaiIiIkokvESUXbyJKJZ5ElFp40kEpbnKCWgwywITo5AIzAvNgSmAOcACduxSyPiuMsgAAAABJRU5ErkJggg==',
		'uoffcur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAMAAADXqc3KAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAAYElEQVQoz5XLwRGAMAhE0Y1jb3RAd9tAOrCI9OQhJqISGLmEfOaVBn92sxP1mJ9tAeyBgMofQcCSXLA/k6SCIwySCd7lIomgTZ3Egs+mkgm+o0os+K0qa1Ea3V4DAXEPJ5x3ES+KPfL8AAAAAElFTkSuQmCC',
		'uoncur.bmp':r'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAMAAADXqc3KAAADAFBMVEUKMjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAALCwsMDAwNDQ0ODg4PDw8QEBARERESEhITExMBAQFGAQGCAQG0AQHcAQH+AQEBRgFGRgGCRgG0RgHcRgH+RgEBggFGggGCggG0ggHcggH+ggEBtAFGtAGCtAG0tAHctAH+tAEB3AFG3AGC3AG03AHc3AH+3AEB/gFG/gGC/gG0/gHc/gH+/gEBAUZGAUaCAUa0AUbcAUb+AUYBRkZGRkaCRka0RkbcRkb+RkYBgkZGgkaCgka0gkbcgkb+gkYBtEZGtEaCtEa0tEbctEb+tEYB3EZG3EaC3Ea03Ebc3Eb+3EYB/kZG/kaC/ka0/kbc/kb+/kYBAYJGAYKCAYK0AYLcAYL+AYIBRoJGRoKCRoK0RoLcRoL+RoIBgoJGgoKCgoK0goLcgoL+goIBtIJGtIKCtIK0tILctIL+tIIB3IJG3IKC3IK03ILc3IL+3IIB/oJG/oKC/oK0/oLc/oL+/oIBAbRGAbSCAbS0AbTcAbT+AbQBRrRGRrSCRrS0RrTcRrT+RrQBgrRGgrSCgrS0grTcgrT+grQBtLRGtLSCtLS0tLTctLT+tLQB3LRG3LSC3LS03LTc3LT+3LQB/rRG/rSC/rS0/rTc/rT+/rQBAdxGAdyCAdy0AdzcAdz+AdwBRtxGRtyCRty0RtzcRtz+RtwBgtxGgtyCgty0gtzcgtz+gtwBtNxGtNyCtNy0tNzctNz+tNwB3NxG3NyC3Ny03Nzc3Nz+3NwB/txG/tyC/ty0/tzc/tz+/twBAf5GAf6CAf60Af7cAf7+Af4BRv5GRv6CRv60Rv7cRv7+Rv4Bgv5Ggv6Cgv60gv7cgv7+gv4BtP5GtP6CtP60tP7ctP7+tP4B3P5G3P6C3P603P7c3P7+3P4B/v5G/v6C/v60/v7c/v7+/v7s7Ozt7e3u7u7v7+/w8PDx8fHy8vLz8/P09PT///8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD1zcP1tjmEAAAAXElEQVQoz5XLsRGAQAhE0dWxjs2tZKs3JrcSg/MUlYORBOYzb9oQz+xuUvFjJAiY/ggCntSCbV2kFOyhk0rwLicpBH1qJBd8NlMl+I6mXPBbTWOxRACwNRG7wscB7eQO5yBktpIAAAAASUVORK5CYII=',
	},
]#すとーむ氏に怒られたら消します(爆)


#-----拡張子を入れた辞書/配列作成-----
ext_dict = {#全て小文字で！
	'image': [
		['.jpg', '.jpeg'],#JPEG品質指定必須
		['.bmp', '.png'],#JPEG品質指定不要
	],
	'sound': [
		['.wav', '.mp3'],#OGG化時変換必須
		['.nbz'],#既にwavへ変換済のはず
		['.ogg'],#変換後
	]
}

all_image = []#全拡張子用画像配列
for i in ext_dict['image']:
	all_image.extend(i)

all_repsound = (ext_dict['sound'][0] + ext_dict['sound'][1])#全置換用音源配列
all_convsound = (ext_dict['sound'][0] + ext_dict['sound'][2])#全変換用音源配列


######################################## GUI表示部分 ########################################
kbps_list = ['128', '112', '96', '64', '56', '48', '32']
Hz_list = ['44100', '22050', '11025']

col = [
	[sg.Text('入力先：'), sg.InputText(k='input_dir', size=(67, 15), readonly=True), sg.FolderBrowse()],
	[sg.Text('出力先：'), sg.InputText(k='output_dir', size=(67, 15), readonly=True), sg.FolderBrowse()],
]

frame_1 = sg.Frame('画像', [
	[sg.Text('変換する解像度を指定：')],
	[sg.Radio(text='320x240', group_id='A', k='res_320'),
	 sg.Radio(text='360x270', group_id='A', k='res_360', default=True),
	 sg.Radio(text='そのまま', group_id='A', k='res_NoChange')],
	[sg.Text('JPG品質：'), sg.Slider(range=(100,1), default_value=95, k='jpg_quality', pad=((0,0),(0,0)), orientation='h')],
	[sg.Checkbox('無透過のPNGをJPGに変換&拡張子偽装', k='jpg_mode', default=True)],
	[sg.Checkbox('透過用BMPの横解像度を偶数に指定', k='img_even', default=True)],
	[sg.Checkbox('カーソルを標準の画像へ強制上書き', k='cur_overwrite', default=False)],
], size=(300, 205))

frame_2 = sg.Frame('音源', [
	[sg.Checkbox('音源をOGGへ圧縮する', k='ogg_mode', default=ffmpeg_exist, disabled=(not ffmpeg_exist))],
	[sg.Text('BGM：'), sg.Combo(values=(kbps_list), default_value='112', readonly=True, k='BGM_kbps', disabled=(not ffmpeg_exist)), sg.Text('kbps'), 
	 sg.Combo(values=(Hz_list), default_value='44100', readonly=True, k='BGM_Hz', disabled=(not ffmpeg_exist)), sg.Text('Hz'),],
	[sg.Text('SE：'), sg.Combo(values=(kbps_list), default_value='56', readonly=True, k='SE_kbps', disabled=(not ffmpeg_exist)), sg.Text('kbps'), 
	 sg.Combo(values=(Hz_list), default_value='22050', readonly=True, k='SE_Hz', disabled=(not ffmpeg_exist)), sg.Text('Hz'),],
], size=(300, 125), pad=(0,0))

frame_3 = sg.Frame('その他', [
	[sg.Checkbox('smjpeg_encode.exeで動画を変換する', k='vid_flag', default=smjpeg_exist, disabled=(not smjpeg_exist))],
	[sg.Checkbox('nsaed.exeで出力ファイルを圧縮する', k='nsa_mode', default=nsaed_exist, disabled=(not nsaed_exist))],
], size=(300, 80), pad=(0,0))

flame_4 = sg.Frame('', [
	[sg.Text(' PSPでの画面表示：'), 
	 sg.Radio(text='拡大しない', group_id='B', k='size_normal', default=True),
	 sg.Radio(text='拡大(比率維持)', group_id='B', k='size_aspect'),
	 sg.Radio(text='拡大(フルサイズ)', group_id='B', k='size_full')],
], size=(530, 40))

flame_5 = sg.Frame('', [
	[sg.Button('convert', pad=(9,6))]
], size=(70, 40))

progressbar = sg.Frame('', [
	[sg.ProgressBar(10000, orientation='h', size=(60, 15), key='progressbar')]
], size=(610, 25))

frame_in_2and3 = sg.Column([[frame_2],[frame_3]])

layout = [
	[col],
	[frame_1,frame_in_2and3],
	[flame_4,flame_5],
	[progressbar]
]

window = sg.Window(window_title, layout, size=(640, 360), element_justification='c', margins=(0,0))#ウインドウを表示


######################################## 関数へ逃しておく処理 ########################################

#-----プログレスバー更新-----
progbar_per = [5,5,10,75,5]#全体の処理のざっくりとした割合([txtデコード, txt置換, 動画, 画像音楽, nsa化])
def func_progbar_update(mode, num, nummax):#イマイチ自分でも何書いてんのか分かんないの笑う

	barstart = ( sum(progbar_per[0:mode]) / sum(progbar_per) * 10000 )
	barmax =( (progbar_per[mode]) / sum(progbar_per) * 10000 )
	
	window['progressbar'].UpdateBar(int(barstart + (num + 1) * (barmax / nummax) ))



#-----入出力先未指定/競合時エラー-----
def func_dir_err():
	global err_flag

	if not (values['input_dir']):#output_dirと表記を合わせるためあえてsearch_dir未使用
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

	os.makedirs(result_dir)#出力用のディレクトリを作成

	if os.path.isfile(search_dir + r'/0.txt') or os.path.isfile(search_dir + r'/00.txt'):#0.txtか00.txt
		for num in range(0, 10):#0~9(00~09).txtまでを調べる
			if os.path.isfile(search_dir + r'/00.txt'):#二桁連番で配列格納を繰り返す00.txtのばあい
				oldtext = (search_dir + r'/' + str(num).zfill(2) + r'.txt')#zfillで先頭を0埋め
			else:#一桁連番で配列格納を繰り返す0.txtのばあい
				oldtext = (search_dir + r'/' + str(num) + r'.txt')
					
			newtext = (result_dir + r'/' + str(num) + r'.txt')

			if os.path.isfile(oldtext):#txtがあれば
				shutil.copy(oldtext,newtext)#コピー
				os.chmod(path=newtext, mode=stat.S_IWRITE)#念の為読み取り専用を外す
				text_list.append(newtext)#シナリオのパスを配列へ格納

	elif os.path.isfile(search_dir + r'/nscript.dat'):#復号化処理を行うnscript.datのばあい
		oldtext = (search_dir + r'/nscript.dat')
		newtext = (result_dir + r'/0.txt')
			
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
	global err_flag
	global game_mode

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
			print('解像度の関係上このソフトは変換できません')
			err_flag = True

	elif oldnsc_search:#ONS解像度旧表記時
		game_mode = int(oldnsc_search.group(1))#作品解像度を代入

	else:#ONS解像度無表記時
		game_mode = 640#作品解像度を代入

	if re.search(r'\*define', text) == None :#*defineがない時
		print('不正なtxtが存在します')
		err_flag = True#シナリオじゃなさそうなのでエラー

	if re.search(r'\n[ |\t]*nsa[ |\t]*\n', text) == None :#nsa読み込み命令が無い時
		text = re.sub(r'\*define', r'*define\nnsa', text, 1)#*define直下に命令追記(保険)



#-----全txtへ行う処理-----
def func_txt_all(text):
	global vid_list_rel
	global alpha_img_list_tup

	#-PSPで使用できない命令を無効化する-
	text = re.sub(r'([\n|\t|:| ])avi "(.+?)",([0|1])', r'\1mpegplay "\2",\3', text)#aviをmpegplayで再生(後に拡張子偽装)
	text = re.sub(r'([\n|\t|:| ])okcancelbox %(.+?),', r'\1mov %\2,1 ;', text)#okcancelboxをmovで強制ok
	text = re.sub(r'([\n|\t|:| ])yesnobox %(.+?),', r'\1mov %\2,1 ;', text)#yesnoboxをmovで強制yes

	#-拡張子置換-
	#変数作成
	if values['ogg_mode']:#全音源ogg変換時
		replace_ext_list = all_repsound#wav/mp3/nbz
	else:#ogg無変換時
		replace_ext_list = ext_dict['sound'][1]#nbzのみ

	#-置換する拡張子をfor文で処理-
	for rp in (replace_ext_list):
		text = text.replace(rp.upper(), '.ogg')#大文字
		text = text.replace(rp.lower(), '.ogg')#小文字(元々小文字のはずだが念の為)

	#-txt内の画像の相対パスを格納 どちらも[2](3個目括弧)がパス部分のはず-
	alpha_img_list_tup += re.findall(r'lsph? ([0-9]{1,3}),"(:.;)?(.+?)"(,(([0-9]{1,3})|(%[0-9]{1,4}))){3}', text)#<手伝ってもらったやつ>
	alpha_img_list_tup += re.findall(r'lsph?2(add|sub)? [0-9]{1,3},"(:.;)?(.+?)"(,((-?[0-9]{1,3})|(%[0-9]{1,4}))){6}', text)#<手伝ってもらったやつ>

	if values['vid_flag']:#動画変換処理を行う場合
		vid_list_rel += re.findall(r'mpegplay "(.+?)",[0|1]', text)#txt内の動画の相対パスを格納
	else:#動画変換処理を行わない場合
		text = re.sub(r'mpegplay "(.+?)",[0|1]:', r'', text)#if使用時 - 再生部分を抹消
		text = text.replace('mpegplay ', ';mpegplay ')#再生部分をコメントアウト

	open(textpath, mode='w').write(text)#全置換処理終了後書き込み



#-----格納されたtxt内の動画の相対パスを処理-----
def func_vid_conv(vid, vid_result):

	if os.path.isfile(vid) == False:#パスのファイルが実際に存在するかチェック
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
		'-qscale', '0',
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

	shutil.move(vidtmpdir + '/output.mjpg', vid_result)#完成品を移動
	shutil.rmtree(vidtmpdir)#作業用フォルダの削除



#-----全画像変換処理部分-----
def func_image_conv(file, file_ext):
	img = Image.open(file)#画像を開く

	if img.format == False:#画像ではない場合(=画像のフォーマットが存在しない場合)
		return#終了 - 拡張子偽装対策
	
	#---arc.nsa向けフォルダ分け用処理---
	if values['nsa_mode'] == True:
		#---先にファイル保存用ディレクトリを作成---
		os.makedirs((search_dir_result.replace(search_dir,(result_dir + r'/arc' ))), exist_ok=True)
		#---ファイル保存先パス用変数を代入---
		result_dir_forfile = (result_dir + r'/arc')

	else:#通常時フォルダ分け用処理
		os.makedirs((search_dir_result.replace(search_dir,result_dir)), exist_ok=True)#保存先作成
		result_dir_forfile = result_dir#保存先パス用変数を代入


	#---出力先パス用変数の代入---
	file_result = (file.replace(search_dir,result_dir_forfile))

	#---変換後サイズを指定---
	result_width = round(img.width*per)
	result_height = round(img.height*per)
	
	#---拡張子偽装済みカーソル(!?)対策のため名前だけ取り出し変数に代入---
	file_nameonly = os.path.splitext(os.path.basename(file))[0]#実際あるんですよ行儀悪い同人ゲーとかで

	#---通常画像とカーソル画像がココで分岐---
	if file_nameonly + r'.bmp' in cur_dictlist[0].keys():#画像がカーソル

		#---カーソル強制上書きモード判断---
		if values['cur_overwrite'] == True:
			cur_conv = True

		else:
			#---読み込んだものと同名のカーソルを辞書から持ってくる&デコード&代入---
			img_default = Image.open(BytesIO(base64.b64decode(cur_dictlist[2][file_nameonly + r'.bmp'])))

			#---画素比較のためnumpyへ変換---
			np_img_default = np.array(img_default)
			np_img = np.array(img)

			#---結果を変数へ代入---
			cur_conv = np.array_equal(np_img, np_img_default)

		#---画素比較---
		if cur_conv:#カーソルが公式の画像と同一の時
			if values['res_NoChange']:#解像度無変更時
				#-変更の必要なし→そのまま代入-
				img_resize = img_default

			else:#解像度変更時
				#-縮小率50%を境にアイコンサイズ(大/小)を決定-
				cur_dictnum = int(per < 0.5)#bool(T/F)の結果をint(1/0)にしているがもしかしたら型変換不要かも？

				#-読み込んだものと同じカーソルの縮小版を辞書から持ってくる&デコード&代入-
				img_resize = Image.open(BytesIO(base64.b64decode(cur_dictlist[cur_dictnum][file_nameonly + r'.bmp'])))

		else:#カーソルが独自の画像の時
			if (img.mode != 'RGB'):#RGBじゃない画像をRGB形式に
				img = img.convert('RGB')

			#---背景色を目立ちにくい灰色に統一---
			img_datas = img.getdata()
			a_px = img.getpixel((0, 0))#左上の1pxを背景色に指定

			img_px = []#ピクセル代入用配列作成
			for item in img_datas:
				if item == a_px:#背景色と一致したら
					img_px.append((128, 128, 128))#灰色に
				else:#それ以外は
					img_px.append(item)#そのまま
			img.putdata(img_px)#完了

			#---カーソルを切り出し→縮小→再結合---
			sp_val = int(img.width / img.height)#枚数
			img_resize = Image.new('RGBA', (result_height*sp_val, result_height), (128, 128, 128))#結合用画像
			for i in range(sp_val):#枚数分繰り返す
				img_crop = img.crop((img.height*i, 0, img.height*(i+1), img.height))#画像切り出し
				img_crop = img_crop.resize((result_height-1, result_height-1))#縮小 - 輪郭ボケを限界まで減らすためNEAREST(無指定)
				img_resize.paste(img_crop, (result_height*i, 1))#結合用画像へ貼り付け - 上1pxは必ず空ける(透過判定pxのため)

		#---画像保存---
		img_resize.save(file_result, 'PNG')#容量削減のためPNG


	else:#画像がカーソルではない

		#---RGBじゃない画像をRGB形式に(但しRGBAはそのまま)---
		if (img.mode != 'RGB') and (img.mode != 'RGBA'):
			img = img.convert('RGB')

		#---縦/横幅指定が0以下の時1に---
		if result_width < 1:#流石に1切ると変換できないので
			result_width = 1
		if result_height < 1:
			result_height = 1

		#---lsp系の透過命令で呼び出された画像かどうかをチェック---
		lsp_img = (file.lower() in alpha_img_list)#lsp_imgにはT/Fが入る

		#---画像に透明部分があるとNスクに扱われているか(偽装JPG化が不可能か)をチェック---
		alpha_img = ( lsp_img or (img.mode == 'RGBA' or 'transparency' in img.info) )#alpha_imgにはT/Fが入る - Tなら無理

		#---立ち絵用横幅偶数指定---
		if int(img.width) >= 4 and int(img.height) >= 4 and alpha_img == False and values['img_even']:#横4px以上&透明部分なし&偶数指定ON

			#---ピクセルの色数を変数に代入---
			chara_mainL = img.getpixel((1, 1))#本画像部分左上1px - 1
			chara_mainR = img.getpixel((img.width/2-1, 1))#本画像部分右上1px - 2
			chara_alphaL = img.getpixel((img.width/2, 1))#透過部分左上1px - 3
			chara_alphaR = img.getpixel((img.width-1, 1))#透過部分右上1px - 4

			if chara_mainL == chara_mainR and chara_alphaL == chara_alphaR == (255,255,255):#1,2が同一&3,4が白
				result_width = math.ceil(result_width/2)*2 #(横幅/2の切り上げ)*2で横幅を偶数へ→立ち絵横の謎の縦線回避

		#---画像保存処理変数代入---
		if lsp_img:#lsp_imgは輪郭がぼける(≒ゴミが入る)のを極力防ぐためNEAREST
			img_resize = img.resize((result_width, result_height), Image.NEAREST)
		else:#それ以外の画像は最高画質のLANCZOS
			img_resize = img.resize((result_width, result_height), Image.LANCZOS)	

		#---画像保存---
		if (file_ext in (ext_dict['image'][1])) and alpha_img == False and values['jpg_mode']:#pngかbmp&jpg圧縮モード&透明部分なし
			img_resize.save((file_result), 'jpeg', quality=int(values['jpg_quality']))#jpgmode ON時の不透明png/bmp 拡張子偽装

		else:#拡張子そのまま
			if file_ext in (ext_dict['image'][0]):#元々jpg
				img_resize.save(file_result, quality=int(values['jpg_quality']))
			else:#それ以外(pngかbmp)
				img_resize.save(file_result)



#-----全音源変換処理部分-----
def func_music_conv(file):
	#---arc.nsa向けフォルダ分け用処理---
	if values['nsa_mode']:
		#---ディレクトリ名に"bgm"とあるかで判定---
		if 'bgm' in str(search_dir_result):
			arc_num_sound = r'2'
		else:
			arc_num_sound = r'1'

		#---先にファイル保存用ディレクトリを作成---
		os.makedirs((search_dir_result.replace(search_dir, (result_dir + r'/arc' + arc_num_sound))), exist_ok=True)
		#---ファイル保存先パス用変数を代入---
		result_dir_forfile = (result_dir + r'/arc' + arc_num_sound)
		
	else:#通常時フォルダ分け用処理
		os.makedirs((search_dir_result.replace(search_dir,result_dir)), exist_ok=True)#保存先作成
		result_dir_forfile = result_dir#保存先パス用変数を代入

	#---ogg変換用処理---
	if values['ogg_mode']:
		#---ディレクトリ名に"bgm"とあるかで判定---
		if 'bgm' in str(search_dir_result):	
			result_kbps = str(values['BGM_kbps']) + 'k'
			result_Hz = str(values['BGM_Hz'])
		else:
			result_kbps = str(values['SE_kbps']) + 'k'
			result_Hz = str(values['SE_Hz'])

	#---出力先パスの代入---
	file_result = (file.replace(search_dir,result_dir_forfile))
	
	if values['ogg_mode']:
		subprocess.run(['ffmpeg', '-y',
			'-i', file,
			'-ab', result_kbps,
			'-ar', result_Hz,
			'-ac', '2',
			(os.path.splitext(file_result)[0] + ".ogg"),
			], shell=True, **subprocess_args(True))
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
		shutil.move((os.path.dirname(sys.argv[0])) + r"/tools/arc.nsa" , arc_num_dir + '.nsa')#nsa移動
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
	open(result_dir + r'/ons.ini', 'w').writelines(ons_ini)



######################################## Event Loop ########################################
while True:
	event, values = window.read()
	if event is None or event == 'Exit':
		break

	elif event == 'convert':
		err_flag = False

		#-----とりあえず真っ先にウインドウの操作無効化-----
		window['convert'].update(disabled=True)
		window.disable()
		window.refresh()

		#-----特定の機能を利用しない場合プログレスバーの計算からはずす-----
		if values['vid_flag'] == False:
			progbar_per_2 = progbar_per[2]
			progbar_per[2] = 0
		if values['nsa_mode'] == False:
			progbar_per_4 = progbar_per[4]
			progbar_per[4] = 0

		#-----ディレクトリのパスを先に代入-----
		search_dir = (values['input_dir'])
		result_dir = (values['output_dir'] + r'/result')

		#-----入出力先のパスが競合しそうなら勝手に消す-----
		if os.path.exists(result_dir):
			shutil.rmtree(result_dir)

		#-----[関数]入出力先未指定/競合時エラー-----
		func_dir_err()

		#-----[関数]シナリオ復号&コピー周り-----
		if err_flag == False:	
			text_list = []
			func_ext_dec()
			func_progbar_update(0, 1, 1)#左から順に{種類, 現在の順番, 最大数}

		#-----シナリオ読み込み&置換処理-----
		if err_flag == False:
			vid_list_rel = []#txt内の動画の相対パスを格納するための配列
			alpha_img_list_tup = []#txt内の画像(透明指定だけど透過画像じゃないやつ)の相対パスを格納するための配列

			for i,textpath in enumerate(text_list):
				text = open(textpath, 'r', errors="ignore").read()#テキストを読み込み

				if textpath == (result_dir + r'/0.txt'):#[関数]0.txt読み込み時(初回限定)処理
					game_mode = 0
					func_txt_zero(text)

				if err_flag == False:#[関数]全txtへ行う処理
					func_txt_all(text)

				func_progbar_update(1, i, len(text_list))#左から順に{種類, 現在の順番, 最大数}

		#-----ココから本処理(エラーメッセージなし)-----
		if err_flag == False:

			#---解像度指定---
			if values['res_320']:#ラジオボタンから代入
				resolution = 320
			elif values['res_360']:
				resolution = 360
			elif values['res_NoChange']:
				resolution = game_mode

			#-----txtから動画再生命令を検知し動画をPSP専用形式へ置換(&拡張子偽装)-----
			if values['vid_flag']:
				vid_res = (str(resolution) + r':' + str(int(resolution/4*3)))#引数用動画解像度代入

				#---[関数]格納されたtxt内の動画の相対パスを処理---
				for i,vid_rel in enumerate(set(vid_list_rel)):#set型で重複削除
					vid_rel = vid_rel.replace('\\','/')#文字列として扱いづらいのでとりあえず\置換
					vid = search_dir + '/' + vid_rel#格納された相対パスを絶対パスへ - os.path.join使うべきかもなぁ
					vid_result = result_dir + '/' + vid_rel#処理後の保存先 - ここもos.path.join使うべきかもなぁ			
				
					func_vid_conv(vid, vid_result)
					func_progbar_update(2, i, len(set(vid_list_rel)))#左から順に{種類, 現在の順番, 最大数}


			#-----画像/音源処理-----
			per = resolution / game_mode#画像縮小率=指定解像度/作品解像度

			#---txtから透過処理のあるスプライト表示命令を検知し画像のパスを配列へ格納---
			alpha_img_list = []
			for alpha_img_tup in set(alpha_img_list_tup) :#set型で重複削除
				alpha_img_list.append( ( search_dir + '/' + (alpha_img_tup[2].replace('\\','/')) ).lower() )#格納された相対パスを小文字に&絶対パスへ

			#---全ファイルのフルパスを配列に代入---
			search_dir_result = ""
			files_list = []
			for search_dir_result, sub_dirs, files_list_rel in os.walk(search_dir): #サブフォルダ含めファイル検索
				for file_name in files_list_rel:
					files_list.append(os.path.join(search_dir_result,file_name))#パスを代入


			for i,file in enumerate(files_list):

				#フルパスからまたディレクトリ部分切り出し
				search_dir_result = os.path.dirname(file)#さっきせっかく結合したのに無駄だなぁ
				
				file = file.replace('\\','/')#文字列として扱いづらいのでとりあえず\置換
				file_ext = (os.path.splitext(file)[1]).lower()#パスから拡張子を取り出し&強制小文字

				#-[関数]全画像変換処理部分-
				if file_ext in (all_image):
					func_image_conv(file, file_ext)

				#-[関数]全音源変換処理部分-
				elif file_ext in (all_convsound):
					func_music_conv(file)
				
				func_progbar_update(3, i, len(files_list))#左から順に{種類, 現在の順番, 最大数}


			#-----[関数]arc.nsa圧縮------
			if values['nsa_mode']:
				arc_num_list = ['arc', 'arc1', 'arc2']
				for i,arc_num in enumerate(arc_num_list):		
					func_arc_nsa(arc_num)
					func_progbar_update(4, i, len(arc_num_list))

			#-----[関数]ons.ini作成------
			func_ons_ini()
			
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