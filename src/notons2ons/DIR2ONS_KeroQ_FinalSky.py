#!/usr/bin/env python3
from PIL import Image
from pathlib import Path
import concurrent.futures
import subprocess as sp
import tempfile, shutil, math, wave, sys, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'ケロQ',
		'date': 19990827,
		'title': '終ノ空',
		'requiredsoft': ['DirectorCastRipper_D10'],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),

		'version': [
			'素晴らしき日々 10th Anniversary特別仕様版 付属版',
		],

		'notes': [
			'waitでの待ち時間や文字表示速度、画面遷移が原作と違う',
			'半透明で表示するはずの立ち絵が半透明にならない',
			'タイトル画面で選択したボタンが光るように変更',
			'改ページの位置が違う場面がある',
			'セーブ/ロード画面は簡略化',
			'起動時のケロQロゴ&赤背景の説明画像\n(Macromediaロゴと18歳未満は～的な文)が無い',
			'初回起動時のみ出てくる専用のタイトル画面\n(青空背景に"スタート"、"終了"のみの画面)が無い',
			'マップ移動などの繰り返し選択肢が出る場面で、\n本来出ない選択肢が出る',
			'クリアモードでのシナリオ選択時、\n個別ルートの途中から開始することができない',
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from requiredfile_locations import location
	from utils import subprocess_args

	input_dir = values['input_dir']

	DirectorCastRipper_Path = location('DirectorCastRipper_D10')
	Xtras_dir = Path(DirectorCastRipper_Path.parent / 'Xtras')
	
	#展開物パス
	dxr_list = [
		Path(input_dir / 'READY.dxr'),
		Path(input_dir / 'DATA' / 'K.dxr'),
		Path(input_dir / 'DATA' / 'MENU.dxr'),
		Path(input_dir / 'DATA' / 'S.dxr'),
		Path(input_dir / 'DATA' / 'T.dxr'),
		Path(input_dir / 'DATA' / 'Y.dxr'),
		Path(input_dir / 'DATA' / 'Z.dxr'),

		#cstは勝手に入るので記入不要っぽい
		# Path(input_dir / 'DATA' / 'CASTS' / 'AUDIO.cst'),
		# Path(input_dir / 'DATA' / 'CASTS' / 'CHARS.cst'),
		# Path(input_dir / 'DATA' / 'CASTS' / 'GENERAL.cst'),
	]

	#存在チェック
	for dxr_path in dxr_list:
		if not dxr_path.is_file(): raise FileNotFoundError('{}が見つかりません'.format(str(dxr_path.name)))

	#PyInstallerエラー回避 - https://github.com/pyinstaller/pyinstaller/wiki/Recipe-subprocess#windows-dll-loading-order
	if sys.platform == "win32":
		import ctypes
		ctypes.windll.kernel32.SetDllDirectoryA(None)

	#展開ツール環境用一時ディレクトリ作成
	with tempfile.TemporaryDirectory() as temp_dir:
		temp_dir = Path(temp_dir)

		#コピー先パス
		DirectorCastRipper_copy_Path = Path(temp_dir / 'DirectorCastRipper.exe')
		Xtras_copy_dir = Path(temp_dir / 'Xtras')

		#全部コピー
		shutil.copy(DirectorCastRipper_Path, DirectorCastRipper_copy_Path)
		shutil.copytree(Xtras_dir, Xtras_copy_dir)

		#一括展開(上記展開物パスをコマンドに引数として全部突っ込む)
		sp.run([DirectorCastRipper_copy_Path]+dxr_list, shell=True, **subprocess_args())

		#展開物移動
		Exports_Path = Path(temp_dir / 'Exports')
		shutil.move(Exports_Path, pre_converted_dir)

	return


def default_txt():
	s = ''';mode800
*define

caption "終ノ空 for ONScripter"

rmenu "セーブ",save,"ロード",load,"スキップ",skip,"タイトル",reset
savenumber 18
transmode alpha
globalon
rubyon
nsa
windowback

humanz 20
windowchip 10
maxkaisoupage 1

effect 10,10,150

defsub textclear_d
defsub setwin
defsub str2path
defsub gosub_sel
defsub ab
defsub lc
defsub nt

game
;----------------------------------------
;%156 mono
;%157 talk
;%160 [txtskip]
;%161 char
;%162 back
;%163 event
;%164 [括弧内]
;%165 sky
;%166 eye
;%167 preload
;%168 audio
;%169 [次回audio - 0初期/1BGM/2SE]
;$185 現在dir
;$186 現在bgm
;----------------------------------------
*str2path
getparam $191
;<<-img_if_txt->>
return
;----------------------------------------
*setwin
	getparam %180
	if %180==0 setwindow  85, 70,24,8,24,24,2,5,1,0,1,#666666,0,0             ,799,599
	if %180==1 setwindow 160,490,24,2,24,24,0,5,1,0,1,"Exports/GENERAL/91.png", 23,483

	if %180==9 setwindow  85, 99,24,8,24,24,2,5,1,0,1,#666666,0,0             ,799,599
return
;----------------------------------------
*lc
	;line_check - 関数名短くしたほうが変換時txt容量小さくなるのでlc
	getparam $170

	if $170=="{" mov %164,1:return
	if $170=="}" mov %164,0:print 10:return

	if %167==1 return
	if %168==1 gosub *audio_setting:return
	if %196==1 gosub *select_setting:return
	
	if %161==1 if $170!="+" if $170!="-" if $170!="+-" str2path $170:lsp 25,$195,0,0:csp 24:gosub *print_nokakko:return
	if %161==1 if $170=="+" return
	if %161==1 if $170=="-" csp 25:gosub *print_nokakko:return
	if %161==1 if $170=="+-" csp 25:gosub *print_nokakko:return
	
	if %162==1 if $170!="+" if $170!="-" if $170!="+-" str2path $170:lsp 26,$195,24,40:gosub *print_nokakko:return
	if %162==1 if $170=="+" return
	if %162==1 if $170=="-" csp 26:gosub *print_nokakko:return
	if %162==1 if $170=="+-" csp 26:gosub *print_nokakko:return
	
	if %163==1 if $170!="+" if $170!="-" if $170!="+-" if $170!="*-" if $170!="--" if $170!="*" str2path $170:lsp 24,$195,0,0:gosub *print_nokakko:return
	if %163==1 if $170=="+" return
	if %163==1 if $170=="*" return
	if %163==1 if $170=="*-" return
	if %163==1 if $170=="--" csp 24:gosub *print_nokakko:return
	if %163==1 if $170=="-" csp 24:gosub *print_nokakko:return
	if %163==1 if $170=="+-" csp 24:gosub *print_nokakko:return
	
	if %165==1 if $170=="+" lsp 29,"Exports/GENERAL/121.png",0,0:gosub *print_nokakko:return
	if %165==1 if $170=="-" csp 29:gosub *print_nokakko:return

	if %166==1 if $170!="+" if $170!="-" str2path "目"+$170:lsp 28,$195,0,0:gosub *print_nokakko:return
	if %166==1 if $170=="-" csp 28:gosub *print_nokakko:return

	if %156==1 if %157==0 ab $170:return
	if %156==0 if %157==1 nt $170:return

	*err_loop
	＜ＯＮＳコンバータ不具合＞このメッセージは　みえないはずだよ　みえたらおしえてね\\
	goto *err_loop
return

*audio_setting
	if $170=="L+" mov %169,1:return
	if $170=="S" mov %169,2:return
	if $170=="L-" bgmstop:mov %169,0:return
	if $170=="L--" bgmstop:mov %169,0:return
	if $170=="L0" bgmstop:mov %169,0:return
	if $170=="S0" dwavestop 1:mov %169,0:return

	;どれでもない→文字列
	str2path $170
	;bgmは今流れてるのと違うやつのときのみ作動
	if %169==1 if $186!=$195 bgm $195 mov $186,$195
	if %169==2 dwave 1,$195
	mov %169,0
	resettimer
return

*select_setting
	if %197==0 mov $90,$170:inc %197:return
	if %197==1 mov $91,$170:inc %197:return
	if %197==2 mov $92,$170:inc %197:return
	if %197==3 mov $93,$170:inc %197:return
	if %197==4 mov $94,$170:inc %197:return
	if %197==5 mov $95,$170:inc %197:return
	
*print_nokakko
	;スクリプト側が括弧内ではないときはprint10する
	;括弧内のときは(括弧出たタイミングで一括print10なので)何もしない
	if %164==0 print 10
return
;----------------------------------------
*ab
	;auto_break_line - 関数名短くしたほうが変換時txt容量小さくなるのでab
	;文字/数字 150~159までを使ってます
	getparam $150
	
	mov %158,24		;一行に表示する文字数
	mov %159,9		;この行数まで到達したらor超えそうになったら改ページ

	;文字スキップ
	if %160==0 mov $151,"@":mov $154,"\\"
	if %160!=0 mov $151,"":mov $154,""

	;文字列の長さを代入→なぜか倍の数字出るので÷2
	len %150,$150
	div %150,2

	;使用行数を代入するため取得文字数を一行に表示する文字数で割る
	mov %151,%150/%158

	;上記"/"は切り捨てのため余りがある(割り切れてない)場合はもう一行分追加
	mov %152,%150 mod %158
	if %152!=0 add %151,1

	;使用行数をカウントへ代入
	add %153,%151

	;カウントが超えた場合goto
	if %153=%159 goto *brline_max1
	if %153>%159 if $151=="" goto *brline_max2
	if %153>%159 if $151!="" goto *brline_max3

	;通常時
	$150$151
return

;カウントちょうどMAX時飛び先
*brline_max1
	$150$154
	if %160!=0 textclear
	mov %153,0
return

;カウントMAX超え時飛び先
*brline_max2
	$154
	if %160!=0 textclear
*brline_max3
	mov %153,%151
	textclear
	$150$151
return
;----------------------------------------
*textclear_d
	mov %153,0
	textclear
return
;----------------------------------------
*nt
	;normal_talk
	getparam $150

	;ab用カウントリセット
	mov %153,0
	
	;文字列$150の8(=全角4)文字目から2(=全角1)文字分の部分文字列を$151に切り出す→"「"なら発言
	mid $151,$150,8,2
	if $151=="「" goto *ntline1
	if $151!="「" goto *ntline2

*ntline1
	;発言
	mid $152,$150,0,8
	mid $153,$150,10,99
	
	lsp 10,":s/24,24,0;#ffffff"+$152,64,495
	「$153\\
	
	saveon
return

*ntline2
	;非発言
	mov $152,""
	lsp 10,":s/24,24,0;#ffffff"+$152,64,495
	$150\\
	saveon
return
;----------------------------------------
*gosub_sel
	getparam $196
	mov %196,1
	mov %197,0
	mov %198,0
	setwin 9

	gosub $196

	;ここに$90表示いれる
	lsp 11,":s/24,24,0;#ffffff"+$90,85,70
	print 1

	select $91,*gosel1,
	       $92,*gosel2,
	       $93,*gosel3,
	       $94,*gosel4,
	       $95,*gosel5

*gosel1
	mov %198,1:goto *goselend
*gosel2
	mov %198,2:goto *goselend
*gosel3
	mov %198,3:goto *goselend
*gosel4
	mov %198,4:goto *goselend
*gosel5
	mov %198,5:goto *goselend

*goselend
	mov %196,0
	mov %197,0

	mov $90,"":mov $91,"":mov $92,"":mov $93,"":mov $94,"":mov $95,""
	csp 11:print 1
return
;----------------------------------------
*start
;;;原作だと選んだ選択肢消えてくんだけどめんどいので放置
;%250 panty[1] or no[2]
;%251 ayana[1] or kotomi[2]

;;;debug フラグ
;mov %200,5
;mov %214,1
;mov %250,1
;mov %251,2

;ロード画面表示→文字スプライト読み込み→即削除 - 低スペック機でビットマップフォントを使った際ここで長めのロードが入る
bg "Exports/READY/2.png",1
lsph 10,":s/24,24,0;#ffffffてすと",1000,1000:csp 10:print 10
bg black,1

;背景 - 進度に応じて変更
if %200==0 bg "Exports/MENU/11.png",10:goto *title_bg_end
if %200==1 bg "Exports/MENU/12.png",10:goto *title_bg_end
if %200==2 bg "Exports/MENU/13.png",10:goto *title_bg_end
if %200==3 bg "Exports/MENU/14.png",10:goto *title_bg_end
if %200==4 bg "Exports/MENU/15.png",10:goto *title_bg_end
if %200==5 bg "Exports/MENU/15.png",10:goto *title_bg_end
*title_bg_end

bgm "Exports/AUDIO/11.wav"

if %200==0 lsp 70,"Exports/MENU/22.png",564,344
if %200==1 lsp 71,"Exports/MENU/23.png",564,344
if %200==2 lsp 72,"Exports/MENU/24.png",564,344
if %200==3 lsp 73,"Exports/MENU/25.png",564,344
if %200==4 lsp 74,"Exports/MENU/26.png",564,344
lsp 81,"Exports/MENU/31.png",564,432
lsp 82,"Exports/MENU/41.png",564,520
if %214==1 lsp 83,"Exports/MENU/62.png",10,10

if %200==0 lsp 50,"Exports/MENU/22_btn.png",564,344
if %200==1 lsp 51,"Exports/MENU/23_btn.png",564,344
if %200==2 lsp 52,"Exports/MENU/24_btn.png",564,344
if %200==3 lsp 53,"Exports/MENU/25_btn.png",564,344
if %200==4 lsp 54,"Exports/MENU/26_btn.png",564,344
lsp 61,"Exports/MENU/31_btn.png",564,432
lsp 62,"Exports/MENU/41_btn.png",564,520
if %214==1 lsp 63,"Exports/MENU/62_btn.png",10,10
print 1

*title_loop
	bclear
	btrans

	exbtn_d     "C50C51C52C53C54C61C62C63"
	exbtn 50,50,"P50C51C52C53C54C61C62C63"
	exbtn 51,51,"C50P51C52C53C54C61C62C63"
	exbtn 52,52,"C50C51P52C53C54C61C62C63"
	exbtn 53,53,"C50C51C52P53C54C61C62C63"
	exbtn 54,54,"C50C51C52C53P54C61C62C63"
	exbtn 61,61,"C50C51C52C53C54P61C62C63"
	exbtn 62,62,"C50C51C52C53C54C61P62C63"
	exbtn 63,63,"C50C51C52C53C54C61C62P63"

	btnwait %0

	if %0==50 csp -1:bg black,10:bgmstop:goto *root_y
	if %0==51 csp -1:bg black,10:bgmstop:goto *root_k
	if %0==52 csp -1:bg black,10:bgmstop:goto *root_z
	if %0==53 csp -1:bg black,10:bgmstop:goto *root_t
	if %0==54 csp -1:bg black,10:bgmstop:goto *root_s
	if %0==61 csp -1:bg black,10:bgmstop:systemcall load:reset
	if %0==62 csp -1:bg black,10:bgmstop:end
	if %0==63 csp -1:bg black,10:bgmstop:goto *clear_mode
goto *title_loop
;----------------------------------------
;;;;; クリアモード ;;;;;
*clear_mode

lsp 50,"Exports/MENU/64.png",10,10
lsp 51,":s/24,24,0;#666666#ffffff彩名モード",250,100
lsp 52,":s/24,24,0;#666666#ffffff琴美モード",400,100
lsp 53,":s/24,24,0;#666666#ffffff見てない",250,130
lsp 54,":s/24,24,0;#666666#ffffff見た",400,130

lsph 56,":s/24,24,0;#ffffff●"   ,225,100
lsph 57,":s/24,24,0;#ffffff●"   ,375,100
lsph 58,":s/24,24,0;#ffffff●"   ,225,130
lsph 59,":s/24,24,0;#ffffff●"   ,375,130

lsp 60,":s/24,24,0;#666666#ffffffＹ１３"      ,250,200
lsp 61,":s/24,24,0;#666666#ffffffＫ１２"      ,250,230
lsp 62,":s/24,24,0;#666666#ffffffＺ０９"      ,250,260
lsp 63,":s/24,24,0;#666666#ffffffＴ１３"      ,250,290
lsp 64,":s/24,24,0;#666666#ffffffそれ以降"      ,250,320

lsp 100,":s/24,24,0;#ffffff＃ｍｏｄｅ："   ,10,100
lsp 101,":s/24,24,0;#ffffff＃ｐａｎｔｙ：" ,10,130

lsp 110,":s/24,24,0;#ffffffはじめから："   ,10,200
lsp 111,":s/24,24,0;#ffffff琴美の場合："   ,10,230
lsp 112,":s/24,24,0;#ffffffざくろの場合：" ,10,260
lsp 113,":s/24,24,0;#ffffff卓司の場合："   ,10,290
lsp 114,":s/24,24,0;#ffffffそれ以降："     ,10,320
print 1

*cm_loop
	;●
	if %251==1 vsp 56,1
	if %251==2 vsp 57,1
	if %250==2 vsp 58,1
	if %250==1 vsp 59,1
	if %251!=1 vsp 56,0
	if %251!=2 vsp 57,0
	if %250!=2 vsp 58,0
	if %250!=1 vsp 59,0

	bclear

	spbtn 50,50
	spbtn 51,51
	spbtn 52,52
	spbtn 53,53
	spbtn 54,54
	spbtn 60,60
	spbtn 61,61
	spbtn 62,62
	spbtn 63,63
	spbtn 64,64

	btnwait %0
	if %0==50 csp -1:reset
	if %0==51 mov %251,1
	if %0==52 mov %251,2
	if %0==53 mov %250,2
	if %0==54 mov %250,1
	if %0==60 csp -1:bg black,10:bgmstop:goto *root_y
	if %0==61 csp -1:bg black,10:bgmstop:goto *root_k
	if %0==62 csp -1:bg black,10:bgmstop:goto *root_z
	if %0==63 csp -1:bg black,10:bgmstop:goto *root_t
	if %0==64 csp -1:bg black,10:bgmstop:goto *root_s
goto *cm_loop
;----------------------------------------
;;;;; 行人ルート ;;;;;
*root_y

;おとぎ話をしてあげよう～視点 のとこ
wait 1000
lsp 24,"Exports/Y/11.png",0,0:print 10:wait 1500
lsp 24,"Exports/Y/12.png",0,0:print 10:wait 1500
lsp 24,"Exports/Y/13.png",0,0:print 10:wait 1500
lsp 24,"Exports/Y/14.png",0,0:print 10:wait 3000
csp 24:print 10
lsp 24,"Exports/Y/21.png",0,0:print 10:wait 3000
csp 24:print 10

;開始前暗転&背景空設置
mov %161,1:lc "black":mov %161,0
lsp 29,"Exports/GENERAL/121.png",0,0:gosub *print_nokakko

;本編
gosub *SCR_Y_31_txt:gosub *SCR_Y_41_txt
gosub_sel *SCR_Y_52_txt
if %198==1 gosub *SCR_Y_54_txt:mov %250,1:gosub *SCR_Y_55_txt
if %198==2 gosub *SCR_Y_56_txt:mov %250,2:gosub *SCR_Y_57_txt
gosub *SCR_Y_61_txt:gosub *SCR_Y_62_txt:gosub *SCR_Y_63_txt:gosub *SCR_Y_64_txt:gosub *SCR_Y_65_txt:gosub *SCR_Y_66_txt
*jump01
gosub_sel *SCR_Y_72_txt
if %198==1 if %60==0           gosub *SCR_Y_74_txt:mov %60,1:goto *jump01
if %198==1 if %60==1           gosub *SCR_Y_75_txt          :goto *jump01
if %198==2 if %61==0           gosub *SCR_Y_77_txt          :goto *jump01
if %198==2 if %61==1           gosub *SCR_Y_76_txt:mov %62,1:goto *jump01
if %198==3                     gosub *SCR_Y_78_txt          :goto *jump01
if %198==4 if %60==1 if %62==1 gosub *SCR_Y_84_txt          :goto *jump02
if %198==4 if %63==0           gosub *SCR_Y_79_txt:mov %63,1:goto *jump01
if %198==4 if %63==1           gosub *SCR_Y_80_txt          :goto *jump01
if %198==5 if %61==0           gosub *SCR_Y_81_txt:mov %61,1:goto *jump01
if %198==5 if %61==1           gosub *SCR_Y_82_txt          :goto *jump01
end
*jump02
if %250==1 gosub *SCR_Y_91_txt
gosub *SCR_Y_92_txt:gosub *SCR_Y_93_txt:gosub *SCR_Y_94_txt
*jump03
if %64==1 if %65==1 if %66==1 if %67==1 goto *jump04
gosub_sel *SCR_Y_102_txt
if %198==1 gosub *SCR_Y_104_txt:mov %64,1:goto *jump03
if %198==2 gosub *SCR_Y_105_txt:mov %65,1:goto *jump03
if %198==3 gosub *SCR_Y_106_txt:mov %66,1:goto *jump03
if %198==4 gosub *SCR_Y_107_txt:mov %67,1:goto *jump03
end
*jump04
gosub *SCR_Y_109_txt:gosub *SCR_Y_121_txt:gosub *SCR_Y_131_txt:gosub *SCR_Y_132_txt:gosub *SCR_Y_133_txt:gosub *SCR_Y_134_txt
*jump05
if %68==1 if %72==1 goto *jump07
gosub_sel *SCR_Y_142_txt
if %198==1 if %68==0 if %69==0 goto *jump06
if %198==1 if %68==1 if %69==0 gosub *SCR_Y_150_txt          :goto *jump05
if %198==1 if %68==1           gosub *SCR_Y_151_txt          :goto *jump05
if %198==2 if %71==1 if %72==0 gosub *SCR_Y_152_txt:mov %72,1:goto *jump05
if %198==2                     gosub *SCR_Y_153_txt          :goto *jump05
if %198==3 if %70==1 if %71==0 gosub *SCR_Y_154_txt:mov %71,1:goto *jump05
if %198==3                     gosub *SCR_Y_155_txt          :goto *jump05
if %198==4 if %73==0           gosub *SCR_Y_156_txt:mov %73,1:goto *jump05
if %198==4                     gosub *SCR_Y_157_txt          :goto *jump05
if %198==5 if %70==0           gosub *SCR_Y_158_txt:mov %70,1:goto *jump05
if %198==5                     gosub *SCR_Y_159_txt          :goto *jump05
end
*jump06
mov %68,1:gosub *SCR_Y_144_txt
gosub_sel *SCR_Y_146_txt
if %198==1 gosub *SCR_Y_148_txt          :goto *jump05
if %198==2 gosub *SCR_Y_149_txt:mov %69,1:goto *jump05
end
*jump07
gosub *SCR_Y_161_txt:gosub *SCR_Y_171_txt:gosub *SCR_Y_172_txt:gosub *SCR_Y_173_txt:gosub *SCR_Y_191_txt:gosub *SCR_Y_201_txt
gosub *SCR_Y_202_txt:gosub *SCR_Y_203_txt:gosub *SCR_Y_204_txt:gosub *SCR_Y_205_txt:gosub *SCR_Y_206_txt:gosub *SCR_Y_207_txt
gosub_sel *SCR_Y_212_txt
if %198==1 mov %251,1:gosub *SCR_Y_214_txt
if %198==2 mov %251,2:gosub *SCR_Y_215_txt
gosub *SCR_Y_217_txt
*jump08
gosub_sel *SCR_Y_222_txt
if %198==1 gosub *SCR_Y_224_txt:goto *jump08
if %198==2 gosub *SCR_Y_225_txt:goto *jump08
if %198==3 gosub *SCR_Y_229_txt:goto *jump09
if %198==4 gosub *SCR_Y_226_txt:goto *jump08
if %198==5 gosub *SCR_Y_227_txt:goto *jump08
end
*jump09
gosub *SCR_Y_231_txt:gosub *SCR_Y_251_txt:gosub *SCR_Y_261_txt:gosub *SCR_Y_262_txt:gosub *SCR_Y_263_txt:gosub *SCR_Y_264_txt
*jump10
gosub_sel *SCR_Y_272_txt
if %198==1 if %74==0                      gosub *SCR_Y_274_txt:mov %74,1:goto *jump10
if %198==1                                gosub *SCR_Y_275_txt:          goto *jump10
if %198==2                                gosub *SCR_Y_276_txt:          goto *jump10
if %198==3 if %76==1                      gosub *SCR_Y_284_txt:          goto *jump11
if %198==3                                gosub *SCR_Y_277_txt:          goto *jump10
if %198==4 if %75==0 if %251==1           gosub *SCR_Y_278_txt:mov %75,1:goto *jump10
if %198==4 if %75==0 if %251==2           gosub *SCR_Y_279_txt:mov %75,1:goto *jump10
if %198==4 if %74==1 if %75==1  if %76==0 gosub *SCR_Y_280_txt:mov %76,1:goto *jump10
if %198==4                                gosub *SCR_Y_281_txt:          goto *jump10
if %198==5                                gosub *SCR_Y_282_txt:          goto *jump10
end
*jump11
gosub *SCR_Y_291_txt
if %251==2 goto *jump24
gosub *SCR_Y_292_txt
gosub_sel *SCR_Y_294_txt
if %198==1 gosub *SCR_Y_296_txt:goto *jump24
if %198==2 gosub *SCR_Y_297_txt:goto *jump24
*jump24
gosub *SCR_Y_301_txt:gosub *SCR_Y_302_txt:gosub *SCR_Y_321_txt:gosub *SCR_Y_331_txt:gosub *SCR_Y_332_txt:gosub *SCR_Y_333_txt
gosub *SCR_Y_334_txt:gosub *SCR_Y_335_txt:gosub *SCR_Y_351_txt
*jump12
gosub_sel *SCR_Y_342_txt
if %198==1 gosub *SCR_Y_353_txt:goto *jump12
if %198==2 gosub *SCR_Y_355_txt:goto *jump13
end
*jump13
gosub *SCR_Y_361_txt
*jump14
gosub_sel *SCR_Y_342_txt
if %198==1 gosub *SCR_Y_365_txt:goto *jump15
if %198==2 gosub *SCR_Y_363_txt:goto *jump14
end
*jump15
gosub *SCR_Y_371_txt
*jump16
gosub_sel *SCR_Y_342_txt
if %198==1 gosub *SCR_Y_373_txt:goto *jump16
if %198==2 gosub *SCR_Y_375_txt:goto *jump17
end
*jump17
gosub *SCR_Y_391_txt:gosub *SCR_Y_401_txt:gosub *SCR_Y_402_txt:gosub *SCR_Y_403_txt
*jump18
gosub_sel *SCR_Y_412_txt
if %198==1 gosub *SCR_Y_414_txt:goto *jump19
if %198==2 gosub *SCR_Y_415_txt:goto *jump18
end
*jump19
gosub *SCR_Y_417_txt:gosub *SCR_Y_421_txt
*jump20
gosub_sel *SCR_Y_432_txt
if %198==1 gosub *SCR_Y_434_txt:goto *jump20
if %198==2 gosub *SCR_Y_435_txt:goto *jump20
if %198==3 gosub *SCR_Y_437_txt:goto *jump21
end
*jump21
gosub *SCR_Y_441_txt:gosub *SCR_Y_442_txt:gosub *SCR_Y_451_txt
if %251==1 goto *jump25
gosub *SCR_Y_452_txt:gosub *SCR_Y_453_txt:gosub *SCR_Y_454_txt:gosub *SCR_Y_455_txt
*jump25
gosub *SCR_Y_461_txt:gosub *SCR_Y_462_txt:gosub *SCR_Y_463_txt:gosub *SCR_Y_481_txt
if %251==2 goto *jump26
gosub *SCR_Y_491_txt:gosub *SCR_Y_492_txt:gosub *SCR_Y_493_txt:gosub *SCR_Y_494_txt:gosub *SCR_Y_495_txt:gosub *SCR_Y_496_txt
goto *jump27
*jump26
gosub *SCR_Y_501_txt:gosub *SCR_Y_502_txt:gosub *SCR_Y_503_txt:gosub *SCR_Y_504_txt:gosub *SCR_Y_505_txt
*jump22
gosub_sel *SCR_Y_512_txt
if %198==1 gosub *SCR_Y_514_txt:goto *jump22
if %198==2 gosub *SCR_Y_517_txt:goto *jump23
end
*jump23
gosub *SCR_Y_521_txt
*jump27
gosub *SCR_Y_531_txt:gosub *SCR_Y_551_txt:gosub *SCR_Y_561_txt

;ここに時計11:59
dwaveloop 1,"Exports/AUDIO/55.wav":resettimer
lsp 24,"Exports/Y/581.png",0,0:print 1
waittimer 4000
dwavestop 1:csp -1:print 1
wait 1000

;yukitoEND
bgm "Exports/AUDIO/11.wav"
lsp 24,"Exports/Y/591.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/592.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/593.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/594.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/595.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/596.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/597.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/598.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/599.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/600.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/601.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/602.png",0,0:print 10:wait 3800
lsp 24,"Exports/Y/603.png",0,0:print 10:wait 3800
csp 24:print 10
bgmstop
wait 500

mov %200,1:mov %210,1
reset
;----------------------------------------
;;;;; 琴美ルート ;;;;;
*root_k

;視点
lsp 24,"Exports/K/11.png",0,0:print 10:wait 3000
csp 24:print 10

;開始前暗転&背景空設置
mov %161,1:lc "black":mov %161,0
lsp 29,"Exports/GENERAL/121.png",0,0:gosub *print_nokakko

;本編
gosub *SCR_K_21_txt:gosub *SCR_K_31_txt:gosub *SCR_K_32_txt:gosub *SCR_K_33_txt
gosub *SCR_K_34_txt:gosub *SCR_K_35_txt:gosub *SCR_K_36_txt
*jump28
gosub_sel *SCR_K_42_txt
if %198==1           gosub *SCR_K_44_txt          :goto *jump28
if %198==2 if %77==0 gosub *SCR_K_45_txt:mov %77,1:goto *jump28
if %198==2           gosub *SCR_K_46_txt          :goto *jump28
if %198==3 if %77==0 gosub *SCR_K_47_txt          :goto *jump28
if %198==3           gosub *SCR_K_51_txt          :goto *jump29
if %198==4           gosub *SCR_K_48_txt          :goto *jump28
if %198==5           gosub *SCR_K_49_txt          :goto *jump28
end
*jump29
gosub *SCR_K_61_txt:gosub *SCR_K_62_txt:gosub *SCR_K_63_txt:gosub *SCR_K_81_txt:gosub *SCR_K_91_txt:gosub *SCR_K_92_txt
if %250==2 gosub *SCR_K_103_txt:gosub *SCR_K_104_txt
if %250==1 gosub *SCR_K_101_txt:gosub *SCR_K_102_txt
gosub *SCR_K_111_txt:gosub *SCR_K_112_txt:gosub *SCR_K_113_txt:gosub *SCR_K_114_txt:gosub *SCR_K_115_txt:gosub *SCR_K_116_txt
gosub *SCR_K_117_txt:gosub *SCR_K_118_txt:gosub *SCR_K_119_txt
if %250==1 gosub *SCR_K_121_txt:gosub *SCR_K_122_txt
gosub *SCR_K_123_txt:gosub *SCR_K_124_txt:gosub *SCR_K_141_txt:gosub *SCR_K_151_txt:gosub *SCR_K_152_txt:gosub *SCR_K_153_txt
gosub *SCR_K_154_txt:gosub *SCR_K_155_txt:gosub *SCR_K_156_txt:gosub *SCR_K_157_txt:gosub *SCR_K_158_txt:gosub *SCR_K_159_txt
gosub *SCR_K_171_txt:gosub *SCR_K_181_txt:gosub *SCR_K_182_txt:gosub *SCR_K_183_txt:gosub *SCR_K_184_txt:gosub *SCR_K_185_txt
gosub *SCR_K_191_txt
if %251==1 gosub *SCR_K_192_txt
if %251==2 gosub *SCR_K_193_txt:gosub *SCR_K_194_txt
gosub *SCR_K_201_txt:gosub *SCR_K_202_txt:gosub *SCR_K_221_txt:gosub *SCR_K_231_txt:gosub *SCR_K_232_txt:gosub *SCR_K_233_txt
gosub *SCR_K_234_txt:gosub *SCR_K_235_txt:gosub *SCR_K_236_txt:gosub *SCR_K_237_txt
if %251==1 gosub *SCR_K_241_txt
if %251==2 gosub *SCR_K_242_txt
gosub *SCR_K_251_txt:gosub *SCR_K_291_txt:gosub *SCR_K_292_txt
if %251==1 gosub *SCR_K_301_txt:gosub *SCR_K_302_txt:gosub *SCR_K_303_txt
if %251==1 gosub *SCR_K_304_txt:gosub *SCR_K_305_txt
if %251==2 gosub *SCR_K_311_txt:gosub *SCR_K_312_txt:gosub *SCR_K_313_txt:gosub *SCR_K_314_txt
if %251==2 gosub *SCR_K_315_txt:gosub *SCR_K_316_txt:gosub *SCR_K_317_txt
gosub *SCR_K_331_txt:gosub *SCR_K_332_txt
bgmstop:csp -1:print 10
wait 1000

;kotomiEND
bgm "Exports/AUDIO/11.wav"
lsp 24,"Exports/K/351.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/352.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/353.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/354.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/355.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/356.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/357.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/358.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/359.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/360.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/361.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/362.png",0,0:print 10:wait 3800
lsp 24,"Exports/K/363.png",0,0:print 10:wait 3800
csp 24:print 10
bgmstop
wait 500

mov %200,2:mov %211,1
reset
;----------------------------------------
;;;;; ざくろルート ;;;;;
*root_z

;視点
lsp 24,"Exports/Z/11.png",0,0:print 10:wait 3000
csp 24:print 10

;開始前暗転&背景空設置
mov %161,1:lc "black":mov %161,0
lsp 29,"Exports/GENERAL/121.png",0,0:gosub *print_nokakko

;本編
gosub *SCR_Z_21_txt:gosub *SCR_Z_31_txt:gosub *SCR_Z_32_txt:gosub *SCR_Z_33_txt:gosub *SCR_Z_34_txt:gosub *SCR_Z_35_txt
gosub *SCR_Z_36_txt:gosub *SCR_Z_51_txt:gosub *SCR_Z_61_txt:gosub *SCR_Z_62_txt:gosub *SCR_Z_63_txt:gosub *SCR_Z_81_txt
gosub *SCR_Z_91_txt:gosub *SCR_Z_92_txt:gosub *SCR_Z_93_txt:gosub *SCR_Z_94_txt:gosub *SCR_Z_95_txt:gosub *SCR_Z_111_txt
gosub *SCR_Z_121_txt:gosub *SCR_Z_122_txt
*jump30
gosub_sel *SCR_Z_132_txt
if %198==1 if %78==1 if %79==1 if %80==1           :goto *jump31
if %198==1           gosub *SCR_Z_134_txt          :goto *jump30
if %198==2 if %78==0 gosub *SCR_Z_135_txt:mov %78,1:goto *jump30
if %198==2           gosub *SCR_Z_136_txt          :goto *jump30
if %198==3           gosub *SCR_Z_137_txt          :goto *jump30
if %198==4 if %79==0 gosub *SCR_Z_138_txt:mov %79,1:goto *jump30
if %198==4           gosub *SCR_Z_139_txt          :goto *jump30
if %198==5 if %80==0 gosub *SCR_Z_140_txt:mov %80,1:goto *jump30
if %198==5           gosub *SCR_Z_141_txt          :goto *jump30
end
*jump31
gosub *SCR_Z_143_txt
bgmstop:csp -1:print 10
wait 1000

;zakuroEND
bgm "Exports/AUDIO/11.wav"
lsp 24,"Exports/Z/171.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/172.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/173.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/174.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/175.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/176.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/177.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/178.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/179.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/180.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/181.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/182.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/183.png",0,0:print 10:wait 3800
lsp 24,"Exports/Z/184.png",0,0:print 10:wait 3800
csp 24:print 10
bgmstop
wait 500


mov %200,3:mov %212,1
reset
;----------------------------------------
;;;;; 卓司ルート ;;;;;
*root_t

;視点
lsp 24,"Exports/T/11.png",0,0:print 10:wait 3000
csp 24:print 10

;開始前暗転&背景空設置
mov %161,1:lc "black":mov %161,0
lsp 29,"Exports/GENERAL/121.png",0,0:gosub *print_nokakko

;本編
gosub *SCR_T_21_txt:gosub *SCR_T_41_txt:gosub *SCR_T_42_txt:gosub *SCR_T_43_txt
*jump32
gosub_sel *SCR_T_52_txt
if %198==1 if %81==1 gosub *SCR_T_60_txt          :goto *jump33
if %198==1           gosub *SCR_T_54_txt          :goto *jump32
if %198==2 if %81==0 gosub *SCR_T_55_txt:mov %81,1:goto *jump32
if %198==2           gosub *SCR_T_56_txt          :goto *jump32
if %198==3           gosub *SCR_T_57_txt          :goto *jump32
if %198==4           gosub *SCR_T_58_txt          :goto *jump32
end
*jump33
gosub *SCR_T_61_txt:gosub *SCR_T_62_txt:gosub *SCR_T_63_txt:gosub *SCR_T_64_txt:gosub *SCR_T_81_txt:gosub *SCR_T_91_txt
gosub *SCR_T_92_txt:gosub *SCR_T_93_txt:gosub *SCR_T_94_txt
*jump34
gosub_sel *SCR_T_102_txt
if %198==1 if %82==1 if %85==1 gosub *SCR_T_114_txt          :goto *jump35
if %198==1                     gosub *SCR_T_104_txt          :goto *jump34
if %198==2 if %85==0 if %84==1 gosub *SCR_T_105_txt:mov %85,1:goto *jump34
if %198==2                     gosub *SCR_T_106_txt          :goto *jump34
if %198==3 if %84==0 if %83==1 gosub *SCR_T_107_txt:mov %84,1:goto *jump34
if %198==3                     gosub *SCR_T_108_txt          :goto *jump34
if %198==4 if %82==0           gosub *SCR_T_109_txt:mov %82,1:goto *jump34
if %198==4                     gosub *SCR_T_110_txt          :goto *jump34
if %198==5 if %83==0           gosub *SCR_T_111_txt:mov %83,1:goto *jump34
if %198==5                     gosub *SCR_T_112_txt          :goto *jump34
end
*jump35
gosub *SCR_T_121_txt:gosub *SCR_T_141_txt:gosub *SCR_T_161_txt:gosub *SCR_T_162_txt:gosub *SCR_T_163_txt:gosub *SCR_T_164_txt
gosub *SCR_T_165_txt:gosub *SCR_T_166_txt:gosub *SCR_T_167_txt:gosub *SCR_T_171_txt:gosub *SCR_T_172_txt:gosub *SCR_T_173_txt
gosub *SCR_T_174_txt:gosub *SCR_T_175_txt:gosub *SCR_T_176_txt:gosub *SCR_T_177_txt:gosub *SCR_T_191_txt:gosub *SCR_T_221_txt
gosub *SCR_T_222_txt:gosub *SCR_T_223_txt:gosub *SCR_T_231_txt:gosub *SCR_T_232_txt:gosub *SCR_T_233_txt:gosub *SCR_T_234_txt
gosub *SCR_T_235_txt:gosub *SCR_T_236_txt:gosub *SCR_T_237_txt:gosub *SCR_T_241_txt:gosub *SCR_T_242_txt:gosub *SCR_T_243_txt
gosub *SCR_T_244_txt:gosub *SCR_T_251_txt:gosub *SCR_T_271_txt:gosub *SCR_T_281_txt:gosub *SCR_T_291_txt:gosub *SCR_T_292_txt
gosub *SCR_T_293_txt:gosub *SCR_T_294_txt:gosub *SCR_T_295_txt:gosub *SCR_T_311_txt:gosub *SCR_T_321_txt:gosub *SCR_T_322_txt
gosub *SCR_T_323_txt:gosub *SCR_T_331_txt:gosub *SCR_T_332_txt:gosub *SCR_T_333_txt:gosub *SCR_T_351_txt:gosub *SCR_T_361_txt
gosub *SCR_T_362_txt
bgmstop:csp -1:print 10
wait 1000

;takujiEND
bgm "Exports/AUDIO/11.wav"
lsp 24,"Exports/T/391.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/392.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/393.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/394.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/395.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/396.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/397.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/398.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/399.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/400.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/401.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/402.png",0,0:print 10:wait 3800
lsp 24,"Exports/T/403.png",0,0:print 10:wait 3800
csp 24:print 10
bgmstop
wait 500

mov %200,4:mov %213,1
reset
;----------------------------------------
;;;;; それ以降 ;;;;;
*root_s

;そして
lsp 24,"Exports/S/11.png",0,0:print 10:wait 3000
csp 24:print 10

;開始前暗転&背景空設置
mov %161,1:lc "black":mov %161,0
lsp 29,"Exports/GENERAL/121.png",0,0:gosub *print_nokakko

;本編
if %251==1 gosub *SCR_S_31_txt:gosub *SCR_S_32_txt:gosub *SCR_S_33_txt:gosub *SCR_S_34_txt:gosub *SCR_S_35_txt
if %251==1 gosub *SCR_S_36_txt:gosub *SCR_S_37_txt:gosub *SCR_S_41_txt:gosub *SCR_S_42_txt:gosub *SCR_S_43_txt
if %251==1 gosub *SCR_S_44_txt:gosub *SCR_S_51_txt
if %251==2 gosub *SCR_S_71_txt:gosub *SCR_S_72_txt:gosub *SCR_S_73_txt
if %251==2 gosub *SCR_S_74_txt:gosub *SCR_S_75_txt:gosub *SCR_S_76_txt
bgmstop:csp -1:print 10
wait 1000

;この作品をすべての呪われた生と～
lsp 24,"Exports/S/91.png",0,0:print 10:wait 3000
lsp 24,"Exports/S/92.png",0,0:print 10:wait 3000
lsp 24,"Exports/S/93.png",0,0:print 10:wait 3000
lsp 24,"Exports/S/94.png",0,0:print 10:wait 3000
csp 24:print 10
wait 500

;soreikouEND
bgm "Exports/AUDIO/11.wav"
lsp 24,"Exports/S/111.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/112.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/113.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/114.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/115.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/116.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/117.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/118.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/119.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/120.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/121.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/122.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/123.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/124.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/125.png",0,0:print 10:wait 3800
lsp 24,"Exports/S/126.png",0,0:print 10:wait 3800
csp 24:print 10
bgmstop
wait 500


mov %200,5:mov %214,1
reset
;----------------------------------------
'''
	return s
#--------------------def--------------------
# ディレクトリの存在チェック関数
def dir_check(path_list):

	CHK = True
	for p in path_list:
		if not p.exists():
			print('ERROR: "' + str(p) + '" is not found!')
			CHK = False
			
	return CHK



def image_convert_main(f, same_hierarchy, values):
	f_re = f.relative_to(same_hierarchy)
	im = Image.open(f)

	#立ち絵ちょっと切り出し
	if (im.width == 802) and (im.height == 602):
		im_crop = im.crop((1, 1, 801, 601))
		im_crop.save(f)

	#メッセージウィンドウ半透明白塗り用
	elif (im.width == 754) and (im.height == 82) and (f.name == '91.png'):
		if values: im3 = Image.new("RGBA", (im.width, im.height), (0, 0, 0, 0))
		else: im3 = Image.new("RGBA", (im.width*2, im.height*2), (0, 0, 0, 0))#そのままだとPSP縮小時なぜか右&下盛大にバグるので空白作る
		im2 = Image.new("RGBA", (719-33, 75-5), (192, 192, 192, 192)) #白塗り背景に白文字は見にくいので
		im3.paste(im, (0, 0))
		im3.paste(im2, (34, 6))
		im3.save(f)
	
	#黒背景
	elif f_re in [Path(r'.\Exports\K\11.png'),Path(r'.\Exports\K\12.png'),Path(r'.\Exports\K\13.png'),Path(r'.\Exports\K\14.png'),Path(r'.\Exports\K\15.png'),Path(r'.\Exports\K\16.png'),Path(r'.\Exports\K\17.png'),Path(r'.\Exports\K\18.png'),Path(r'.\Exports\S\11.png'),Path(r'.\Exports\T\11.png'),Path(r'.\Exports\T\12.png'),Path(r'.\Exports\T\13.png'),Path(r'.\Exports\T\14.png'),Path(r'.\Exports\T\15.png'),Path(r'.\Exports\T\16.png'),Path(r'.\Exports\T\17.png'),Path(r'.\Exports\T\18.png'),Path(r'.\Exports\Y\21.png'),Path(r'.\Exports\Y\22.png'),Path(r'.\Exports\Y\23.png'),Path(r'.\Exports\Y\24.png'),Path(r'.\Exports\Y\25.png'),Path(r'.\Exports\Y\26.png'),Path(r'.\Exports\Y\27.png'),Path(r'.\Exports\Y\28.png'),Path(r'.\Exports\Y\29.png'),Path(r'.\Exports\Z\11.png'),Path(r'.\Exports\Z\12.png'),Path(r'.\Exports\Z\13.png'),Path(r'.\Exports\Z\14.png'),Path(r'.\Exports\Z\15.png')]:
		im2 = Image.new("RGBA", (800, 600), (0, 0, 0, 255))
		im2.paste(im, (400-math.ceil(im.width/2), 300-math.ceil(im.height/2)))
		im2.save(f)
		
	#目
	elif f_re in [Path(r'.\Exports\GENERAL\131.png'),Path(r'.\Exports\GENERAL\132.png'),Path(r'.\Exports\GENERAL\133.png'),Path(r'.\Exports\GENERAL\134.png'),Path(r'.\Exports\GENERAL\135.png'),Path(r'.\Exports\GENERAL\136.png'),Path(r'.\Exports\GENERAL\137.png'),Path(r'.\Exports\GENERAL\138.png')]:
		im2 = Image.new("RGBA", (800, 600), (0, 0, 0, 0))
		im2.paste(im, (400-math.ceil(im.width/2), 300-math.ceil(im.height/2)))
		im2.save(f)
	
	#タイトルボタン
	elif f_re in [Path(r'.\Exports\MENU\22.png'),Path(r'.\Exports\MENU\23.png'),Path(r'.\Exports\MENU\24.png'),Path(r'.\Exports\MENU\25.png'),Path(r'.\Exports\MENU\26.png'),Path(r'.\Exports\MENU\31.png'),Path(r'.\Exports\MENU\41.png'),Path(r'.\Exports\MENU\62.png'),Path(r'.\Exports\MENU\64.png')]:
		im2 = Image.new("RGBA", (im.width, im.height), (255, 255, 255, 192))
		im2.save(f.parent / str(f.stem + '_btn.png'))



def image_convert(path_list, same_hierarchy, values):
	with concurrent.futures.ThreadPoolExecutor() as executor:#マルチスレッドで高速化
		futures = []
		for d in path_list:
			for f in d.glob('*.png'):
				futures.append(executor.submit(image_convert_main, f, same_hierarchy, bool(values)))
		concurrent.futures.as_completed(futures)



def file_rename(path_list):

	name_dict = {}

	for d in path_list:
		name_dict[d.stem] = {}

		#そのディレクトリのcsv読込
		with open(Path(d / 'Members.csv'), encoding='cp932', errors='ignore') as f: s = f.read()
		for a in re.findall(r'([0-9]+?),(.+?),(.+?),(.+),', s): name_dict[d.stem][a[2]] = str(a[0])

	return name_dict



# txt置換→0.txt出力関数
def text_cnv(DEBUG_MODE, zero_txt, path_list, same_hierarchy , name_dict):

	#default.txtを読み込み
	txt = default_txt()

	#シナリオファイルを読み込み
	for d in path_list:
		for p in d.glob('*.txt'):
			with open(p, encoding='cp932', errors='ignore') as f:
				fr = f.read()

				#デコード済みtxt一つごとに開始時改行&サブルーチン化
				if DEBUG_MODE: txt += '\n;--------------- '+ str(p.parent.name) + ' - ' + str(p.name) +' ---------------'
				txt += ('\n*SCR_'+ str(p.parent.name) + '_' + str(p.name).replace('.', '_') +'\n')
				txt += 'mov $185,"'+str(p.parent.name)+'"\n\n'

				for line in fr.splitlines():
					cmd_line = re.match(r'<(/)?([A-z]+?)(/)?>', line)
					
					if cmd_line:
						# [2] - 現在未設定 {'reset', 'waitmusic'}
						#reset → 画像消す
						if cmd_line[2] == 'preload':
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %167,1'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %167,0'
							else:
								print('ERR:preload')

						elif cmd_line[2] == 'shade':#preload使いまわし=無視
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %167,1'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %167,0'
							else:
								print('ERR:shade')

						elif cmd_line[2] == 'mono':
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %156,1:setwin 0'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %156,0'
							else:
								print('ERR:mono')

						elif cmd_line[2] == 'talk':
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %157,1:setwin 1'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %157,0:csp 10'
							else:
								print('ERR:talk')

						elif cmd_line[2] == 'char':
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %161,1'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %161,0'
							else:
								print('ERR:char')

						elif cmd_line[2] == 'back':
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %162,1'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %162,0'
							else:
								print('ERR:back')

						elif cmd_line[2] == 'event':
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %163,1'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %163,0'
							else:
								print('ERR:event')

						elif cmd_line[2] == 'skipon':
							if (not cmd_line[1]) and (cmd_line[3]):
								line = 'mov %160,1'
							else:
								print('ERR:skipon')

						elif cmd_line[2] == 'skipoff':
							if (not cmd_line[1]) and (cmd_line[3]):
								line = 'mov %160,0'
							else:
								print('ERR:skipoff')

						elif cmd_line[2] == 'sky':
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %165,1'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %165,0'
							else:
								print('ERR:sky')

						elif cmd_line[2] == 'eye':
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %166,1'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %166,0'
							else:
								print('ERR:eye')

						elif cmd_line[2] == 'clear':
							if (not cmd_line[1]) and (cmd_line[3]):
								line = 'textclear_d'
							else:
								print('ERR:clear')

						elif cmd_line[2] == 'shake':
							if (not cmd_line[1]) and (cmd_line[3]):
								line = 'quake 4,300'
							else:
								print('ERR:shake')

						elif cmd_line[2] == 'wait':
							if (not cmd_line[1]) and (cmd_line[3]):
								line = 'click'
							else:
								print('ERR:wait')

						elif cmd_line[2] == 'monoreturn':#monoになる
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %157,0:csp 10:mov %156,1:setwin 0'
							else:
								print('ERR:monoreturn')

						elif cmd_line[2] == 'monoescape':#monoやめる
							if (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %156,0:mov %157,1:setwin 1'
							else:
								print('ERR:monoescape')

						elif cmd_line[2] == 'waitse':#効果音終わり待ち 念の為%195初期化
							if (not cmd_line[1]) and (cmd_line[3]):
								line = 'waittimer %195:mov %195,0'
							else:
								print('ERR:waitse')

						elif cmd_line[2] == 'audio':
							if (not cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %168,1'
							elif (cmd_line[1]) and (not cmd_line[3]):
								line = 'mov %168,0'
							else:
								print('ERR:audio')

						elif cmd_line[2] == 'reset':
							if (not cmd_line[1]) and (cmd_line[3]):
								line = 'csp 24:csp 25:print 10'
							else:
								print('ERR:reset')

						else:
							line = (';' + line)

					else:
						line = ('lc "' + line +'"')

					#変換した命令行が空ではない場合
					if line: txt += (line + '\n')#入力
				
				txt += '\nreturn\n'


	#imgif 190-現在dir 191-入力txt 195 出力img
	img_if_txt = ''
	for k, v in name_dict.items():
		if (not k=='GENERAL') and (not k=='AUDIO') and (not k=='CHARS'): img_if_txt += ('if $185!="'+k+'" goto *skip_dir_'+k+'\n')
		
		for k2, v2 in v.items():
			if(k=='AUDIO'):#wav時ついでに再生時間取得(waitseで利用)
				wav_path = Path(same_hierarchy / 'Exports' / k / str(v2 + '.wav'))
				if wav_path.exists():
					with wave.open(str(wav_path), mode='rb') as wf:
						wav_time = str(math.floor(float(wf.getnframes() / wf.getframerate()) * 1000))#ミリ秒
					img_if_txt += ('if $191=="' + k2 + '" mov $195,"Exports/' + k + '/' + v2 + '.wav":mov %195,' + wav_time + ':goto *imend\n')
			else:
				img_if_txt += ('if $191=="' + k2 + '" mov $195,"Exports/' + k + '/' + v2 + '.png":goto *imend\n')

		if (not k=='GENERAL') and (not k=='AUDIO') and (not k=='CHARS'): img_if_txt += ('*skip_dir_'+k+'\n')
	img_if_txt += '*imend\n'
	txt = txt.replace(r';<<-img_if_txt->>', img_if_txt)

	#出力結果を書き込み
	open(zero_txt, 'w', errors='ignore').write(txt)
	return


# メイン関数
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	# デバッグモード
	debug = 0

	#同一階層のパスを変数へ代入
	same_hierarchy = pre_converted_dir#Path.cwd()

	#デバッグ時はtestディレクトリ直下
	if debug: same_hierarchy = (same_hierarchy / '_test')

	#利用するパスを辞書に入れ一括代入
	PATH_DICT = {
		#先に準備しておくべきファイル一覧
		'READY' :(same_hierarchy / 'Exports' / 'READY'),
		'K' :(same_hierarchy / 'Exports' / 'K'),
		'MENU' :(same_hierarchy / 'Exports' / 'MENU'),
		'S' :(same_hierarchy / 'Exports' / 'S'),
		'T' :(same_hierarchy / 'Exports' / 'T'),
		'Y' :(same_hierarchy / 'Exports' / 'Y'),
		'Z' :(same_hierarchy / 'Exports' / 'Z'),
		'AUDIO' :(same_hierarchy / 'Exports' / 'AUDIO'),
		'CHARS' :(same_hierarchy / 'Exports' / 'CHARS'),
		'GENERAL' :(same_hierarchy / 'Exports' / 'GENERAL'),
	}

	PATH_DICT2 = {
		#変換後に出力されるファイル一覧
		'0_txt' :(same_hierarchy / '0.txt'),
	}

	#ディレクトリの存在チェック
	dir_check_result = dir_check(PATH_DICT.values())

	#存在しない場合終了
	if not dir_check_result: raise FileNotFoundError('終ノ空の展開ファイルが不足しています')

	#名前変更だったもの - 実際は辞書作成
	name_dict = file_rename(PATH_DICT.values())

	#一部画像変換
	image_convert(PATH_DICT.values(), same_hierarchy, values)

	#txt置換→0.txt出力
	text_cnv(debug, PATH_DICT2['0_txt'], PATH_DICT.values(), same_hierarchy, name_dict)


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()