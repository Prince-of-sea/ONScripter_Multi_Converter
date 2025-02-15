#!/usr/bin/env python3
from pathlib import Path
import concurrent.futures
import glob
import os
import re
import chardet


# ONScripter_Multi_Converter用タイトル情報管理関数
def title_info():

	#タイトル情報管理辞書作成
	info = {
		'brand': 'minori',
		'date': 20040723,
		'title': 'はるのあしおと',
		'requiredsoft': [],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),

		'version': [
			'はるのあしおと パッケージ版(2004/07/23)',
		],

		'notes': [
			'本作の変換は主にRightHand氏が制作したものです',
			'詳細につきましては、\ngithub.com/migite/HARU2ONSを確認してください',
		]
	}

	#作った辞書をreturn
	return info


# ONScripter_Multi_Converter用アーカイブ自動展開関数
def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):

	#GARBroを使って展開する関数をutils.pyから呼び出す
	from utils import extract_archive_garbro

	#並列で処理する最大数を引数の辞書から持ってきて変数に代入
	num_workers = values_ex['num_workers']
	
	#入力元のパスを引数の辞書から持ってきて変数に代入
	input_dir = values['input_dir']
	
	#並列処理を(さっき代入してきた最大数をセットして)開始
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:

		#並列処理管理用の配列を作成
		futures = []
		
		#展開予定のpazファイルの名前をfor文で回す
		for paz_name in ['bg', 'bgm', 'mov', 'scr', 'se', 'st', 'sys', 'voice']:

			#pazファイルのフルパスを代入
			p = Path(input_dir / Path(paz_name + '.paz'))

			#出力先のフルパスを代入
			e = Path(pre_converted_dir / paz_name)

			#pazファイルがなければ
			if not p.exists():

				#(ファイル名)が見つかりませんエラー
				raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))
			
			#処理予定のタスクへ「"GARBroを使って展開する関数"へpazファイルと出力先を引数にして処理」を追加
			futures.append(executor.submit(extract_archive_garbro, p, e, 'png'))

		#並列処理タスクがすべて終わるまでここで待つ
		concurrent.futures.as_completed(futures)

	#bgフォルダ内の.aniファイルのパスをfor文で回す
	for filepath in Path(pre_converted_dir / 'bg').glob('*.ani'):

		#削除
		filepath.unlink()
	
	#stフォルダ内の.aniファイルのパスをfor文で回す
	for filepath in Path(pre_converted_dir / 'st').glob('*.ani'):

		#削除
		filepath.unlink()
	
	#scrフォルダ内のev~.scファイルのパスをfor文で回す
	for filepath in Path(pre_converted_dir / 'scr').glob('ev*.sc'):

		#削除
		filepath.unlink()

	#scrフォルダ内のtest.scファイルを削除
	Path(pre_converted_dir / 'scr' / 'test.sc').unlink()

	return


def default_txt():
	s = ''';$V2000G1000S800,600L10000
*define
caption "HARU2NS4ONSVer0.84"
nsa
globalon
rmenu "セーブ",save,"ロード",load,"リセット",reset,"スキップ",skip,"ログ",lookback
pretextgosub *pretext_sb
windowback
savenumber 18
humanz 30
selectvoice "","sys\\cursor.wav","sys\\click.wav"

mov %TEXT_size,1

;numalias領域
numalias st_x1,51
numalias st_y1,52
numalias st_x2,53
numalias st_y2,54
numalias st_x3,55
numalias st_y3,57
numalias st_x4,58
numalias st_y4,59
numalias st_x5,60
numalias st_y5,61
numalias x1_default,62
numalias x2_default,63
numalias x3_default,64
numalias x4_default,65
numalias x5_default,66
numalias winmode,100
numalias A_001,201
numalias clearChika,202
numalias clearNagomi,203
numalias clearYuduki,204
numalias clearYuu,205
numalias favNagomi,206
numalias favYuduki,207
numalias favYuu,208
numalias B_004,209
numalias B_008,210
numalias B_011,211
numalias B_015,212
numalias C_007,213
numalias C_012,214
numalias C_015,215
numalias C_017,216
numalias D_004,217
numalias D_006,218
numalias D_007,219
numalias D_009,220
numalias D_013,221
numalias D_015,222
numalias E_007,223
numalias E_008,224
numalias route,225
numalias Vol_bgm,250
numalias Vol_voice,251
numalias Vol_Se,252
numalias TEXT_size,260
numalias eroskip,261

;defsub領域
defsub setwin0
defsub setwin1
defsub setwin2
defsub cspchar
defsub csptitle
defsub cspmemory
defsub stposition

;effect領域
effect 2,10,300		;エフェクト番号2に効果番号10(クロスフェード)の300ミリ秒を割り当て

game
;スプライト番号一覧
;10,11　名前表示
;30~34　立ち絵
;37,38　演出背景(現在廃止中)
;39　標準背景
;41~45　タイトル画面ボタン
;49　タイトル背景

;------------------定義域ここまで-------------------

*start

goto *title

*pretext_sb
saveoff

gettag $0

if %winmode == 0 csp 11

if %winmode == 1 lsp 10,":s/30,30,0;#ffffff$0",55,430
if %winmode == 1 lsp 11,"sys\\namePanel.png",0,417,128

print 1

saveon
return


*setwin0
textoff
csp 10:csp 11
mov %winmode,0
return

*setwin1
textoff
if %TEXT_size == 0 setwindow3 50,480,30,3,24,24,1,2,10,1,1,":a;sys/msgPanel.png",0,417
if %TEXT_size == 1 setwindow3 50,480,26,4,26,26,1,2,10,1,1,":a;sys/msgPanel.png",0,417
if %TEXT_size == 2 setwindow3 50,480,22,4,30,30,1,2,10,1,1,":a;sys/msgPanel.png",0,417
mov %winmode,1
return

*setwin2
textoff
if %TEXT_size == 0 setwindow3 100,50,20,10,24,24,1,2,10,1,1,":a;sys/fullPanel.png",0,0
if %TEXT_size == 1 setwindow3 100,50,18,10,26,26,1,2,10,1,1,":a;sys/fullPanel.png",0,0
if %TEXT_size == 2 setwindow3 100,50,16,10,28,28,1,2,10,1,1,":a;sys/fullPanel.png",0,0
mov %winmode,2
return

*cspchar
csp 37
csp 38
csp 30
csp 31
csp 32
csp 33
csp 34
print 1
return

*csptitle
csp 41
csp 42
csp 43
csp 44
csp 45
csp 49
print 10,300
return

*cspmemory
csp 51
csp 52
csp 53
csp 54
csp 55
csp 56
csp 57
csp 58
return

*stposition
getspsize 34,%st_x1,%st_y1
getspsize 33,%st_x2,%st_y2
getspsize 32,%st_x3,%st_y3
getspsize 31,%st_x4,%st_y4
getspsize 30,%st_x5,%st_y5

div %st_x1,2
add %st_x1,%x1_default
sub %st_x1,800
sub %st_y1,600
mov %st_x1,-%st_x1
mov %st_y1,-%st_y1

amsp 34,%st_x1,%st_y1
vsp 34,1

if %st_x2 == 0 print 1
if %st_x2 == 0 return

div %st_x2,2
add %st_x2,%x2_default
sub %st_x2,800
sub %st_y2,600
mov %st_x2,-%st_x2
mov %st_y2,-%st_y2

amsp 33,%st_x2,%st_y2
vsp 33,1

if %st_x3 == 0 print 1
if %st_x3 == 0 return 

div,%st_x3,2
add %st_x3,%x3_default
sub %st_x3,800
sub %st_y3,600
mov %st_x3,-%st_x3
mov %st_y3,-%st_y3

amsp 32,%st_x3,%st_y3
vsp 32,1

if %st_x4 == 0 print 1
if %st_x4 == 0 return

div %st_x4,2
add %st_x4,%x4_default
sub %st_x4,800
sub %st_y4,600
mov %st_x4,-%st_x4
mov %st_y4,-%st_y4

amsp 31,%st_x4,%st_y4
vsp 31,1

if %st_x5 == 0 print 1
if %st_x5 == 0 return

div %st_x5,2
add %st_x5,%x5_default
sub %st_x5,800
sub %st_y5,600
mov %st_x5,-%st_x5
mov %st_y5,-%st_y5

amsp 30,%st_x5,%st_y5
vsp 30,1

return

;----------追加命令ここまで-------------

*title
csp -1
rmode 0
bgm "bgm\\bgm_22.ogg"
lsph 41,":a;sys/mainmenuNewGame.png",570,45
lsph 42,":a;sys/mainmenuLoadGame.png",570,90
lsph 43,":a;sys/mainmenuSystem.png",570,135
lsph 44,":a;sys/mainmenuMemories.png",570,180
lsph 45,":a;sys/mainmenuExit.png",570,225
lsph 49,":a;sys/topmenu.png",0,0

vsp 49,1

exbtn 41,41, "P41"
exbtn 42,42, "P42"
exbtn 43,43, "P43"
exbtn 44,44, "P44"
exbtn 45,45, "P45"

exbtn_d "C41C42C43C44C45"

*title_loop

btnwait %0
if %0 == 0 goto *title_loop
if %0 == -1 goto *title_loop

if %0 == 41 goto *startmode
if %0 == 42 goto *loadmode
if %0 == 43 goto *settingmode
if %0 == 44 goto *memory
if %0 == 45 goto *endmode

goto *title_loop
end

*startmode
csptitle
rmode 1
bgmstop
saveon
setwin0
erasetextwindow 0
goto *A_001
end

*loadmode
csptitle
saveon
lsph 49,":a;sys/saveloadBase.png",0,0:vsp 49,1
print 1
systemcall load
bgmstop
goto *title
end

*settingmode
csptitle
lsph 49,":a;sys/configBase.png",0,0:vsp 49,1
print 1
bgmstop

*settingmenu
setwin2
select "音量設定",*volconfig_select,"文字サイズ変更",*mojisize,"Ｈシーンスキップ",*skipero,"おわる",*title


*volconfig_select
select "かんたん設定",*volconfig,"詳細設定",*volmenu_GUI


*volconfig
setwin1
selnum %Vol_bgm,"音量設定　ＢＧＭ１００","音量設定　ＢＧＭ５０","音量設定　ＢＧＭ０"

if %Vol_bgm == 0 mov %Vol_bgm,100
if %Vol_bgm == 1 mov %Vol_bgm,50
if %Vol_bgm == 2 mov %Vol_bgm,0

bgmvol %Vol_bgm

selnum %Vol_voice,"音量設定　ＶＯＩＣＥ１００","音量設定　ＶＯＩＣＥ５０","音量設定　ＶＯＩＣＥ０"

if %Vol_voice == 0 mov %Vol_voice,100
if %Vol_voice == 1 mov %Vol_voice,50
if %Vol_voice == 2 mov %Vol_voice,0

voicevol %Vol_voice

selnum %Vol_Se,"音量設定　ＳＥ１００","音量設定　ＳＥ５０","音量設定　ＳＥ０"

if %Vol_Se == 0 mov %Vol_Se,100
if %Vol_Se == 1 mov %Vol_Se,50
if %Vol_Se == 2 mov %Vol_Se,0

sevol %Vol_Se

設定が完了しました\\
setwin0
goto *settingmenu

*mojisize
setwin1
selnum %TEXT_size,"文字サイズ小","文字サイズ中","文字サイズ大"


設定が完了しました\\
setwin0
goto *settingmenu

*skipero
setwin1
selnum %eroskip,"オフ","オン"
設定が完了しました\\
goto *settingmenu

*memory

lsph 69,"sys\\exmPrologue.png",0,0:vsp 49,1
print 1
wait 2000
cspmemory
goto *title
end

*endmode
csptitle
;bg black,10,300		;ここ多分記述ミスなので修正しますた
bg black,2				;こっちではエフェクト番号だけ指定、定義節で効果番号とエフェクト番号の紐づけ(?)を行うのが正解
end


;------ 以下Prince-of-seaが勝手に移植したガバガバGUI音量設定 --------------
*volmenu_GUI
	;https://gist.github.com/Prince-of-sea/325b8ae6912ecf23316a71c3d008480c
	;文字/数字/スプライト/ボタン
	;全部130~149までを使ってます - 競合に注意
	
	;はるのあしおと専用
	vsp 49,0
	bg black,2
	
	;バー文字列定義
	mov $130,":s;#FFFFFF#666666○――――――――――"
	mov $131,":s;#FFFFFF#666666―○―――――――――"
	mov $132,":s;#FFFFFF#666666――○――――――――"
	mov $133,":s;#FFFFFF#666666―――○―――――――"
	mov $134,":s;#FFFFFF#666666――――○――――――"
	mov $135,":s;#FFFFFF#666666―――――○―――――"
	mov $136,":s;#FFFFFF#666666――――――○――――"
	mov $137,":s;#FFFFFF#666666―――――――○―――"
	mov $138,":s;#FFFFFF#666666――――――――○――"
	mov $139,":s;#FFFFFF#666666―――――――――○―"
	mov $140,":s;#FFFFFF#666666――――――――――○"
	
*volmenu_loop
	;取得
	getbgmvol   %130
	getsevol    %131
	getvoicevol %132
	
	;文字列変換
	itoa2 $141,%130
	itoa2 $142,%131
	itoa2 $143,%132
	
	;バー代入
	if %130==  0 mov $146,$130
	if %130== 10 mov $146,$131
	if %130== 20 mov $146,$132
	if %130== 30 mov $146,$133
	if %130== 40 mov $146,$134
	if %130== 50 mov $146,$135
	if %130== 60 mov $146,$136
	if %130== 70 mov $146,$137
	if %130== 80 mov $146,$138
	if %130== 90 mov $146,$139
	if %130==100 mov $146,$140
	if %131==  0 mov $147,$130
	if %131== 10 mov $147,$131
	if %131== 20 mov $147,$132
	if %131== 30 mov $147,$133
	if %131== 40 mov $147,$134
	if %131== 50 mov $147,$135
	if %131== 60 mov $147,$136
	if %131== 70 mov $147,$137
	if %131== 80 mov $147,$138
	if %131== 90 mov $147,$139
	if %131==100 mov $147,$140
	if %132==  0 mov $148,$130
	if %132== 10 mov $148,$131
	if %132== 20 mov $148,$132
	if %132== 30 mov $148,$133
	if %132== 40 mov $148,$134
	if %132== 50 mov $148,$135
	if %132== 60 mov $148,$136
	if %132== 70 mov $148,$137
	if %132== 80 mov $148,$138
	if %132== 90 mov $148,$139
	if %132==100 mov $148,$140
	
	;画面作成
	lsp 130,":s;#FFFFFF［Ｃｏｎｆｉｇ］", 50, 50
	lsp 131,":s;#FFFFFF#666666リセット", 400,450
	lsp 132,":s;#FFFFFF#666666戻る",     550,450
	
	lsp 135,":s;#FFFFFFＢＧＭ",           50,150
	lsp 136,":s;#FFFFFF#666666＜",       200,150
	lsp 137,$146,                        250,150
	lsp 138,":s;#FFFFFF#666666＞",       550,150
	lsp 139,":s;#FFFFFF#666666"+$141,    600,150
	
	lsp 140,":s;#FFFFFFＳＥ",             50,250
	lsp 141,":s;#FFFFFF#666666＜",       200,250
	lsp 142,$147,                        250,250
	lsp 143,":s;#FFFFFF#666666＞",       550,250
	lsp 144,":s;#FFFFFF#666666"+$142,    600,250
	
	lsp 145,":s;#FFFFFFＶＯＩＣＥ",       50,350
	lsp 146,":s;#FFFFFF#666666＜",       200,350
	lsp 147,$148,                        250,350
	lsp 148,":s;#FFFFFF#666666＞",       550,350
	lsp 149,":s;#FFFFFF#666666"+$143,    600,350
	
	print 1
	
	;ボタン定義
	bclear
	spbtn 131,131
	spbtn 132,132
	spbtn 136,136
	spbtn 138,138
	spbtn 141,141
	spbtn 143,143
	spbtn 146,146
	spbtn 148,148
	
	;入力待ち
	btnwait %140
	
	if %140==131 bgmvol 100:sevol 100:voicevol 100
	if %140==132 csp -1:reset
	if %140==136 if %130!=  0 sub %130,10:bgmvol %130
	if %140==138 if %130!=100 add %130,10:bgmvol %130
	if %140==141 if %131!=  0 sub %131,10:sevol %131
	if %140==143 if %131!=100 add %131,10:sevol %131
	if %140==146 if %132!=  0 sub %132,10:voicevol %132
	if %140==148 if %132!=100 add %132,10:voicevol %132
	
goto *volmenu_loop
;音量調整ここまで


;-------------------シナリオここから------------------

'''

	return s


# メイン関数
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)



	same_hierarchy = str(pre_converted_dir)

	scenario_dir = os.path.join(same_hierarchy,'scr')

	# with open(os.path.join(same_hierarchy, 'default.txt')) as f:
	# 	txt = f.read()
	
	txt=default_txt()

	pathlist = glob.glob(os.path.join(scenario_dir, '*.sc'))

	#初期値リストです
	Screen_line = 0
	Messege_line = 0
	Messege_before = 0
	Labelcount = 0

	if not values: print('コンバートを開始します…')

	for snr_path in pathlist:

		with open(snr_path, 'rb') as f:
			char_code =chardet.detect(f.read())['encoding']

		with open(snr_path, encoding=char_code, errors='ignore') as f:
			
			txt += 'cspchar\ngoto *title\n;--------------- '+ os.path.splitext(os.path.basename(snr_path))[0] +' ---------------\nend\n*' + os.path.splitext(os.path.basename(snr_path))[0] + '\nlookbackflush\n'
			txt = txt.replace('//', ';;;')

			#print(txt)
			
			for line in f:
				#命令が特殊な形は先に分けておきます
				TKT_line =  re.match(r'\.message\s([0-9]+)\t(.*?)\t(.*?)\t(.+)',line)
				Stage_st_line =re.match(r'\.stage\s(\S*)\s(\d*)\s(\S*)\s(\d*)',line)
				Stage_line = re.match(r'\.stage',line)
				BGM_line = re.match(r'\.playBGM',line)
				SE_line = re.match(r'\.playSE (\S*)',line)
				Window_line = re.match(r'\.panel\s([0-9]+)([\s]*)([0-9]*)',line)
				Label_line = re.match(r'\.label (\S*)',line)
				Chain_line = re.match(r'\.chain (\S*).sc',line)
				Include_line = re.match(r'\.include\s(\S*).sc',line)
				Shake_line = re.match(r'\.shakeScreen\t([A-Z]+)\t([0-9]+)\t([0-9]+)',line)
				Wait_line = re.match(r'\.wait (\d+)',line)
				Select3_line = re.match(r'\.select\s(\S*):(\S*)\s(\S*):(\S*)\s(\S*):(\S*)',line)
				Select2_line = re.match(r'\.select\s(\S+):(\S+)\s(\S+):(\S+)',line)
				movie_line = re.match(r'\.movie\s(\S*)\s(\S*).mpg',line)
				if_line = re.match(r'\.if (\S*) (\S*) (\d*) (\S*)',line)
				Jump_line = re.match(r'\.goto\s(\S*)',line)
				mov_line = re.match(r'\.setGlobal\s(\S*) = (\S*)',line)
				add_line = re.match(r'\.set (\S*) =',line)
				trancelate_line = re.match(r'\.transition (\d*) (\S*) (\d*)',line)
				erojump_line = re.match(r'#include\s(\S*).sc',line)
				eroreturn_line = re.match(r';■エロシーンここまで',line)
				vscroll_line = re.match(r'\.vscroll\s(\d+)\s(\d+)',line)
				hscroll_line = re.match(r'\.hscroll\s(\d+)\s(\d+)',line)



				if TKT_line:
					Space_line = ''
					Messege_line = TKT_line[1]
					VoicePath = TKT_line[2]
					NoNameKigo = re.sub(r'@|#','',TKT_line[3])
					NorubyTXT = re.sub(r'\{\S*}|\\n|\\N|\\a|\\w','',TKT_line[4])

					#print(Screen_line)
					if  Screen_line == 0:

						Enter_line = '\\\n'

					elif Screen_line == 1:

						if Messege_line == Messege_before:
							
							Enter_line = '@\n'

						else:
							Enter_line = '\\\n'


					else:

						Enter_line = '\\\n'

					linea = 'dwave 0,"voice\\' + VoicePath + '.ogg"\n'
					lineb = '[' + NoNameKigo + ']' + NorubyTXT + Enter_line

					if VoicePath == '':
						line = lineb
					
					else:
						line = linea + lineb

					Messege_before = Messege_line

					#print(line)

					#if '#' in line:
						#print(line)

				elif Stage_line:
					#BGや立ち絵の調節をします。最長一致から並べていきます

					line = re.sub(r'\.stage\s\* |\.stage\s|\:\[(\S+)\,(\S+)\,(\S+)\]ol_(\S+).png|\:ol_(\S+).png|\:\[(\S+)\,(\S+)\,(\S+)\]','',line)
					#print(line)
					#背景 + 立ち絵最大5人で分類していきます。?
					Stage1_line = re.match(r'(\S+)\s(\d+)\s(\d+)\sst(\S+)\s(\d+)\sst(\S+)\s(\d+)\sst(\S+)\s(\d+)\sst(\S+)\s(\d+)\sst(\S+)\s(\d*)',line)
					Stage2_line = re.match(r'(\S+)\s(\d*)\s(\d*)\sst(\S+)\s(\d*)\sst(\S+)\s(\d*)\sst(\S+)\s(\d*)\sst(\S)\s(\d+)',line)
					Stage3_line = re.match(r'(\S+)\s(\d*)\s(\d*)\sst(\S+)\s(\d*)\sst(\S+)\s(\d*)\sst(\S+)\s(\d*)',line)
					Stage4_line = re.match(r'(\S+)\s(\d*)\s(\d*)\sst(\S+)\s(\d*)\sst(\S+)\s(\d*)',line)
					Stage5_line = re.match(r'(\S+)\s(\d*)\s(\d*)\sst(\S+)\s(\d*)',line)
					#ここから画面効果を含んだパターンです。画面効果は現在省いています
					Stage6_line = re.match(r'(\S+)\s(\S+)\s(\d+)\s(\d+)\sst(\S+)\s(\d)',line)
					Stage7_line = re.match(r'(\S+)\s(\S{4,})\s(\d+)\s(\d+)',line)
					#ここからはst命令という名の背景だったり拡大などです
					Stage11_line = re.match(r'st(\S+)\s(\S{4,})\s(\d*)\s(\d*)',line)
					Stage12_line = re.match(r'st(\S+)\s(\d*)\s(\d*)',line)
					#最後に背景表示のみです
					Stage99_line = re.match(r'(\S+)\s(\d*)\s(\d*)',line)

					

					if Stage1_line:
						#print(line)
						#最長一致。背景画像+立ち絵5人
						line0 = 'cspchar\n'
						st1_x = 800 - int(Stage1_line[5])
						st2_x = 800 - int(Stage1_line[7])
						st3_x = 800 - int(Stage1_line[9])
						st4_x = 800 - int(Stage1_line[11])
						st5_x = 800 - int(Stage1_line[13])

						line1 = 'lsph 39,":a;bg\\' + Stage1_line[1] + '",-' + Stage1_line[2] + ',-' + Stage1_line[3] + ':vsp 39,1\n'
						line2 = 'lsph 34,":a;st\\st' + Stage1_line[4] + '",0,0\n'
						line3 = 'lsph 33,":a;st\\st' + Stage1_line[6] + '",0,0\n'
						line4 = 'lsph 32,":a;st\\st' + Stage1_line[8] + '",0,0\n'
						line5 = 'lsph 31,":a;st\\st' + Stage1_line[10] + '",0,0\n'
						line6 = 'lsph 30,":a;st\\st' + Stage1_line[12] + '",0,0\n'

						line7 = 'mov %x1_default,' + str(st1_x) + '\n'
						line8 = 'mov %x2_default,' + str(st2_x) + '\n'
						line9 = 'mov %x3_default,' + str(st3_x) + '\n'
						line10 = 'mov %x4_default,' + str(st4_x) + '\n'
						line11 = 'mov %x5_default,' + str(st5_x) + '\n'
						line12 = 'stposition\n'

						line = line0 + line1 + line2 + line3 + line4 +line5 + line6 + line7 + line8 + line9 + line10 + line11 + line12 +'\n'
						#print(line)

					elif Stage2_line:

						line0 = 'cspchar\n'
						st1_x = 800 - int(Stage2_line[5])
						st2_x = 800 - int(Stage2_line[7])
						st3_x = 800 - int(Stage2_line[9])
						st4_x = 800 - int(Stage2_line[11])

						line1 = 'lsph 39,":a;bg\\' + Stage2_line[1] + '",-' + Stage2_line[2] + ',-' + Stage2_line[3] + ':vsp 39,1\n'
						line2 = 'lsph 34,":a;st\\st' + Stage2_line[4] + '",0,0\n'
						line3 = 'lsph 33,":a;st\\st' + Stage2_line[6] + '",0,0\n'
						line4 = 'lsph 32,":a;st\\st' + Stage2_line[8] + '",0,0\n'
						line5 = 'lsph 31,":a;st\\st' + Stage2_line[10] + '",0,0\n'

						line6 = 'mov %x1_default,' + str(st1_x) + '\n'
						line7 = 'mov %x2_default,' + str(st2_x) + '\n'
						line8 = 'mov %x3_default,' + str(st3_x) + '\n'
						line9 = 'mov %x4_default,' + str(st4_x) + '\n'
						line10 = 'stposition\n'

						line = line0 + line1 + line2 + line3 + line4 +line5 + line6 + line7 + line8 + line9 + line10 +'\n'
						#print(line)

					elif Stage3_line:
						#print(line)
						line0 = 'cspchar\n'
						st1_x = 800 - int(Stage3_line[5])
						st2_x = 800 - int(Stage3_line[7])
						st3_x = 800 - int(Stage3_line[9])

						line1 = 'lsph 39,":a;bg\\' + Stage3_line[1] + '",-' + Stage3_line[2] + ',-' + Stage3_line[3] + ':vsp 39,1\n'
						line2 = 'lsph 34,":a;st\\st' + Stage3_line[4] + '",0,0\n'
						line3 = 'lsph 33,":a;st\\st' + Stage3_line[6] + '",0,0\n'
						line4 = 'lsph 32,":a;st\\st' + Stage3_line[8] + '",0,0\n'

						line5 = 'mov %x1_default,' + str(st1_x) + '\n'
						line6 = 'mov %x2_default,' + str(st2_x) + '\n'
						line7 = 'mov %x3_default,' + str(st3_x) + '\n'
						line8 = 'stposition\n'

						line = line0 + line1 + line2 + line3 + line4 +line5 + line6 + line7 + line8 +'\n'

						#print(line)
					elif Stage4_line:
						
						#print(line)
						line0 = 'cspchar\n'
						st1_x = 800 - int(Stage4_line[5])
						st2_x = 800 - int(Stage4_line[7])

						line1 = 'lsph 39,":a;bg\\' + Stage4_line[1] + '",-' + Stage4_line[2] + ',-' + Stage4_line[3] + ':vsp 39,1\n'
						line2 = 'lsph 34,":a;st\\st' + Stage4_line[4] + '",0,0\n'
						line3 = 'lsph 33,":a;st\\st' + Stage4_line[6] + '",0,0\n'

						line4 = 'mov %x1_default,' + str(st1_x) + '\n'
						line5 = 'mov %x2_default,' + str(st2_x) + '\n'
						line6 = 'stposition\n'

						line = line0 + line1 + line2 + line3 + line4 +line5 + line6 +'\n'

					elif Stage5_line:
						line0 = 'cspchar\n'
						st1_x = 800 - int(Stage5_line[5])

						line1 = 'lsph 39,":a;bg\\' + Stage5_line[1] + '",-' + Stage5_line[2] + ',-' + Stage5_line[3] + ':vsp 39,1\n'
						line2 = 'lsph 34,":a;st\\st' + Stage5_line[4] + '",0,0\n'

						line3 = 'mov %x1_default,' + str(st1_x) + '\n'
						line4 = 'stposition\n'
						line = line0 + line1 + line2 + line3 + line4 +'\nprint 1\n'

					elif Stage11_line:
						#print(line)
						line0 = 'cspchar\n'

						line1 = 'lsph 39,":a;bg\\' + Stage11_line[2] + '",-' + Stage11_line[3] + ',-' + Stage11_line[4] + ':vsp 39,1\n'
						line2 = 'lsph 34,":a;bg\\st' + Stage11_line[1] + '",0,0:vsp 34,1\n'

						line = line0 + line1 + line2 + '\nprint 1\n'

					elif Stage12_line:
						#print(line)
						line0 = 'cspchar\n'

						line1 = 'lsph 34,":a;st\\st' + Stage12_line[1] + '",0,0:vsp 34,1\n'

						line = line0 + line1 + '\nprint 1\n'

					elif Stage6_line:
						line0 = 'cspchar\n'
						st1_x = 800 - int(Stage6_line[6])

						line1 = 'lsph 39,":a;bg\\' + Stage6_line[2] + '",-' + Stage6_line[3] + ',-' + Stage6_line[4] + ':vsp 39,1\n'
						line2 = 'lsph 34,":a;st\\st' + Stage6_line[5] + '",' + str(st1_x) + ',0\n'

						line3 = 'mov %x1_default,' + str(st1_x) + '\n'
						line4 = 'stposition\n'

						line = line1 + line2 + line3 + line4 +'\n'

					elif Stage7_line:
						line0 = 'cspchar\n'

						line1 = 'lsph 39,":a;bg\\' + Stage7_line[2] + '",-' + Stage7_line[3] + ',-' + Stage7_line[4] + ':vsp 39,1\n'

						line =line0 + line1 + '\nprint 1\n'
						#print(line)


					elif Stage99_line:
						#print(line)
						line0 = 'cspchar\n'

						line1 = 'lsph 39,":a;bg\\' + Stage99_line[1] + '",-' + Stage99_line[2] + ',-' + Stage99_line[3] + ':vsp 39,1\n'
						line = line0 + line1 + '\nprint 1\n'
						#print(line)

					else:
						line = line
						#print(line)

	
				#背景CG・立ち絵の処理ここまで

				elif BGM_line:

					BGMSTART =re.match(r'\.playBGM (\S*).ogg',line)
			
					if BGMSTART:

						line = 'bgm "bgm\\' + BGMSTART[1] + '.ogg" \n' 

					else:
						#BGM再生命令にファイルを指定していないときは一括でストップを掛けます
						#本来は [playBGM *]のように[*]を使いますが、例外も含めストップさせておきます
						line = 'bgmstop\n'

				elif SE_line:

					SESTART =re.match(r'\.playSE (\S*).ogg',line)

					if SESTART:
					
						line = 'dwave 1,"se\\' + SESTART[1] + '.ogg" \n'

					else:

						line = 'dwavestop 1\n'

				elif Window_line:
					#ウインドウモードの切替です。0で非表示、1で画像通り、2で全画面です 3は電話演出用
					#Screen_line変数は改行の仕方を変えるためにテストでおいています
					#0のときはメッセージごとに改行、1のときはメッセージ番号が前の番号から変わったら改行です
					
					#print(line)
					if '0' in Window_line[1]:

						line = 'setwin0\n'
						Screen_line = 5
						#print(line)

					elif '1' in Window_line[1]:

						line = 'setwin1\n'
						Screen_line = 0
						#print(line)

					elif '2' in Window_line[1]:

						line = 'setwin2\n'
						Screen_line = 1
						#print(line)

					elif '3' in Window_line[1]:
						#print(line)
						line = 'setwin1\n'
						Screen_line = 0

					else:
						line = ';' + line
						Screen_line == 9
						#print(Window_line[1])


				elif Label_line:

					#テキスト内でのラベルジャンプを担当

					if re.match(r'\.label label[0-9]',line):

						#なんかラベル名義重複回避のためにカウンタ作ってたら一つずれたので
						Labelcount2 = Labelcount - 1

						line = '*' + Label_line[1] + '_' + str(Labelcount2) + '\n'

						#print(line)
					
					else:
						line = '*' + Label_line[1] + '\n'
						#print(line)
						

				elif Include_line:
					#print(line)
					line = '*' + Include_line[1] + '\n'

				elif Shake_line:
					#未作成・dafault.txtで処理する書き方にする予定
					#7/12訂正　このままで大丈夫そう
					line = 'quake ' + Shake_line[2] + ',' + Shake_line[3] + '\n'
					
				elif Wait_line:
					
					#line.replace('\.wait','wait')  + '\\\n'
					line = 'delay ' + Wait_line[1] + '\n'
					#print(line)
					
				elif Chain_line:

					line = 'goto *' + Chain_line[1] + '\nend\n'
					#print(line)

				elif Select3_line:

					linea = '"' + Select3_line[1] + '",*' + Select3_line[2] + '_' + str(Labelcount) + ','
					lineb = '"' + Select3_line[3] + '",*' + Select3_line[4] + '_' + str(Labelcount) + ','
					linec = '"' + Select3_line[5] + '",*' + Select3_line[6] + '_' + str(Labelcount) + '\n'

					line = 'select ' + linea + lineb + linec
					Labelcount  = Labelcount + 1
					#print(Labelcount)
					
					#print(line)

				elif Select2_line:

					linea = '"' + Select2_line[1] + '",*' + Select2_line[2] + '_' + str(Labelcount) + ','
					lineb = '"' + Select2_line[3] + '",*' + Select2_line[4] + '_' + str(Labelcount) + '\n'

					line = 'select ' + linea + lineb
					Labelcount  = Labelcount + 1
					#print(Labelcount)
					#print(line)


				elif '.end' in line:

					line = ';end\n'

				elif movie_line:

					line = 'csp -1:print 1\nmovie "mov\\' + movie_line[2] + '.mpg",click\nprint 1\n'

				elif if_line:

					line = 'if %' + if_line[1] + ' ' + if_line[2] + ' ' + if_line[3] + ':goto *' + if_line[4] + '\n'

				elif Jump_line:

					line = 'goto *' + Jump_line[1] + '\n'

				elif add_line:

					
					ADDVAR = re.match(r'\.set (\S*) = (\S*) \+ (\d*)',line)
					ADD2VAR = re.match(r'\.set (\S*) = (\S*) \+ (\d*)',line)
					SETVAR = re.match(r'\.set (\S*) = (\d*)',line)

					if ADDVAR:
						line = 'add %' +ADDVAR[1] + ',' + ADDVAR[3] + '\n'
						#print(line)

					elif SETVAR:

						line = 'mov %' + SETVAR[1] + ',' + SETVAR[2] + '\n' 

						#print(line)

					else:

						line = ';' + line + '\n'



				elif mov_line:

					line = 'mov %' + mov_line[1] + ',' + mov_line[2] + '\n' 

				elif trancelate_line:

					if int(trancelate_line[3]) <= 10:
					
						line = 'delay ' + str(trancelate_line[3]) + '00\n'

					elif int(trancelate_line[3]) <= 100:
					
						line = 'delay ' + str(trancelate_line[3]) + '0\n'

					else:
						line = 'delay ' + str(trancelate_line[3]) + '\n'

				elif erojump_line:
					#print(line)

					line = 'if %eroskip == 0 gosub *'  + erojump_line[1] + '\n'

				elif eroreturn_line:
					if not values: print('Convert now…')
					line = 'return\nend\n'

				elif vscroll_line:

					line = 'delay ' + vscroll_line[1] + '\n'

				elif hscroll_line:

					line = 'delay ' + hscroll_line[1] + '\n'



				else:
					#if 'include' in line:
						#print(line)
					
					line = ';' + line + '\n'
				line = line.replace('[]　\\','click\nlookbackflush\n')
				line = line.replace('if %clearNagomi < 1:goto *label2','if %clearNagomi < 1:goto *label2_2')
				line = line.replace('if %clearYuduki < 1:goto *label2','if %clearYuduki < 1:goto *label2_2')
				line = line.replace('if %clearYuduki < 1:goto *label2','if %clearYuduki < 1:goto *label2_2')
				line = line.replace('\\v\\','\\')
				line = line.replace('mov %clearChika,1','mov %clearChika,1\ncsp -1:print 1:setwin0:goto *title')
				line = line.replace('mov %clearNagomi,1','mov %clearNagomi,1\ncsp -1:print 1:setwin0:goto *title')
				line = line.replace('mov %clearYuduki,1','mov %clearYuduki,1\ncsp -1:print 1:setwin0:goto *title')
				line = line.replace('mov %clearYuu,1','mov %clearYuu,1\ncsp -1:print 1:setwin0:goto *title')
					
			

				
				txt += line

		

	if not values: print("処理が完了しました")

	open(os.path.join(same_hierarchy,'0.txt'), 'w', errors='ignore').write(txt)

		

	
	return


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()