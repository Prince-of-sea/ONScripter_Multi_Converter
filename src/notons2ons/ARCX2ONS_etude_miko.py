#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import concurrent.futures
import shutil, re


# 作品について
def title_info():
	return {
		'brand': 'etude',
		'date': 20041126,
		'title': '巫女舞 ～ただ一つの願い～',
		'cli_arg': 'etude_mikomai',
		'requiredsoft': [],
		'is_4:3': True,
		'exe_name': ['mikomai'],

		'version': [
			'巫女舞 〜ただ一つの願い〜 FANZA DL版(qual_0013)',
		],

		'notes': [
			'ウィンドウは見やすくするため文字大きめ＆背景暗めに変更',
			'画像から場所を選択する形式の選択肢も普通の仕様に変更',
			'セーブ、ロード、コンフィグ画面など基本UIは簡略化',
			'一部箇所で本来では出ない暗転が挟まれる事がある',
			'主人公の名前はデフォルト(元樹)で固定',
			'背景/CGのガウスぼかし処理が若干違う',
			'スタッフロールは画像表示のみ実装',
			'おまけ(回想モードなど)は未実装',
			'半透明の立ち絵が表示されない',
			'画面遷移はフェードのみ',
			'たまに立ち絵がズレる',
		]
	}


# リソース自動展開 (マルチコンバータ組み込み時にのみ利用)
def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	# 動画コピー
	opening_path = Path(input_dir / 'opening.mpg')
	if not opening_path.is_file(): raise FileNotFoundError(f'{opening_path}が見つかりません')#なければ強制エラー	
	shutil.copy(opening_path, pre_converted_dir)

	# サウンドコピー
	for dir_name in ['BGM', 'SE']:
		shutil.copytree(Path(input_dir / dir_name), Path(pre_converted_dir / dir_name))

	# arc展開
	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for arc_name in ['bg', 'cg', 'obj', 'scx', 'stand', 'voice']:
			arc_path = Path(input_dir / f'{arc_name}.arc')
			
			if not arc_path.is_file(): raise FileNotFoundError(f'{arc_path}が見つかりません')#なければ強制エラー
			futures.append(executor.submit(extract_archive, arc_name, arc_path, pre_converted_dir))
		
		concurrent.futures.as_completed(futures)

	return


# リソース自動展開本処理
def extract_archive(arc_name: str, arc_path: Path, pre_converted_dir: Path):
	from utils import extract_archive_garbro # type: ignore

	result_dir = Path(pre_converted_dir / arc_name)
	ex_dir = Path(pre_converted_dir / f'_{arc_name}')
	ex_main_dir = Path(ex_dir / arc_name)
	
	# objのみ事前展開→名前被り削除→再圧縮→変換展開
	if (arc_name == 'obj'):
		ex_main_zippath = Path(ex_dir / f'{arc_name}.zip')
		extract_archive_garbro(arc_path, ex_dir)

		for p in ex_main_dir.glob('*.bmp'):
			ps = p.with_suffix('.tga')
			if ps.exists(): ps.unlink()
		
		shutil.make_archive(ex_main_dir, format='zip', root_dir=ex_main_dir)
		shutil.rmtree(ex_main_dir)
		extract_archive_garbro(ex_main_zippath, result_dir, 'png')
		ex_main_zippath.unlink()

	# 通常時はそのまま変換展開	
	else:
		extract_archive_garbro(arc_path, ex_dir, 'png')
		shutil.move(ex_main_dir, result_dir)

	# 元の展開先ディレクトリ削除
	shutil.rmtree(ex_dir)

	# 不要ファイル(*.db)削除
	for p in result_dir.glob('*.db'): p.unlink()

	return


# 0.txtにはじめから書いておくもの (旧コンバータdefault.txt相当)
def default_txt(txt: str, val_txt: str, add0txt_effect: str, end_str_list: list):#todo:スタッフロール文字いつか作る
	return f''';mode800,value1000
*define

caption "巫女舞 for ONScripter"

rmenu "保存",save,"開く",load,"タイトルに戻る",reset,"選択肢まで進む",skip,"バックログ",lookback
savenumber 18
transmode alpha
globalon
rubyon
saveon
nsa
windowback
humanz 20

numalias val_onstmp,47
numalias val_chr_1,48
numalias val_chr_2,49
numalias val_bg,50

numalias onstmpx,54
numalias onstmpy,55
numalias chr_1x,56
numalias chr_1y,57
numalias chr_2x,58
numalias chr_2y,59

numalias aud_bgm,1400
numalias aud_vo,1401
numalias aud_se,1402

numalias val_def_default,400
{val_txt}

effect  9,10,200
effect 10,10,500
{add0txt_effect}

defsub def_mes
defsub def_meswait
defsub def_default
defsub def_read
defsub def_chrin
defsub def_change
defsub def_setpos
defsub def_setpos_int
defsub def_alpha
defsub setwin
game
;----------------------------------------
*LABEL_s_question_2
*LABEL_s_question_3
*LABEL_s_question_4
	setwin 2

	select $val_sel_1,*sel1,
	       $val_sel_2,*sel2,
	       $val_sel_3,*sel3,
	       $val_sel_4,*sel4

	*sel1
		mov %val_answer,0:goto *selend
	*sel2
		mov %val_answer,1:goto *selend
	*sel3
		mov %val_answer,2:goto *selend
	*sel4
		mov %val_answer,3

	*selend
	mov $val_sel_1,""
	mov $val_sel_2,""
	mov $val_sel_3,""
	mov $val_sel_4,""

	setwin 1
return
;----------------------------------------
*LABEL_s_placesel_free
*LABEL_s_placesel_job
	setwin 2

	select "夏希",*sel1p,
	       "久音",*sel2p,
	       "琥珀",*sel3p,
	       "茜",*sel4p

	*sel1p
		mov %val_answer,0:goto *selendp
	*sel2p
		mov %val_answer,1:goto *selendp
	*sel3p
		mov %val_answer,2:goto *selendp
	*sel4p
		mov %val_answer,3

	*selendp
	setwin 1
return
;----------------------------------------
*LABEL_s_placesel_large
	setwin 2

	select "夏希",*sel1p2,
	       "琥珀",*sel3p2

	*sel1p2
		mov %val_answer,0:goto *selendp2
	*sel3p2
		mov %val_answer,1

	*selendp2
	setwin 1
return
;----------------------------------------
*LABEL_s_endroll
	skipoff
	saveoff

	lsph 200,"obj/"+$val_ed00,0,0
	lsph 201,"obj/"+$val_ed01,0,0
	lsph 202,"obj/"+$val_ed02,0,0
	lsph 203,"obj/"+$val_ed03,0,0
	lsph 204,"obj/"+$val_ed04,0,0
	lsph 205,"obj/"+$val_ed05,0,0

	resettimer

	*endroll_loop
		gettimer %77

		if %77>=0      if %77<31000  vsp 200,1:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,0:amsp 200,-1*(800*(%77-     0)/31000),0
		if %77>=31000  if %77<32000  vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,0:print 9:waittimer 31999
		if %77>=32000  if %77<63000  vsp 200,0:vsp 201,1:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,0:amsp 201,0,-1*(600*(%77- 32000)/31000)
		if %77>=63000  if %77<64000  vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,0:print 9:waittimer 63999
		if %77>=64000  if %77<95000  vsp 200,0:vsp 201,0:vsp 202,1:vsp 203,0:vsp 204,0:vsp 205,0:amsp 202,-1*(800*(%77- 64000)/31000),0
		if %77>=95000  if %77<96000  vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,0:print 9:waittimer 95999
		if %77>=96000  if %77<127000 vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,1:vsp 204,0:vsp 205,0:amsp 203,0,-1*(600*(%77- 96000)/31000)
		if %77>=127000 if %77<128000 vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,0:print 9:waittimer 127999
		if %77>=128000 if %77<159000 vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,1:vsp 205,0:amsp 204,-1*(800*(%77-128000)/31000),0
		if %77>=159000 if %77<160000 vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,0:print 9:waittimer 159999
		if %77>=160000 if %77<191000 vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,1:amsp 205,0,-1*(600*(%77-160000)/31000)
		if %77>=191000 if %77<192000 vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,0:print 9:waittimer 191999

		print 1
		if %77>=192000 goto *endroll_loop_end
	goto *endroll_loop
	*endroll_loop_end
	
	lsp 210,"obj/etude_logo.png",600,520:print 10
	click
	csp 210:print 10
	saveon
return
;----------------------------------------
*def_mes
	getparam $1,$2
	if $1=="" vsp 10,0
	if $1!="" lsp 10,":s/24,24,0;#ffffff【"+$1+"】",60,458
	fileexist %2,$2
	if %2==1 dwave 0,$2
return
	
*def_meswait
	\\
	vsp 10,0
return

*def_default
	getparam $val_def_default
return

*def_read
	getparam $1,$2
	if $1=="onstmp" mov $val_def_default,$2

	if $1=="bg"    mov $val_bg,$2
	if $1=="chr_1" mov $val_chr_1,$2
	if $1=="chr_2" mov $val_chr_2,$2
return

*def_chrin
	getparam $1,$2

	if $1=="center" mov %4,400
	if $1=="right"  mov %4,600
	if $1=="left"   mov %4,200
	
	if $2=="chr_1" mov $3,$val_chr_1:mov %5,val_chr_1
	if $2=="chr_2" mov $3,$val_chr_2:mov %5,val_chr_2

	lsph %5,$3,0,0
	getspsize %5,%8,%9

	if $2=="chr_1" mov %chr_1x,%4:mov %chr_1y,0:msp %5,%chr_1x-(%8/2),%chr_1y
	if $2=="chr_2" mov %chr_2x,%4:mov %chr_2y,0:msp %5,%chr_2x-(%8/2),%chr_2y

	vsp %5,1
	print 1
return

*def_change
	getparam $1,$2

	if $1=="chr_1" mov %5,val_chr_1
	if $1=="chr_2" mov %5,val_chr_2

	if $1=="chr_1" lsph %5,$2,0,0
	if $1=="chr_2" lsph %5,$2,0,0

	getspsize %5,%8,%9

	if $1=="chr_1" msp %5,%chr_1x-(%8/2),%chr_1y
	if $1=="chr_2" msp %5,%chr_2x-(%8/2),%chr_2y
	vsp %5,1
	print 1
return

*def_setpos
	getparam $1,$2

	if $2=="center" mov %4,400
	if $2=="right"  mov %4,600
	if $2=="left"   mov %4,200

	if $1=="chr_1" mov %5,val_chr_1
	if $1=="chr_2" mov %5,val_chr_2

	getspsize %5,%8,%9

	if $1=="chr_1" mov %chr_1x,%4:mov %chr_1y,0:msp %5,%chr_1x-(%8/2),%chr_1y
	if $1=="chr_2" mov %chr_2x,%4:mov %chr_2y,0:msp %5,%chr_2x-(%8/2),%chr_2y

	print 9
return

*def_setpos_int
	getparam $1,%2,%3

	if $1=="chr_1" mov $5,$val_chr_1
	if $1=="chr_2" mov $5,$val_chr_2
	if $1==""      mov $5,$val_onstmp
	
	if $1=="chr_1" mov %chr_1x, %2:mov %chr_1y, %3
	if $1=="chr_2" mov %chr_2x, %2:mov %chr_2y, %3
	if $1==""      mov %onstmpx,%2:mov %onstmpy,%3
	
	print 9
return

*def_alpha
	getparam $1,%2

	getspsize %5,%8,%9
	
	;if $1=="bg" 
	if $1=="chr_1" msp %5,%chr_1x-(%8/2),%chr_1y,%2
	if $1=="chr_2" msp %5,%chr_2x-(%8/2),%chr_2y,%2
return
;----------------------------------------
*setwin
	getparam %1
	if %1==1 setwindow  60,480,30,2,24,24,0, 5,10,1,1,"obj/main-kaiwa_.png",  0,385
	if %1==2 setwindow 110,220,26,2,24,24,0,21, 0,1,1,#999999,                0,  0,799,599
return
;----------------------------------------
*volmenu_GUI
	;https://gist.github.com/Prince-of-sea/325b8ae6912ecf23316a71c3d008480c
	;文字/数字/スプライト/ボタン
	;全部130~149までを使ってます - 競合に注意
	
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
	
	;文字列変換
	itoa2 $141,%aud_bgm
	itoa2 $142,%aud_se
	itoa2 $143,%aud_vo
	
	;バー代入
	if %aud_bgm==  0 mov $146,$130
	if %aud_bgm== 10 mov $146,$131
	if %aud_bgm== 20 mov $146,$132
	if %aud_bgm== 30 mov $146,$133
	if %aud_bgm== 40 mov $146,$134
	if %aud_bgm== 50 mov $146,$135
	if %aud_bgm== 60 mov $146,$136
	if %aud_bgm== 70 mov $146,$137
	if %aud_bgm== 80 mov $146,$138
	if %aud_bgm== 90 mov $146,$139
	if %aud_bgm==100 mov $146,$140
	if %aud_se==  0 mov $147,$130
	if %aud_se== 10 mov $147,$131
	if %aud_se== 20 mov $147,$132
	if %aud_se== 30 mov $147,$133
	if %aud_se== 40 mov $147,$134
	if %aud_se== 50 mov $147,$135
	if %aud_se== 60 mov $147,$136
	if %aud_se== 70 mov $147,$137
	if %aud_se== 80 mov $147,$138
	if %aud_se== 90 mov $147,$139
	if %aud_se==100 mov $147,$140
	if %aud_vo==  0 mov $148,$130
	if %aud_vo== 10 mov $148,$131
	if %aud_vo== 20 mov $148,$132
	if %aud_vo== 30 mov $148,$133
	if %aud_vo== 40 mov $148,$134
	if %aud_vo== 50 mov $148,$135
	if %aud_vo== 60 mov $148,$136
	if %aud_vo== 70 mov $148,$137
	if %aud_vo== 80 mov $148,$138
	if %aud_vo== 90 mov $148,$139
	if %aud_vo==100 mov $148,$140
	
	;画面作成
	lsp 130,":s;#FFFFFF［Ｃｏｎｆｉｇ］", 50, 50
	lsp 131,":s;#FFFFFF#666666リセット", 400,450
	lsp 132,":s;#FFFFFF#666666戻る",     550,450
	
	lsp 135,":s;#FFFFFFＢＧＭ",           50,150
	lsp 136,":s;#FFFFFF#666666＜",       200,150
	lsp 137,$146,                        250,150
	lsp 138,":s;#FFFFFF#666666＞",       550,150
	lsp 139,":s;#FFFFFF#666666"+$141,    600,150
	
	lsp 140,":s;#FFFFFFＳＥ",           50,250
	lsp 141,":s;#FFFFFF#666666＜",       200,250
	lsp 142,$147,                        250,250
	lsp 143,":s;#FFFFFF#666666＞",       550,250
	lsp 144,":s;#FFFFFF#666666"+$142,    600,250
	
	lsp 145,":s;#FFFFFFＶＯＩＣＥ",        50,350
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
	
	if %140==131 mov %aud_bgm,100:mov %aud_se,100:mov %aud_vo,100
	if %140==132 dwave 1,"SE/SE_900.WAV":csp -1:bg black,10:reset
	if %140==136 if %aud_bgm!=  0 sub %aud_bgm,10
	if %140==138 if %aud_bgm!=100 add %aud_bgm,10
	if %140==141 if %aud_se!=  0 sub %aud_se,10
	if %140==143 if %aud_se!=100 add %aud_se,10
	if %140==146 if %aud_vo!=  0 sub %aud_vo,10
	if %140==148 if %aud_vo!=100 add %aud_vo,10
	
goto *volmenu_loop
;----------------------------------------
*start

;初回起動時 - 音量用変数すべて100
fileexist %130,"gloval.sav"
if %130==0 if %aud_bgm==0 if %aud_se==0 if %aud_vo==0 mov %aud_bgm,100:mov %aud_se,100:mov %aud_vo,100

bgmvol   60*%aud_bgm/100
sevol    60*%aud_se/100
voicevol 60*%aud_vo/100

setwin 1

;autostart - debug
;gosub *LABEL_M_ALL:reset

;ending - debug
;mov $val_ed00,"nk-001.png":mov $val_ed01,"nk-002.png":mov $val_ed02,"nk-003.png":mov $val_ed03,"nk-004.png":mov $val_ed04,"nk-005.png":mov $val_ed05,"nk-006.png":gosub *LABEL_s_endroll:end

bg white,9
wait 500
bg "obj/OP_BRAND.png",10
wait 2000

bg "obj/OP_BG.png",10
bgm "BGM/M22.wav"

mov $1,"OP_BG_00"
if %1019==1 mov $1,"OP_BG_01"
if %1029==1 mov $1,"OP_BG_01"
if %1039==1 mov $1,"OP_BG_01"
if %1049==1 mov $1,"OP_BG_01"
if %1059==1 mov $1,"OP_BG_02"
lsp 201,"obj/"+$1+".png",230,0
lsp 202,"obj/OP_title.png",40,120

lsph 211,"obj/OP_BTN_START_1.png",   460,360
lsph 212,"obj/OP_BTN_CONTINUE_1.png",460,408
lsph 213,"obj/OP_BTN_CONFIG_1.png",  460,456
if $1!="OP_BG_00" lsph 214,"obj/OP_BTN_OMKE_1.png",    460,504
lsph 215,"obj/OP_BTN_EXIT_1.png",    460,552
lsph 221,"obj/OP_BTN_START_0.png",   460,360
lsph 222,"obj/OP_BTN_CONTINUE_0.png",460,408
lsph 223,"obj/OP_BTN_CONFIG_0.png",  460,456
if $1!="OP_BG_00" lsph 224,"obj/OP_BTN_OMKE_0.png",    460,504
lsph 225,"obj/OP_BTN_EXIT_0.png",    460,552

print 1
*title_loop
	bclear

	exbtn_d         "C211C212C213C214C215P221P222P223P224P225"
	exbtn   211,211,"P211C212C213C214C215C221P222P223P224P225"
	exbtn   212,212,"C211P212C213C214C215P221C222P223P224P225"
	exbtn   213,213,"C211C212P213C214C215P221P222C223P224P225"
	exbtn   214,214,"C211C212C213P214C215P221P222P223C224P225"
	exbtn   215,215,"C211C212C213C214P215P221P222P223P224C225"

	print 1
	btnwait %20

	if %20==211 stop:dwave 1,"SE/SE_902.WAV":csp -1:bg black,9:gosub *LABEL_M_ALL:reset
	if %20==212 dwave 1,"SE/SE_902.WAV":lsp 200,"obj/mode_load_.png",  0,0:print 9:systemcall load   :dwave 1,"SE/SE_900.WAV":csp 200:print 9:goto *title_loop
	if %20==213 dwave 1,"SE/SE_902.WAV":lsp 200,"obj/mode_config_.png",0,0:print 9:gosub *volmenu_GUI
	;if %20==214 wait 1
	if %20==215 stop:dwave 1,"SE/SE_900.WAV":csp -1:bg black,10:wait 200:end
goto *title_loop
;----------------------------------------
{txt}
'''


# アルファベットのみ小文字に変換する関数
def lower_AtoZ(s: str):

	# 変換を適用して返す
	return s.translate( str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') )


# ファイル/ディレクトリの存在チェック関数
def file_check(PATH_DICT: dict):
	
	# エラー用文字列
	errmsg = ''

	# 利用するパスをfor
	for dir_path in PATH_DICT.values():
		
		# 存在しなければエラー用文字列に追記
		if not Path(dir_path).exists(): errmsg += f'{dir_path}が存在しません\n'
	
	# エラー用文字列が空ではない(エラーがある)なら例外出して強制終了
	if (errmsg != ''): raise Exception(errmsg)
	
	# 関数終了
	return


# 画像加工関数
def image_processing(PATH_DICT: dict, gauss_img_list: list, pre_converted_dir: Path):

	# ウィンドウ関連
	p_in = Path(PATH_DICT['obj'] / 'main-kaiwa.png')
	p_out = Path(PATH_DICT['obj'] / 'main-kaiwa_.png')
	bg2h = 55#全部にすると黒塗り部分が長すぎるのでここで調整
	im = Image.open(p_in)
	bg1 = Image.new('RGBA', im.size, (0, 0, 0, 64))
	bg2 = Image.new('RGBA', (im.width, bg2h), (0, 0, 0, 0))
	bg1.paste(bg2)
	im_r = Image.alpha_composite(bg1, im)
	im_r.save(p_out, 'PNG')

	# 背景/CGガウス処理関連
	for gauss_img_path in set(gauss_img_list):
		p_in = Path( pre_converted_dir / gauss_img_path.with_suffix('.png'))
		p_out = Path(p_in.parent / f'{p_in.stem}_gauss.png')

		if p_out.is_file(): continue

		im = Image.open(p_in)
		im_r = im.filter(ImageFilter.BLUR)
		im_r.save(p_out, 'PNG')
	
	# コンフィグ明るさ下げる
	for img_name in ['mode_config', 'mode_load']:
		p_in = Path(PATH_DICT['obj'] / f'{img_name}.png')
		p_out = Path(PATH_DICT['obj'] / f'{img_name}_.png')
		im = Image.open(p_in)
		enhancer = ImageEnhance.Brightness(im)
		im_r = enhancer.enhance(0.4)
		im_r.save(p_out, 'PNG')

	return


# 画像と長さからエフェクト番号自動生成
def effect_edit(t,f,effect_startnum,effect_list):

	list_num=0
	if re.fullmatch(r'[0-9]+',t):#timeが数字のみ＝本処理

		for i, e in enumerate(effect_list,effect_startnum+1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			effect_list.append([t,f])
			list_num = len(effect_list)+effect_startnum

	return str(list_num),effect_startnum,effect_list


# ons仕様へ変数置換(dollar to numalias)
def d2na(s: str):
	if not s: return ''#Noneとかの場合は無の文字列
	return s.replace(r'$', r'%val_')


# ons仕様へ変数置換(dollar to stralias)
def d2sa(s: str):
	if not s: return ''#Noneとかの場合は無の文字列
	return s.replace(r'$', r'$val_')


# シナリオ変換処理関数
def text_cnv(debug: bool, PATH_DICT: dict, PATH_DICT2: dict):

	# エフェクト管理(いつもの)
	effect_startnum = 10
	effect_list = []

	# 飛ばされている(未実装の)コマンドリストを作成
	skip_command_list = []

	# 元のシナリオファイル内で使っている変数リスト作成
	val_list = []

	# ぼかし画像リストを作成
	gauss_img_list = []

	# if文変換時に使うgotoの連番 - 一桁はCtrl+F検索時面倒なので10スタート
	if_goto_cnt = 10
	end_goto_cnt = 10

	# シナリオ文字列保持用変数
	txt = ''

	# シナリオファイルを読み込み
	for scx_path in Path(PATH_DICT['scx']).glob('*.scx'):

		# シナリオファイル名を取得
		scxfilename = str(scx_path.stem)

		#if入った際にelseの行き先とか突っ込んどく - 配列にすることでif内ifに対応
		if_list = []
		end_list = []

		# 除外リストを作成
		exclusion_list = ['init_system', 'S_SCENE', 'S_BACKLOG', 'S_CONFIG', 'S_DATALOAD', 'S_DATASAVE', 'S_DIALOG', 'S_FLAGVIEW', 'S_GALLERY', 'S_KEYBIND', 'S_LOADDIALOG', 'S_MUSIC', 'S_NAMEENTRY', 'S_PLACESEL', 'S_QUESTION', 'S_SAVEDIALOG', 'S_TITLE', 'S_SCENE', 'S_SCX_END', 'S_SHORT_AUTO', 'S_SHORT_CONFIG', 'S_SHORT_HIDE', 'S_SHORT_LOAD', 'S_SHORT_LOG', 'S_SHORT_QLOAD', 'S_SHORT_QSAVE', 'S_SHORT_SAVE', 'S_SHORT_SKIP', 'S_SURFACE', 'S_OMAKE', 'S_MESBUTTON', 'S_ENDROLL']

		# 非デバッグモード時システム関連は無視して次のシナリオファイルへ
		if (not debug) and (scxfilename in exclusion_list): continue

		# シナリオファイルごとにまずラベルを追加
		txt += (
			 '\n;///========================================///\n'+\
			f'{';' if (scxfilename in exclusion_list) else ''}*LABEL_{scxfilename}'+\
			 '\n;///========================================///\n'
		)

		# scxファイルを読み込み
		with open(scx_path, 'r', encoding='cp932') as f:
			
			# 1行ずつ文字列読み込み
			for line in f.readlines():

				# デバッグモード時システム関連全部コメントアウト
				if (debug) and (scxfilename in exclusion_list): txt += f';{line[:-1]}\n'; continue

				# アルファベットを小文字に
				line = lower_AtoZ(line)

				# タブスペースを最低以外削除
				line = line.replace(']"', '] "')#何故かくっついてるところがあるので一時しのぎ
				line = line.replace('\u3000', ' ')
				line = line.replace(' ', '\t')
				while ('\t\t' in line): line = line.replace('\t\t', '\t')

				# 行頭行末スペースと行末の改行を削除
				line = re.fullmatch(r'(\s+)?(.+?)?(\s+)?\n', line).group(2)

				# 空行は無視して次の行へ
				if not line: txt += '\n'; continue

				# 行頭で分岐
				match line[0]:

					# 行頭 - コマンド
					case '/':

						# コメント関連処理
						comment = ''
						comment_line = re.match(r'(.+?)\t?;\t?(.+)', line)
						if comment_line:
							line = comment_line.group(1)
							comment = comment_line.group(2)
						
						# 一行に複数コマンドがある場合を考慮してリスト化
						for line_ in line.split('/'):

							# 切った"/"、"\n"付け直し("\n"は後で消す)
							if line_:  line = f'/{line_}\n'

							# コマンドがない場合は無視
							else: continue

							# タブスペースを最低以外削除(二回目)
							line = line.replace('\u3000', ' ')
							line = line.replace(' ', '\t')
							while ('\t\t' in line): line = line.replace('\t\t', '\t')

							# 行頭行末スペースと行末の改行を削除(二回目)
							line = re.fullmatch(r'(\s+)?(.+?)?(\s+)?\n', line).group(2)

							# コマンド代入
							command = re.match(r'/([a-z]+)', line).group(1)

							# コマンドの引数(?)を代入
							command_arg = line.split('\t')[1:]

							# コマンドで分岐
							match command:

								# コマンド - シナリオコール
								case 'call':
									call_arg0_1 = re.match(r'"scx\\([a-z0-9_]+)\.scx"', command_arg[0]).group(1)
									line = f'gosub *LABEL_{call_arg0_1}'
									
									if (len(command_arg) > 1) and (command_arg[1][0] == '@'):
										line += f'_{command_arg[1][1:]}'

									if (call_arg0_1.upper() in exclusion_list) and (not call_arg0_1 in ['s_question', 's_placesel', 's_endroll']):
										line = f';{line}'

								# コマンド - シナリオジャンプ
								case 'jump':
									line = f'goto *LABEL_{scxfilename}'
									for arg in command_arg:
										jumpif_arg0 = re.match(r'\[(\$[a-z0-9_]+)(([<>=]{,2})([0-9]+|\$([a-z0-9_]+)))?\]', arg)

										if jumpif_arg0:
											if jumpif_arg0[2]:
												line = f'if {d2na(jumpif_arg0[1])}{jumpif_arg0[3]}{d2na(jumpif_arg0[4])} {line}'
											else:
												line = f'if {d2na(jumpif_arg0[1])}==1 {line}'
											
											if (not d2na(jumpif_arg0[1]) in val_list) and (not re.fullmatch(r'[0-9]*', d2na(jumpif_arg0[1]))): val_list.append(d2na(jumpif_arg0[1]))
										
										else: line += f'_{arg[1:]}'
								
								# コマンド - 変数計算
								case 'calc':
									calc_arg0 = re.match(r'\[(\$[a-z0-9_]+)=([0-9]+|\$([a-z0-9_]+))\]', command_arg[0])
									line = f'mov {d2na(calc_arg0[1])},{d2na(calc_arg0[2])}'

									if (not d2na(calc_arg0[1]) in val_list) and (not re.fullmatch(r'[0-9]*', d2na(calc_arg0[1]))): val_list.append(d2na(calc_arg0[1]))
									if (not d2na(calc_arg0[2]) in val_list) and (not re.fullmatch(r'[0-9]*', d2na(calc_arg0[2]))): val_list.append(d2na(calc_arg0[2]))
								
								# コマンド - 変数加算
								case 'add':
									try:#やる気のない例外処理
										add_arg0_1 = f'${re.match(r'\'([a-z]+)\'', command_arg[0]).group(1)}'
										add_arg1_1 = re.match(r'\[\+([0-9]+)\]', command_arg[1]).group(1)
									except: line = f';{line}'; continue
									line = f'add {d2na(add_arg0_1)},{add_arg1_1}'

									if (not d2na(add_arg0_1) in val_list) and (not re.fullmatch(r'[0-9]*', d2na(add_arg0_1))): val_list.append(d2na(add_arg0_1))

								# コマンド - フラグを立てる
								case 'setflag':
									if command_arg:
										setflag_arg0_1 = f'${re.match(r'\[([0-9]+)\]', command_arg[0]).group(1)}'
										line = f'mov {d2na(setflag_arg0_1)},1'
									else:#まれに引数なしsetflagがいるが詳細不明
										line = f';{line}'
										
									if (not d2na(setflag_arg0_1) in val_list) and (not re.fullmatch(r'[0-9]*', d2na(setflag_arg0_1))): val_list.append(d2na(setflag_arg0_1))

								# コマンド - フラグを折る
								case 'resetflag':
									if (command_arg[0] == r'\['):
										resetflag_arg0_1 = f'${re.match(r'\[([0-9]+)\]', command_arg[0]).group(1)}'
										line = f'mov {d2na(resetflag_arg0_1)},0'

										if (not d2na(resetflag_arg0_1) in val_list) and (not re.fullmatch(r'[0-9]*', d2na(resetflag_arg0_1))): val_list.append(d2na(resetflag_arg0_1))

									else:#(0,999) 本当は全リセットだけど多分放置でいいと思う
										line = f';{line}'

								# コマンド - 条件分岐
								case 'if':
									if_arg0 = re.match(r'\[(\$[a-z0-9_]+)(([<>=]{,2})([0-9]+|\$([a-z0-9_]+)))?\]', command_arg[0])

									if if_arg0[2]:
										line = f'if {d2na(if_arg0[1])}{if_arg0[3]}{d2na(if_arg0[4])} goto *iflabel{if_goto_cnt}'
									else:
										line = f'if {d2na(if_arg0[1])}==1 goto *iflabel{if_goto_cnt}'
									
									line += f'\ngoto *iflabel{if_goto_cnt+1}\n*iflabel{if_goto_cnt}'
									if_list.append(if_goto_cnt+1)
									end_list.append(end_goto_cnt)
									if_goto_cnt += 2
									end_goto_cnt += 1

									if (not d2na(if_arg0[1]) in val_list) and (not re.fullmatch(r'[0-9]*', d2na(if_arg0[1]))): val_list.append(d2na(if_arg0[1]))

								# コマンド - 条件分岐例外
								case 'else':
									line = f'goto *ifendlabel{end_list[-1]}\n*iflabel{if_list[-1]}'
									if_list[-1] = 0

								# コマンド - 条件分岐終了
								case 'endif':
									line = (f'*ifendlabel{end_list[-1]}')
									if if_list[-1] != 0: line = (f'*iflabel{if_list[-1]}\n{line}')
									
									if_list.pop()
									end_list.pop()

								# コマンド - 選択肢設定
								case 'setquestion':
									setquestion_arg0_1 = f'${re.match(r'<([a-z0-9_]+)>', command_arg[0]).group(1)}'
									line = (f'mov {d2sa(setquestion_arg0_1)},"{command_arg[1]}"')
									if (not d2sa(setquestion_arg0_1) in val_list) and (not re.fullmatch(r'[0-9]*', d2sa(setquestion_arg0_1))): val_list.append(d2sa(setquestion_arg0_1))

								# コマンド - メッセージ前設定
								case 'mes':
									mes_arg1_1 = ''
									mes_arg2_1 = ''
									for arg in command_arg[1:]:
										mes_arg1 = re.match(r'\'(.+)\'', arg)
										mes_arg2 = re.match(r'"(.+)"', arg)
										if mes_arg1: mes_arg1_1 = mes_arg1.group(1)
										if mes_arg2: mes_arg2_1 = mes_arg2.group(1)

									line = f'def_mes "{mes_arg1_1}","{mes_arg2_1}"'

								# コマンド - メッセージ待ち
								case 'meswait':
									line = 'def_meswait'

								# コマンド - ウェイト
								case 'wait':
									wait_arg0_1 = re.match(r'\[([0-9]+)\]', command_arg[0]).group(1) if (command_arg) else '500'
									wait_arg0_1 = int(wait_arg0_1)
									if debug: wait_arg0_1 /= 10#デバッグモード時テスト高速化のためウェイト1/10
									if (wait_arg0_1 > 1000): wait_arg0_1 = 1000#1秒以上は1秒と固定する
									line = f'wait {int(wait_arg0_1)}'

								# コマンド - 縦揺れ
								case 'tateyure':
									#一個"/tateyure <bg>"あったけど気にしない
									line = 'quake 2,500'

								# コマンド - テキスト空にする
								case 'mescls':
									line = 'textclear'

								# コマンド - スキップしてた場合止める
								case 'messkip':
									messkip_arg0_1 = re.match(r'\[([0-9]+)\]', command_arg[0]).group(1) if (command_arg) else '0'
									if (messkip_arg0_1 == '0'):
										line = 'skipoff'
										if debug: line = f';{line}'#デバッグモード時テスト高速化のため無効化
								
								# コマンド - グローバル変数(?)書込み
								case 'sysset':
									sysset_arg0_1 = re.match(r'\[([0-9]+)\]', command_arg[0]).group(1)
									line = f'mov %{1000+int(sysset_arg0_1)},1'
								
								# コマンド - パス読み込み
								case 'read':
									read_arg1_1 = 'onstmp'
									read_arg2_1 = ''
									for arg in command_arg:
										
										read_arg1 = re.match(r'<([a-z0-9_]+)>', arg)
										read_arg2 = re.match(r'"(.+)"', arg)
										if read_arg1: read_arg1_1 = read_arg1.group(1)
										if read_arg2: read_arg2_1 = read_arg2.group(1)

									line = f'def_read "{read_arg1_1}","{read_arg2_1}"'

									if (not d2sa(read_arg1_1) in val_list) and (not re.fullmatch(r'[0-9]*', d2sa(read_arg1_1))): val_list.append(d2sa(read_arg1_1))

								# コマンド - 初期値設定的な
								case 'default':
									default_arg0_1 = re.match(r'<([a-z0-9_-]+)>', command_arg[0]).group(1)
									if (default_arg0_1 != '-1'):
										line = f'def_default "{default_arg0_1}"'
									else:
										line = f'def_default ""'

								# コマンド - フェードイン
								case 'fadein':
									line = ''
									fadein_arg0_1 = 'onstmp'
									fadein_arg1_1 = '5'
									fadein_arg2_1 = ''
									fadein_arg3_1 = ''
									
									for arg in command_arg:
										fadein_arg0 = re.match(r'<([a-z0-9_-]+)>', arg)
										fadein_arg1 = re.match(r'\[([0-9]+)\]', arg)
										fadein_arg2 = re.match(r'"(.+)"', arg)
										fadein_arg3 = re.match(r"'(.+)'", arg)#gauss

										if fadein_arg0: fadein_arg0_1 = fadein_arg0.group(1)
										if fadein_arg1: fadein_arg1_1 = fadein_arg1.group(1)
										if fadein_arg2: fadein_arg2_1 = fadein_arg2.group(1)
										if fadein_arg3: fadein_arg3_1 = fadein_arg3.group(1)
									
									if (fadein_arg2_1 and fadein_arg3_1):
										gauss_img_list.append(Path(fadein_arg2_1))
										fadein_arg2_1l = fadein_arg2_1.split('.')
										fadein_arg2_1 = f'{fadein_arg2_1l[0]}_gauss.{fadein_arg2_1l[1]}'
									
									s1, effect_startnum, effect_list = effect_edit(str(int(int(fadein_arg1_1)*10)), 'fade', effect_startnum, effect_list)

									if fadein_arg2_1:
										line = f'def_read "{fadein_arg0_1}","{fadein_arg2_1}":'

									if (fadein_arg0_1 in ['bg', 'cg']):							
										line += f'vsp val_chr_1,0:vsp val_chr_2,0:bg $val_{fadein_arg0_1},{s1}'
									else:
										line += f'lsp val_{fadein_arg0_1}, $val_{fadein_arg0_1},%{fadein_arg0_1}x,%{fadein_arg0_1}y:print {s1}'

								# コマンド - 白フェードイン
								case 'whitefadein':
									line = ''
									fadein_arg0_1 = 'bg'#事故りそうなので念の為bg(本当はonstmpから都度読むのが正解)
									fadein_arg1_1 = '5'
									fadein_arg2_1 = ''
									
									for arg in command_arg:
										fadein_arg0 = re.match(r'<([a-z0-9_-]+)>', arg)
										fadein_arg1 = re.match(r'\[([0-9]+)\]', arg)
										fadein_arg2 = re.match(r'"(.+)"', arg)

										if fadein_arg0: fadein_arg0_1 = fadein_arg0.group(1)
										if fadein_arg1: fadein_arg1_1 = fadein_arg1.group(1)
										if fadein_arg2: fadein_arg2_1 = fadein_arg2.group(1)
									
									s1, effect_startnum, effect_list = effect_edit(str(int(int(fadein_arg1_1)*10)), 'fade', effect_startnum, effect_list)

									if fadein_arg2_1:
										line = f'def_read "{fadein_arg0_1}","{fadein_arg2_1}"\n'

									if (fadein_arg0_1 in ['bg', 'cg', 'base']):							
										line += f'bg white,{s1}:bg $val_{fadein_arg0_1},{s1}'#ここ以外fadeinと一緒
									else:
										line += f'lsp val_{fadein_arg0_1}, $val_{fadein_arg0_1},%{fadein_arg0_1}x,%{fadein_arg0_1}y:print {s1}'
										
								# コマンド - フェードアウト
								case 'fadeout':
									line = ''
									fadeout_arg0_1 = 'onstmp'
									fadeout_arg1_1 = '5'
									fadeout_arg2_1 = ''
									fadeout_arg3_1 = ''
									
									for arg in command_arg:
										fadeout_arg0 = re.match(r'<([a-z0-9_-]+)>', arg)
										fadeout_arg1 = re.match(r'\[([0-9]+)\]', arg)
										fadeout_arg2 = re.match(r'"(.+)"', arg)
										fadeout_arg3 = re.match(r'\(([0-9]+,[0-9]+)\)', arg)

										if fadeout_arg0: fadeout_arg0_1 = fadeout_arg0.group(1)
										if fadeout_arg1: fadeout_arg1_1 = fadeout_arg1.group(1)
										if fadeout_arg2: fadeout_arg2_1 = fadeout_arg2.group(1)
										if fadeout_arg3: fadeout_arg3_1 = fadeout_arg3.group(1)
									
									s1, effect_startnum, effect_list = effect_edit(str(int(int(fadeout_arg1_1)*10)), 'fade', effect_startnum, effect_list)

									if fadeout_arg2_1:
										line = f'def_read "{fadeout_arg0_1}","{fadeout_arg2_1}"\n'

									if (fadeout_arg0_1 in ['bg', 'cg']):							
										line += f'vsp val_chr_1,0:vsp val_chr_2,0:bg black,{s1}'
									else:
										line += f'vsp val_chr_1,0:vsp val_chr_2,0:vsp val_{fadeout_arg0_1},0'
										if fadeout_arg3_1: line += f'msp val_{fadeout_arg0_1},{fadeout_arg3_1}'
										line += f':print {s1}'
								
								# コマンド - 白フェードアウト
								case 'whitefadeout':
									line = ''
									fadeout_arg0_1 = 'bg'#事故りそうなので念の為bg(本当はonstmpから都度読むのが正解)
									fadeout_arg1_1 = '5'
									fadeout_arg2_1 = ''
									fadeout_arg3_1 = ''
									
									for arg in command_arg:
										fadeout_arg0 = re.match(r'<([a-z0-9_-]+)>', arg)
										fadeout_arg1 = re.match(r'\[([0-9]+)\]', arg)
										fadeout_arg2 = re.match(r'"(.+)"', arg)
										fadeout_arg3 = re.match(r'\(([0-9]+,[0-9]+)\)', arg)

										if fadeout_arg0: fadeout_arg0_1 = fadeout_arg0.group(1)
										if fadeout_arg1: fadeout_arg1_1 = fadeout_arg1.group(1)
										if fadeout_arg2: fadeout_arg2_1 = fadeout_arg2.group(1)
										if fadeout_arg3: fadeout_arg3_1 = fadeout_arg3.group(1)
									
									s1, effect_startnum, effect_list = effect_edit(str(int(int(fadeout_arg1_1)*10)), 'fade', effect_startnum, effect_list)

									if fadeout_arg2_1:
										line = f'def_read "{fadeout_arg0_1}","{fadeout_arg2_1}"\n'

									if (fadeout_arg0_1 in ['bg', 'cg']):							
										line += f'vsp val_chr_1,0:vsp val_chr_2,0:bg white,{s1}'#ここ以外fadeoutと一緒
									else:
										line += f'vsp val_{fadeout_arg0_1},0:print 10'
										if fadeout_arg3_1: line += f'msp val_{fadeout_arg0_1},{fadeout_arg3_1}'
										line += f':print {s1}'

								# コマンド - 白(フラッシュ扱いで)
								case 'white':
									# bgの裏のbaseいじるのが正解っぽいけど今さら変えられないので誤魔化す

									#fadeout_arg0_1 = re.match(r'<([a-z0-9_-]+)>', command_arg[0]).group(1)
									s1, effect_startnum, effect_list = effect_edit(str(50), 'fade', effect_startnum, effect_list)
									line = f'lsp 1,"bg/white.png",0,0:print {s1}:wait 50:csp 1:print {s1}'#一瞬白塗り

								# コマンド - 黒
								case 'black':
									black_arg0_1 = re.match(r'<([a-z0-9_-]+)>', command_arg[0]).group(1)
									if (black_arg0_1 in ['bg', 'cg']):
										line = f'vsp val_chr_1,0:vsp val_chr_2,0:bg black,10'#手抜き
									else:
										line = f';{line}'

								# コマンド - 表示削除
								case 'dispoff':
									#line = f';{line}'
									dispoff_arg0_1 = re.match(r'<([a-z0-9_-]+)>', command_arg[0]).group(1)
									if (dispoff_arg0_1 in ['bg', 'cg']):
										line = f'vsp val_chr_1,0:vsp val_chr_2,0:bg black,10'
									else:
										line = f'vsp val_{dispoff_arg0_1},0:print 10'

								# コマンド - 表示
								case 'dispon':
									dispon_arg0_1 = 'bg'
									
									for arg in command_arg:
										dispon_arg0 = re.match(r'<([a-z0-9_-]+)>', arg)
										if dispon_arg0: dispon_arg0_1 = dispon_arg0.group(1)

									if (dispon_arg0_1 in ['bg', 'cg']):
										line = f'vsp val_chr_1,0:vsp val_chr_2,0:bg $val_bg,10'
									else:
										line = f'vsp val_{dispon_arg0_1},0:print 10'

								# コマンド - 暗転?
								case 'exfadeout':
									s1, effect_startnum, effect_list = effect_edit(str(50), 'fade', effect_startnum, effect_list)
									line = f'bg black,{s1}'#:print {s1}'#一瞬黒塗り
								
								# コマンド - 立ち絵出現
								case 'chrin':
									#/chrin  (right) <chr_2> "stand\０５コハク巫女＿嘆願.tga"
									chrin_arg0_1 = 'center'
									chrin_arg1_1 = ''
									chrin_arg2_1 = ''

									for arg in command_arg:
										chrin_arg0 = re.match(r'\(([a-z0-9_-]+)\)', arg)
										chrin_arg1 = re.match(r'<([a-z0-9_-]+)>', arg)
										chrin_arg2 = re.match(r'"(.+)"', arg)

										if chrin_arg0: chrin_arg0_1 = chrin_arg0.group(1)
										if chrin_arg1: chrin_arg1_1 = chrin_arg1.group(1)
										if chrin_arg2: chrin_arg2_1 = chrin_arg2.group(1)

									line = f'def_read "{chrin_arg1_1}","{chrin_arg2_1}":'+\
										f'def_chrin "{chrin_arg0_1}","{chrin_arg1_1}"'

								# コマンド - 立ち絵消す
								case 'chrout':
									chrout_arg0_1 = re.match(r'<([a-z0-9_-]+)>', command_arg[0]).group(1) if (command_arg) else ''
									if (chrout_arg0_1):
										line = f'vsp val_{chrout_arg0_1},0:print 10'
									else:
										line = f'vsp val_chr_1,0:vsp val_chr_2,0:print 10'

								# コマンド - 全フェードアウト
								case 'allfadeout':
									line = f'vsp val_chr_1,0:vsp val_chr_2,0:bg black,10'#本当は一部秒数指定っぽいのあったけど無視

								# コマンド - 立ち絵変更
								case 'change':
									change_arg0_1 = ''
									change_arg1_1 = ''

									for arg in command_arg:
										change_arg0 = re.match(r'<([a-z0-9_-]+)>', arg)
										change_arg1 = re.match(r'"(.+)"', arg)

										if change_arg0: change_arg0_1 = change_arg0.group(1)
										if change_arg1: change_arg1_1 = change_arg1.group(1)
									
									line = f'def_read "{change_arg0_1}","{change_arg1_1}":'+\
										f'def_change "{change_arg0_1}","{change_arg1_1}"'
										#f'getspsize val_{change_arg0_1},%1,%2:lsp val_{change_arg0_1},"{change_arg1_1}",0,0:print 1'
										
								# コマンド - 座標セット
								case 'setpos':
									setpos_arg0_1 = ''
									setpos_arg1_1 = ''
									setpos_arg2_1 = ''
									for arg in command_arg:
										setpos_arg0 = re.match(r'<([a-z0-9_-]+)>', arg)
										setpos_arg1 = re.match(r'\(([a-z0-9_-]+|([0-9]+),([0-9]+))\)', arg)
										setpos_arg2 = re.match(r'"(.+)"', arg)

										if setpos_arg0: setpos_arg0_1 = setpos_arg0.group(1)
										if setpos_arg1: setpos_arg1_1 = setpos_arg1.group(1)
										if setpos_arg2: setpos_arg2_1 = setpos_arg2.group(1)

									if (r',' in setpos_arg1_1):
										i,j = setpos_arg1_1.split(',')
										line = f'def_setpos_int "{setpos_arg0_1}",{int(i)},{int(j)}'
									else:
										line = f'def_setpos "{setpos_arg0_1}","{setpos_arg1_1}"'

									if setpos_arg2_1:
										line = f'def_read "{setpos_arg0_1}","{setpos_arg2_1}":{line}'

								# コマンド - 背景遷移らしきもの
								case 'disolve':
									line = ''
									disolve_arg0_1 = 'onstmp'
									disolve_arg1_1 = ''
									disolve_arg2_1 = ''
									
									for arg in command_arg:
										disolve_arg0 = re.match(r'<([a-z0-9_-]+)>', arg)
										disolve_arg1 = re.match(r'"(.+)"', arg)
										disolve_arg2 = re.match(r"'(.+)'", arg)#'gauss'

										if disolve_arg0: disolve_arg0_1 = disolve_arg0.group(1)
										if disolve_arg1: disolve_arg1_1 = disolve_arg1.group(1)
										if disolve_arg2: disolve_arg2_1 = disolve_arg2.group(1)
									
									if (disolve_arg1_1 and disolve_arg2_1):
										gauss_img_list.append(Path(disolve_arg1_1))
										disolve_arg1_1l = disolve_arg1_1.split('.')
										disolve_arg1_1 = f'{disolve_arg1_1l[0]}_gauss.{disolve_arg1_1l[1]}'
									
									s1, effect_startnum, effect_list = effect_edit('500', 'fade', effect_startnum, effect_list)

									if disolve_arg1_1:
										line = f'def_read "{disolve_arg0_1}","{disolve_arg1_1}"'

									if (disolve_arg0_1 in ['bg', 'cg']):							
										line = f'{line}:vsp val_chr_1,0:vsp val_chr_2,0:bg $val_{disolve_arg0_1},{s1}'
									else:
										raise Exception(line)

								# コマンド - セット
								case 'aliasset':
									aliasset_arg1_1 = f'${re.fullmatch(r'\'([a-z0-9_-]+)\'', command_arg[1]).group(1)}'
									aliasset_arg2_1 = re.fullmatch(r'"(.+)"', command_arg[2]).group(1)
									line = f'mov {d2sa(aliasset_arg1_1)},"{aliasset_arg2_1}"'

									if (not d2sa(aliasset_arg1_1) in val_list) and (not re.fullmatch(r'[0-9]*', d2sa(aliasset_arg1_1))): val_list.append(d2sa(aliasset_arg1_1))

								# コマンド - 座標移動(特殊)
								case 'movepos':
									setpos_arg1 = re.match(r'\((([0-9]+),([0-9]+))\)', command_arg[0]).group(1)
									line = f'lsp val_onstmp,$val_def_default,{setpos_arg1}:print 9'

								# コマンド - 透過?
								case 'alpha':
									alpha_arg0_1 = re.match(r'<([a-z0-9_-]+)>', command_arg[0]).group(1)
									alpha_arg1_1 = re.match(r'\[([a-z0-9_-]+)\]', command_arg[1]).group(1)
									line = f'def_alpha "{alpha_arg0_1}",{alpha_arg1_1}'

								# コマンド - 動画
								case 'movie':
									movie_arg0_1 = re.match(r'"(.+)"', command_arg[0]).group(1)
									line = f'skipoff:stop:mpegplay "{movie_arg0_1}",1'
									if debug: line = f';{line}'#デバッグモード時飛ばす


								# コマンド - bgm再生
								case 'bgmplay':
									bgmplay_arg0_1 = re.match(r'\[([0-9]+)\]', command_arg[0]).group(1)
									line = f'bgm "BGM/M{bgmplay_arg0_1}.WAV"'
								
								# コマンド - bgm停止
								case 'bgmstop':
									line = 'bgmstop'

								# コマンド - bgmゆっくり停止
								case 'bgmfade':
									line = 'bgmstop'#めんどいので即終了

								# コマンド - 効果音再生
								case 'seplay':
									seplay_arg0_1 = re.match(r'\[([0-9]+)\]', command_arg[0]).group(1)
									line = f'dwave 1,"SE/SE_{seplay_arg0_1}.wav"'

								# コマンド - 効果音停止
								case 'sestop':
									line = 'dwavestop 1'

								# コマンド - 効果音ゆっくり停止
								case 'sefade':
									line = 'dwavestop 1'#めんどいので即終了

								# コマンド - 効果音繰り返し
								case 'seloop':
									seloop_arg0_1 = re.match(r'\[([0-9]+)\]', command_arg[0]).group(1)
									line = f'dwaveloop 1,"SE/SE_{seloop_arg0_1}.wav"'

								# コマンド - 効果音2再生
								case 'soundplay':
									soundplay_arg1_1 = re.match(r'\[([0-9]+)\]', command_arg[1]).group(1)
									line = f'dwave 2,"SE/SE_{soundplay_arg1_1}.wav"'

								# コマンド - 効果音2ゆっくり再生
								case 'soundfadein':
									
									soundfadein_arg1_1 = ''

									try: soundfadein_arg1_1 = re.match(r'\[([0-9]+)\]', command_arg[1]).group(1)
									except: pass

									if soundfadein_arg1_1:
										line = f'dwave 2,"SE/SE_{soundfadein_arg1_1}.wav"'#めんどいので即開始
									else:
										line = f';{line}'

								# コマンド - 効果音2停止
								case 'soundstop':
									line = 'dwavestop 2'

								# コマンド - 効果音2ゆっくり停止?
								case 'soundfadeout':
									line = 'dwavestop 2'#めんどいので即終了

								# コマンド - 音量調整
								case 'bgmvolume':
									bgmvolume_arg1_1 = '100'
									
									for arg in command_arg:
										bgmvolume_arg1 = re.match(r'\[([0-9]+)\]', arg)

										if bgmvolume_arg1: bgmvolume_arg1_1 = bgmvolume_arg1.group(1)
									
									line = f'bgmvol {bgmvolume_arg1_1}*%aud_bgm/100'

								# コマンド - 音量調整
								case 'soundvolume':
									line = 'wait 0'
									soundvolume_arg1_1 = ''
									soundvolume_arg2_1 = ''
									for arg in command_arg:
										soundvolume_arg1 = re.match(r'<([a-z0-9_-]+)>', arg)
										soundvolume_arg2 = re.match(r'\[([0-9]+)\]', arg)

										if soundvolume_arg1: soundvolume_arg1_1 = soundvolume_arg1.group(1)
										if soundvolume_arg2: soundvolume_arg2_1 = soundvolume_arg2.group(1)
									
									if (soundvolume_arg1_1 == 'bgm') or (soundvolume_arg1_1 == 'env'):
										line += f':bgmvol {soundvolume_arg2_1}*%aud_bgm/100'
									if (soundvolume_arg1_1 == 'se') or (soundvolume_arg1_1 == 'env'):
										line += f':sevol {soundvolume_arg2_1}*%aud_se/100'
									if (soundvolume_arg1_1 == 'voice') or (soundvolume_arg1_1 == 'env'):
										line += f':voicevol {soundvolume_arg2_1}*%aud_vo/100'

								# コマンド - 終了して戻る
								case 'end':
									line = 'return'

								# コマンド - 上記のもの以外(=未実装)
								case _:

									# 未実装のまま無視しても良さそうなやつあったら書く
									ignore_command_list = [
										'init', #変数宣言?
										'initall', #変数宣言?2
										'bglock', #背景固定? 一箇所しか使われてない
										'aliasinit', #aliasset前の宣言?
										'sysget', #グローバル変数(みたいなもの)取得? 開始前クリアチェックに使ってるっぽい
										'fadewait', #画面転換待ち? onsは初めから待つ仕様なので無視
										'sefadein', #少しずつ効果音再生? 一回しか使われてないので無視
									]

									# 未実装コマンドリストに無いなら追加
									if (not command in skip_command_list) and (not command in ignore_command_list):
										skip_command_list.append(command)
									
									# 事故防止のためコメントアウト
									line = f';{line}'

						# 元々の行末コメントアウトを元に戻す
						if comment: line += f'\t;{comment}'

					# 行頭 - ラベル / ONS用に変換(元々英数字のみ&行にコメント無しなのでこんな雑実装でおｋ)
					case '#': line = f'*LABEL_{scxfilename}_{line[1:]}'

					# 行頭 - コメントアウト / コンバータ側で作ったコメントアウトと区別するために;増量
					case ';': line = f';;;;{line}'
						
					# 行頭 - それ以外  / そのまま
					case _: pass

				# テキストに書込み
				txt += f'{line}\n'
				
		# デバッグモード時
		if debug:

			# if_listとend_listのカウントが上手くいってない時にエラーを表示
			if if_list: print(f'\nif_listエラー:\n{if_list}')
			if end_list: print(f'\nend_listエラー:\n{end_list}')

	# エンディングファイルの読み込み
	end_str_list = []
	with open(Path(PATH_DICT['scx'] / 'S_ENDROLL.scx'), 'r', encoding='cp932') as f:

		# 1行ずつ文字列読み込み
		for line in f.readlines():
			line = line.replace('\n', '')
			if (line) and (not line[0] in ['#', ';', '/']):
				end_str_list.append(line)

	# numalias作成用文字列val_txt作成
	val_txt = ''
	for i,val in enumerate(val_list, 500):
		val_txt += f'numalias {val[1:]},{i}\n'#頭の%取る
	
	# エフェクト定義用の配列を命令文に&置換
	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1): add0txt_effect += f'effect {i},10,{e[0]}\n'
	
	# default.txtを(今さら)読み込み
	txt = default_txt(txt, val_txt, add0txt_effect, end_str_list)

	# お手軽置換手抜き修正
	txt = txt.replace(r'.tga', r'.png')#拡張子1
	txt = txt.replace(r'.bmp', r'.png')#拡張子2
	txt = txt.replace(r'$name', r'元樹')#主人公名前
	txt = txt.replace(r'lsp val_onstmp,$val_def_default,75,280:print 9', r'')#END直後のテロップが複数回出るのを治す
	txt = txt.replace(r'lsp val_onstmp,$val_def_default,75,260:print 9',
					r'lsp val_onstmp,$val_def_default,75,260:print 10:wait 3000')#END直後のテロップが一瞬で消えるのを防ぐ
	txt = txt.replace(r'''lsp 1,"bg/white.png",0,0:print 11:wait 50:csp 1:print 11
vsp val_chr_1,0:vsp val_chr_2,0:bg black,10
vsp val_chr_1,0:vsp val_chr_2,0:bg $val_bg,12''',
					r'lsp 1,"bg/white.png",0,0:print 11:wait 50:csp 1:print 11')#変換ミスで生まれたフラッシュ直後の暗転(?)を消す

	# 0.txt書込み
	with open(Path(PATH_DICT2['0.txt']), 'w', encoding='cp932') as f: f.write(txt)

	# デバッグモード時
	if debug:

		# 未実装コマンドリストを表示
		if skip_command_list: print(f'\n以下のコマンドが未実装です:\n{skip_command_list}')

		# ガウス画像リストを表示
		# print(f'ガウス画像リスト:{gauss_img_list}\n')

		# 使われている変数リストを表示
		# print(f'\n以下の変数が使われています:\n{val_list}')

		# エンディングファイルの文字列リストを表示
		# print(f'\nエンディングファイルの文字列リスト({len(end_str_list)}):\n{end_str_list}\n')

	# 関数終了
	return gauss_img_list


# メイン処理関数 ※pre_converted_dir→今までのコンバータのsame_hierarchy
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	# デバッグモード(_testディレクトリの有無で判断)
	debug = Path('./_test').is_dir()

	# マルチコンバータ利用時自動展開&デバッグモード強制解除
	if values: extract_resource(values, values_ex, pre_converted_dir); debug=0

	# デバッグモード時はリソース取得や0.txt作成を_testディレクトリ直下で行う
	if debug: pre_converted_dir /= '_test'

	# 先に準備しておくべきファイル一覧
	PATH_DICT = {}
	for key in ['BGM', 'SE', 'bg', 'cg', 'obj', 'scx', 'stand', 'voice', 'opening.mpg']: PATH_DICT[key] = Path(pre_converted_dir / key)

	# 変換後に出力されるファイル一覧
	PATH_DICT2 = { '0.txt': Path(pre_converted_dir / '0.txt') }

	# ファイル/ディレクトリの存在チェック
	file_check(PATH_DICT)

	# シナリオ変換処理
	gauss_img_list = text_cnv(debug, PATH_DICT, PATH_DICT2)

	# 画像編集処理
	image_processing(PATH_DICT, gauss_img_list, pre_converted_dir)

	# 非デバッグモード時元シナリオ削除
	if not debug: shutil.rmtree(PATH_DICT['scx'])
	
	# 終了
	return


# 単体動作 (事前にリソース手動展開必須)
if __name__ == "__main__":
	main()
	