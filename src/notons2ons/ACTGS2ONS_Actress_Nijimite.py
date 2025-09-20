#!/usr/bin/env python3
from pathlib import Path
import concurrent.futures
import configparser, soundfile, shutil, glob, re, os

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'ACTRESS',
		'date': 20041029,
		'title': '虹を見つけたら教えて。',
		'cli_arg': 'actress_nijimite',
		'requiredsoft': [],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),
		'exe_name': ['ACTGS'],

		'version': [
			'虹を見つけたら教えて。 FANZA DL版(actress_0012)',
		],

		'notes': [
			'画面特殊効果全般の実装が不完全 (結構重要なんですが)雨が一切降りません',
			'一部BADエンドに入れないかも(通常エンドは動作確認済みです)',
			'セーブ/ロード画面は超簡略化',
			'立ち絵の表示順が一部違う',
			'CG/回想モードは未実装 (EXTRAはとりあえずOPを流せるようになってます)',
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro # type: ignore

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	for file_name in ['ACTGS.ini', 'Ending.dat', 'Ending1.dat', 'Ending2.dat', 'Ending3.dat', 'Ending4.dat', 'NijiOp.mpg']:
		p = Path(input_dir / file_name)
		
		#なければ強制エラー
		if not p.exists(): raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))
		
		shutil.copy(p, pre_converted_dir)

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for arc_name in ['Arc.cg', 'Arc.scr', 'Arc.wav']:
			p = Path(input_dir / arc_name)
			e = Path(pre_converted_dir / arc_name[4:])#"Arc."消す

			#なければ強制エラー
			if not p.exists(): raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))

			futures.append(executor.submit(extract_archive_garbro, p, e))
		
		concurrent.futures.as_completed(futures)

	#png変換展開時競合しそうなのを先に削除
	cg_outdir = Path(pre_converted_dir / 'cg')
	for p in cg_outdir.glob('*.bmp'):
		ps = p.with_suffix('.psd')
		if ps.exists(): ps.unlink()
	
	#(psd/bmpをGARbroに変換させるため)cgをzipに圧縮
	shutil.make_archive(cg_outdir, format='zip', root_dir=cg_outdir)
	shutil.rmtree(cg_outdir)

	#GARbro展開変換
	cg_outzip = Path(pre_converted_dir / 'cg.zip')
	extract_archive_garbro(cg_outzip, cg_outdir, 'png')
	cg_outzip.unlink()

	return


def default_txt():
	return ''';mode800
*define

caption "<<-TITLE->> for ONScripter"

rmenu "セーブ",save,"ロード",load,"スキップ",skip,"ログ",lookback,"リセット",reset
savename "ＳＡＶＥ","ＬＯＡＤ","ＤＡＴＡ"
savenumber 18
transmode alpha
globalon
rubyon
saveon
nsa
humanz 10
windowback

;なにこれ面倒くせぇ
pretextgosub *pretext_lb
defsub errmsg
defsub vo
defsub msg2
defsub cls
defsub se_wait
defsub random
defsub select_set
defsub select_reset
defsub select_start
defsub wait_def
defsub bg_def
defsub sp_def
defsub sp_fo
defsub fo
defsub bgm_fo
defsub bgm_stop
defsub sleep

effect 10,10,200

;<<-EFFECT->>

game
;----------------------------------------
*errmsg
	csp -1:print 1
	bg black,1
	
	Ｃｏｎｖｅｒｔ　Ｅｒｒｏｒ！@
	このメッセージが見れるのはおかしいよ@
	クリックでタイトルに戻ります…\\
return


*bgm_fo
	bgmfadeout 1000
	stop
	bgmfadeout 0
return


*sleep
	wait 1000
return


*bgm_stop
	stop
return

*vo
	getparam $0
	if $0=="" dwavestop 0
	if $0!="" dwave 0,"wav_dec\\" + $0 + ".wav"
	mov $10,""
return


*msg2
	getparam $10
return


*pretext_lb
	lsp 10,":s/26,26,0;#ffffff"+$10,33,495-5-26 ;名前の表示
return


*cls
	csp -1
return


*se_wait
	;旧ONSでSE待機は再現不可なので
	wait 2000
return


*random
	getparam %0
	rnd %41,%0
return


*select_set
	getparam $0
	
	if $21=="" mov $21,$0:goto *ssend
	if $21!="" if $22=="" mov $22,$0:goto *ssend
	if $21!="" if $22!="" if $23=="" mov $23,$0:goto *ssend
	if $21!="" if $22!="" if $23!="" if $24=="" mov $24,$0:goto *ssend
	if $21!="" if $22!="" if $23!="" if $24!="" if $25=="" mov $25,$0:goto *ssend
	*ssend
return


*select_reset
	mov $21,""
	mov $22,""
	mov $23,""
	mov $24,""
	mov $25,""
return


*select_start
	vsp 10,0:setwindow 60,60,27,6,26,26,0,50,20,0,0,#999999,50,50,749,549;ウィンドウselect用
	
	if $21=="NULL" mov $21,""
	if $22=="NULL" mov $22,""
	if $23=="NULL" mov $23,""
	if $24=="NULL" mov $24,""
	if $25=="NULL" mov $25,""
	
	if $21=="" if $22=="" if $23=="" if $24=="" if $25=="" goto *selskip
	select $21,*S1, $22,*S2, $23,*S3, $24,*S4, $25,*S5
	
	*S1
		mov $21,"":mov %40,1:goto *selskip
	*S2
		mov $22,"":mov %40,2:goto *selskip
	*S3
		mov $23,"":mov %40,3:goto *selskip
	*S4
		mov $24,"":mov %40,4:goto *selskip
	*S5
		mov $25,"":mov %40,5:goto *selskip
	
	*selskip
	setwindow 33,495,29,3,26,26,0,5,20,0,0,#999999,0,455,799,599;ウィンドウ汎用
return


*wait_def
	getparam %0
	wait %0*1000
return


*bg_def
	getparam $0,%0,$1,$2,$3
	vsp 15,0:vsp 16,0:vsp 17,0:vsp 10,0
	
	if %0==2 lsp 15,"cg\\"+$2+".png",   0,0
	if %0==3 lsp 16,"cg\\"+$2+".png",-180,0
	if %0==3 lsp 17,"cg\\"+$3+".png", 180,0
	
	erasetextwindow 1
	if $1=="" goto *nobg
	
	if %0!=0 if $0=="fi" bg "cg\\"+$1+".png",10
	if %0!=0 if $0==""   bg "cg\\"+$1+".png",1
	if %0==0 if $2=="FADE_SET" bg "cg\\"+$1+".png",10
	if %0==0 if $2!="FADE_SET" bg "cg\\"+$1+".png",1
	erasetextwindow 0
return
	*nobg
	
	if %0!=0 if $0=="fi" bg black,10
	if %0!=0 if $0==""   bg black,1
	if %0==0 if $2=="FADE_SET" bg black,10
	if %0==0 if $2!="FADE_SET" bg black,1
	erasetextwindow 0
return


*sp_def
	getparam $0,%0,$1,$2,$3
	vsp 15,0:vsp 16,0:vsp 17,0
	if $0=="fi" print 10
	
	if %0==1 lsp 15,"cg\\"+$1+".png",   0,0
	if %0==2 lsp 16,"cg\\"+$1+".png",-180,0:lsp 17,"cg\\"+$2+".png", 180,0
	if %0==3 lsp 15,"cg\\"+$1+".png",   0,0:lsp 16,"cg\\"+$2+".png",-180,0:lsp 17,"cg\\"+$3+".png", 180,0
	
	print 10
return


*sp_fo
	csp 0:csp 1:csp 2:csp 3:csp 4:csp 5:csp 6:csp 7:csp 8:csp 9
	print 10
return


*fo
	vsp 15,0:vsp 16,0:vsp 17,0
	bg black,10
return

;----------------------------------------
;[memo]
;数字変数
;	%0~%9 getparam汎用
;	%10 疑似ACTGS括弧再現用
;	%11 直近のselectが2か否か
;	%20 タイトル用btnwait
;	%21~%25 select用疑似配列(?)
;	
;	%40 S = 直前のセレクト 
;	%41 R = 直前のランダム 
;	%42 K = 直前の？？？？ - [KAISOU]	シーン回想用フラグかな(未確認)
;	%43 T = 直前の？？？？ - [TRIAL]	体験版かな(bg1_fi "_スペック" とかあるし)
;	%44 L = 直前の？？？？ - [LABEL]	シーン回想時の番号っぽい(1-5)
;	
;	%50~%199 ACTGS自動割り当て(通常)
;	%200~%?? ACTGS自動割り当て(グローバル)
;	
;文字変数
;	$0~$9 getparam汎用
;	$10 キャラ名前
;	
;スプライト
;	0~9 ACTGSスプライト
;	10 名前
;	11 _white
;	12 black
;	
;	15 立ち絵前
;	16 立ち絵右
;	17 立ち絵左
;	20~タイトル
;----------------------------------------
*start
setwindow 33,495,29,3,26,26,0,5,20,0,0,#999999,0,455,799,599;ウィンドウ汎用

goto *SCR_open
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
;----------------------------------------
*niji_title_menu

bgm "wav_dec\\BGM01.wav"

if %1000!=1 lsp 20,"cg\\_MnChara.png",0,0
if %1000==1 lsp 20,"cg\\_MnChara.png",0,0
if %1000!=1 bg "cg\\_MnBack.png",1
if %1000==1 bg "cg\\_MnBack5.png",1

lsp 30,"cg\\_MnStart.png"  ,75, 84
lsp 31,"cg\\_MnCont.png"   ,75,148
lsp 32,"cg\\_MnOmake.png"  ,75,212
lsp 33,"cg\\_MnOption.png" ,75,276
lsp 34,"cg\\_MnEnd.png"    ,75,340
lsp 35,"cg\\_MnStart.png"  ,75, 84,128
lsp 36,"cg\\_MnCont.png"   ,75,148,128
lsp 37,"cg\\_MnOmake.png"  ,75,212,128
lsp 38,"cg\\_MnOption.png" ,75,276,128
lsp 39,"cg\\_MnEnd.png"    ,75,340,128


print 1
*niji_title_loop
	bclear
	btrans
	
	exbtn_d "C30C31C32C33C34"
	exbtn 30,30,"P30C31C32C33C34"
	exbtn 31,31,"C30P31C32C33C34"
	exbtn 32,32,"C30C31P32C33C34"
	exbtn 33,33,"C30C31C32P33C34"
	exbtn 34,34,"C30C31C32C33P34"
	
	print 1
	btnwait %20
	if %20==30 csp -1:stop:erasetextwindow 0:goto *niji_title_menu_end
	if %20==31 csp -1:stop:bg "cg\\_MLLoadBack.png",10:systemcall load:bg black,10:goto *niji_title_menu
	if %20==32 csp -1:stop:bg black,10:mpegplay "NijiOp.mpg",1:goto *niji_title_menu
	if %20==33 csp -1:stop:bg black,10:goto *volmenu_GUI
	if %20==34 csp -1:stop:end
	
goto *niji_title_loop
;----------------------------------------
'''

def effect_edit(t,f,effect_list,effect_startnum):
	#global effect_list

	list_num=0
	if re.fullmatch(r'[0-9]+',t):#timeが数字のみ＝本処理

		for i, e in enumerate(effect_list,effect_startnum+1):#1からだと番号が競合する可能性あり
			if (e[0] == t) and (e[1] == f):
				list_num = i

		if not list_num:
			effect_list.append([t,f])
			list_num = len(effect_list) + effect_startnum

	return str(list_num),effect_list,effect_startnum


def str2var_v2(s, m, str2var_dict, str2var_cnt):
	if re.fullmatch(r'[0-9A-z-_]+?', s) and (m == 'filename'):#ファイル名かつ日本語なし
		s2 = s#変更不要
	else:
		#global str2var_dict
		#global str2var_cnt

		d=str2var_dict[m].get(s)#過去に変換済みかチェック
		
		if d:#変換済みの場合 - 要素をもってくる
			s2 = d
		else:#変換済みではない場合 - 新たに作成
			act_global = bool(re.fullmatch(r'F[0-9]{4}',s))#ACTGSでグローバル変数のばあい
			t = str2var_cnt[m]+(act_global*200)#200足す(≒ONSでもグローバルに)
			
			str2var_dict[m][s] = t
			s2 = t
			str2var_cnt[m] += 1
		
		#str型へ
		if (m == 'filename'):
			s2 = 'RENAMED__' + str(s2)
		else:
			s2 = str(s2)
	
	return s2, str2var_dict, str2var_cnt


def music_cnv_main(i, dp):
	soundfile.write(dp, soundfile.read(i)[0], soundfile.read(i)[1])
	return


def music_cnv(values_ex, DIR_WAV):
	#GARbro出力されたoggが何故か一部ちゃんと鳴らないので
	num_workers = values_ex.get('num_workers', os.cpu_count() + 4)
	d1 = glob.glob(os.path.join(DIR_WAV, '*.*'))

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for i in (d1):
			dd = (os.path.dirname(i) + '_dec')
			dp = (os.path.join(dd, os.path.splitext(os.path.basename(i))[0] + '.wav'))
			os.makedirs(dd, exist_ok=True)
			futures.append(executor.submit(music_cnv_main, i, dp))

		concurrent.futures.as_completed(futures)
		


def text_def(DIR_SCR, define_dict):
	for p in glob.glob(os.path.join(DIR_SCR, '*.scr')):
		with open(p, encoding='cp932', errors='ignore') as f:
			for line in f:
				define_line = re.match(r'define[\t\s]+(.+?)[\t\s]+"?([A-z0-9-_]+?)"?\n', line)
				if define_line: define_dict[ define_line[1] ] = define_line[2]
	
	return define_dict


def text_cnv(DIR_SCR, debug, same_hierarchy, str2var_cnt, define_dict, cfg_dict, gosub_list):
	#global gosub_list

	effect_startnum = 10
	effect_list = []

	str2var_dict = {
		'filename':{},
		'numalias':{
			'S':40,
			'R':41,
			'K':42,
			'T':43,
			'L':44,
		},
	}
	
	# with open(DEFAULT_TXT) as f:
	# 	txt = f.read()
	txt = default_txt()

	for p in sorted(glob.glob(os.path.join(DIR_SCR, '*.scr'))):

		with open(p, encoding='cp932', errors='ignore') as f:

			name = os.path.splitext(os.path.basename(p))[0]
			txt += '\nerrmsg:reset\n;--------------- '+ name +' ---------------\n*SCR_'+ name.replace('.', '_') +'\n\n'

			fr = f.read()
			fr = fr.replace(r'{','{\n').replace(r'}','\n}\n')#処理しやすいようにif文全部複数行跨ぎに
			fr = re.sub(r'\n([^0-9A-z\[\]]+?)\{\n([^0-9A-z\[\]]+?)\n\}\n', r'\n\1｛\2｝', fr)#↑の副作用修正
			
			for line in fr.splitlines():
				line = line.replace(r';', r'') + '\n'
				line = re.sub(r'[\t\s]*(.+?)[\t\s]*\n', r'\1\n', line)

				msg2_line = re.match(r'msg2[\t\s]+(.*)', line)
				gosub_line = re.match(r'\[[\t\s]*(.+?)[\t\s]*\][\t\s]*\{', line)
				goend_line = re.match(r'}', line)
				change_line = re.match(r'change[\t\s]+"(.*?)"', line)
				mov_line = re.match(r'([^=+-]+)[\t\s]*([=+-]+)[\t\s]*([^=+-]+?)(([+-])[\t\s]*([0-9]+?))?\n', line)
				movie_line = re.match(r'movie "(.[A-z0-9-_]+?)(\.[A-z]+?)?"', line)
				flash_line = re.match(r'flash[0-9] ', line)
				goto_line = re.match(r'goto[\t\s]+(.+?)\n', line)
				at_line = re.match(r'@(.+?)\n', line)
				defsel_line = re.match(r'def_sel[\t\s]+(.+?)\n', line)
				select_line = re.match(r'select(2)?[\t\s]+([0-9])', line)#select2割と不完全な実装です
				bg_line = re.match(r'bg([1-3])?(_fi)?[\t\s]+', line)
				sp_line = re.match(r'sp([1-3])(_fi|_cf)?[\t\s]+', line)
				sp0_line = re.match(r'sp[\t\s]+([0-9])[\t\s]+"(.*?)"[\t\s]+([A-z_]+)', line)
				ev1_line = re.match(r'ev1(_fi)?[\t\s]+"(.*?)"', line)
				ef2_line = re.match(r'ef2[\t\s]+"(.*?)"[\t\s]+"(.*?)"', line)
				shake_line = re.match(r'shake[\t\s]+([A-z0-9-_]+)', line)
				ev_line = re.match(r'ev[\t\s]+"(.*?)"[\t\s]+([A-z_]+)', line)
				bgm1_line = re.match(r'bgm1[\t\s]+"(.*?)"', line)
				se2_line = re.match(r'se2[\t\s]+([A-z0-9-_\"]+)', line)

				if re.match(r'se_wait', line):
					pass

				elif re.match(r'random ([0-9]+)', line):
					pass

				elif re.match(r'cls', line):
					pass

				elif re.match(r'ret', line):
					line = '\\\n'

				elif re.match(r'vo "(.*?)"', line):
					if debug:
						line = r';' + line

				elif re.match(r'fo', line):
					pass

				elif re.match(r'sp_fo', line):
					pass

				elif re.match(r'bgm_fo', line):
					pass

				elif re.match(r'bgm_stop', line):
					pass

				elif re.match(r'sleep', line):
					pass

				elif re.match(r'wait ', line):#これ関数で上書きしてx100くらいにしたほうがいいかも
					line = line.replace(r'wait', r'wait_def')

				elif re.match(r'title', line):
					line = 'reset\n'

				elif re.match(r'menu', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'def_cg', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'kaisou_end', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'flag_update', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'bg_effect', line):#コレ結構危うい
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'auto_ret_off', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'select_center_on', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'N', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'set_rgb', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'window(_on|_off)', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'window(_sel)? ', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'define[\t\s]+(.+?)[\t\s]+"?([A-z0-9-_]+?)"?\n', line):
					line = r';' + line#エラー防止の為コメントアウト

				elif re.match(r'blue_sky', line):#
					line = 'mov %1000,1\n'#クリアフラグらしきもの

				elif msg2_line:
					line = 'msg2 "' + msg2_line[1].replace(r'【', r'').replace(r'】', r'') + '"\n'
					if debug:
						line = r';' + line

				elif gosub_line:
					cntstr_g = str(str2var_cnt['gotocnt'])

					line = '\n\nmov %10,0\n'

					for x in gosub_line[1].split(r'|'):
						for y in x.split(r'&'):
							gosub_str = re.search(r'([^=><!]+)[\t\s]*([=><!]+)[\t\s]*([^=><!]+)', y)

							gosub_str_1_b = define_dict.get(gosub_str[1])
							gosub_str_3_b = define_dict.get(gosub_str[3])

							gosub_str_1_t = gosub_str_1_b if (not gosub_str_1_b == None) else gosub_str[1]
							gosub_str_3_t = gosub_str_3_b if (not gosub_str_3_b == None) else gosub_str[3]

							if (re.fullmatch(r'[0-9]+?', gosub_str_1_t)): gosub_str_1_r = gosub_str_1_t
							else:
								sv, str2var_dict, str2var_cnt = str2var_v2(gosub_str_1_t, 'numalias', str2var_dict, str2var_cnt)#対象1(F0000 or 定義済み変数)
								gosub_str_1_r = '%' + sv

							if (re.fullmatch(r'[0-9]+?', gosub_str_3_t)): gosub_str_3_r = gosub_str_3_t
							else:
								sv, str2var_dict, str2var_cnt = str2var_v2(gosub_str_3_t, 'numalias', str2var_dict, str2var_cnt)#対象2(F0000 or 定義済み変数)
								gosub_str_3_r= '%' + sv
							gosub_str_2_r = r'!=' if (gosub_str[2] == '!') else gosub_str[2]#比較

							line += 'if ' + gosub_str_1_r + gosub_str_2_r + gosub_str_3_r + ' '
							
						line += 'mov %10,1\n'

					line += '\nif %10==1 goto *IF_GOTO' + cntstr_g + '\n'
					line += '*IF_END' + cntstr_g + '\n'
					line += 'goto *IF_SKIP' + cntstr_g + '\n'
					line += '*IF_GOTO' + cntstr_g + '\n\n'

					gosub_list += [cntstr_g]
					str2var_cnt['gotocnt'] += 1

				elif goend_line:
					line = '\ngoto *IF_END' + gosub_list[-1] + '\n'
					line += '*IF_SKIP' + gosub_list[-1] + '\n'

					gosub_list = gosub_list[:-1]

				elif change_line:#別scrへ飛ぶ
					line = 'goto *SCR_' + change_line[1] + '\n'

				elif select_line:
					if (select_line[1] == '2'):
						pass#print('WARNING:"select2" used.')

					if (select_line[2] == '1'):
						line = 'select_start\n'
						line += 'select_reset\n'
					else:
						# print('WARNING:select args error!')
						line = r';' + line#エラー防止の為コメントアウト

				elif bg_line:#背景
					if (bg_line[2] == '_fi'):
						fade = '"fi"'
					else:
						fade = '""'

					if bg_line[1] == '1':
						bg1_line = re.match(r'bg1(_fi)?[\t\s]+"(.*?)"', line)
						n = '1'
						a1 = '"' + bg1_line[2] + '"'
						a2 = '""'
						a3 = '""'
					elif bg_line[1] == '2':
						bg2_line = re.match(r'bg2(_fi)?[\t\s]+"(.*?)"[\t\s]+"(.*?)"', line)
						n = '2'
						a1 = '"' + bg2_line[2] + '"'
						a2 = '"' + bg2_line[3] + '"'
						a3 = '""'
					elif bg_line[1] == '3':
						bg3_line = re.match(r'bg3(_fi)?[\t\s]+"(.*?)"[\t\s]+"(.*?)"[\t\s]+"(.*?)"', line)
						n = '3'
						a1 = '"' + bg3_line[2] + '"'
						a2 = '"' + bg3_line[3] + '"'
						a3 = '"' + bg3_line[4] + '"'
					else:
						bg0_line = re.match(r'bg[\t\s]+"(.*?)"[\t\s]+([A-z_]+)', line)
						n = '0'
						a1 = '"' + bg0_line[1] + '"'
						a2 = '"' + bg0_line[2] + '"'
						a3 = '""'

					line = 'bg_def ' + fade + ',' + n + ',' + a1 + ',' + a2 + ',' + a3 + '\n'

				elif sp_line:#立ち絵
					if (sp_line[2] == '_fi'):
						fade = '"fi"'
					if (sp_line[2] == '_cf'):
						fade = '"cf"'
					else:
						fade = '""'

					if sp_line[1] == '1':
						sp1_line = re.match(r'sp1(_fi|_cf)?[\t\s]+"(.*?)"', line)
						n = '1'
						a1 = '"' + sp1_line[2] + '"'
						a2 = '""'
						a3 = '""'
					elif sp_line[1] == '2':
						sp2_line = re.match(r'sp2(_fi|_cf)?[\t\s]+"(.*?)"[\t\s]+"(.*?)"', line)
						n = '2'
						a1 = '"' + sp2_line[2] + '"'
						a2 = '"' + sp2_line[3] + '"'
						a3 = '""'
					elif sp_line[1] == '3':
						sp3_line = re.match(r'sp3(_fi|_cf)?[\t\s]+"(.*?)"[\t\s]+"(.*?)"[\t\s]+"(.*?)"', line)
						n = '3'
						a1 = '"' + sp3_line[2] + '"'
						a2 = '"' + sp3_line[3] + '"'
						a3 = '"' + sp3_line[4] + '"'

					line = 'sp_def ' + fade + ',' + n + ',' + a1 + ',' + a2 + ',' + a3 + '\n'

				elif sp0_line:
					spi = 9 - int(sp0_line[1])
					line = 'lsp ' + str(spi) + ',"cg\\' + sp0_line[2] + '.png"\n'

					if sp0_line[3] == 'FADE_SET':
						line += 'print 10 ;sp0_mode\n'
					else:
						line += 'print 1 ;sp0_mode\n'

				elif mov_line:#window誤認のため対策を
					if (mov_line[2] == '='):
						mov_line_6_ = '' if (mov_line[6] == None) else mov_line[6]

						mov_line_1_b = define_dict.get(mov_line[1])
						mov_line_3_b = define_dict.get(mov_line[3])
						mov_line_6_b = define_dict.get(mov_line_6_)

						mov_line_1_t = mov_line_1_b if (not mov_line_1_b == None) else mov_line[1]
						mov_line_3_t = mov_line_3_b if (not mov_line_3_b == None) else mov_line[3]
						mov_line_6_t = mov_line_6_b if (not mov_line_6_b == None) else mov_line_6_

						if (re.fullmatch(r'[0-9]+?', mov_line_1_t)): mov_line_1_r = mov_line_1_t
						else:
							sv, str2var_dict, str2var_cnt = str2var_v2(mov_line_1_t, 'numalias', str2var_dict, str2var_cnt)
							mov_line_1_r = '%' + sv
						if (re.fullmatch(r'[0-9]+?', mov_line_3_t)): mov_line_3_r = mov_line_3_t
						else:
							sv, str2var_dict, str2var_cnt = str2var_v2(mov_line_3_t, 'numalias', str2var_dict, str2var_cnt)
							mov_line_3_r = '%' + sv

						if (re.fullmatch(r'[0-9]+?', mov_line_6_t)):
							mov_line_6_r = mov_line_6_t
						elif (mov_line_6_t == ''):
							mov_line_6_r = ''
						else:
							mov_line_6_r, str2var_dict, str2var_cnt = str2var_v2(mov_line_6_t, 'numalias', str2var_dict, str2var_cnt)

						mov_line_5_r = mov_line[5] if (not mov_line[5] == None) else ''

						line = 'mov ' + mov_line_1_r + ',' + mov_line_3_r + mov_line_5_r + mov_line_6_r + '\n'
					else:
						if debug:
							print('WARNING:mov set error!')
						line = r';' + line#エラー防止の為コメントアウト

				elif movie_line:
					ext = '.mpg' if (movie_line[2] == None) else movie_line[2]
					line = 'mpegplay "' + movie_line[1] + ext + '",1\n'

				elif flash_line:
					linedef = line
					line = ''
					for s in linedef.replace('\n', '').split(' '):
						if (not s[:5] == 'flash'):
							fl_time = str( int( float(s)*1000 ) )
							ef,effect_list,effect_startnum = effect_edit(fl_time, 'fade',effect_list,effect_startnum)
							line += 'lsp 11,"cg\\_White.png",0,0:print 1:csp 11:print ' + ef + '\n'

				elif goto_line:
					line = 'goto *SCR_' + name.replace('.', '_') + '_' + goto_line[1] + '\n'

				elif at_line:
					line = '*SCR_' + name.replace('.', '_') + '_' + at_line[1] + '\n'

				elif defsel_line:
					line = 'select_set "' + defsel_line[1] + '"\n'

				elif ev1_line:
					line = 'erasetextwindow 1:vsp 15,0:vsp 16,0:vsp 17,0:vsp 10,0:'
					if ev1_line[1] == '_fl':
						line += 'bg black,1:'
					
					line += 'bg "cg\\' + ev1_line[2] + '.png",10:erasetextwindow 0\n'
				
				elif ef2_line:
					ef,effect_list,effect_startnum = effect_edit('100', ef2_line[1],effect_list,effect_startnum)
					line = 'erasetextwindow 1:bg "cg\\' + ef2_line[2] + '.png",' + ef + ':erasetextwindow 0\n'

				elif shake_line:#振動(絶対原作と違う)
					if shake_line[1]=='SHAKE_1':
						line ='quake 4,200\n'
					elif shake_line[1]=='SHAKE_2':
						line ='quake 4,400\n'
					else:
						# print('WARNING:shake to quake convert error!')
						line = r';' + line#エラー防止の為コメントアウト	

				elif ev_line:		
					line += 'erasetextwindow 1:vsp 15,0:vsp 16,0:vsp 17,0:vsp 10,0:bg "cg\\' + ev_line[2] + '.png",'
					if ev_line[2] == 'FADE_SET':
						line += '10:'
					else:
						line += '1:'
					line += 'erasetextwindow 0\n'

				elif bgm1_line:
					line = 'bgm "wav_dec\\' + bgm1_line[1] + '.wav"\n'

				elif se2_line:
					line = 'dwave 1,"wav_dec\\' + se2_line[1].replace(r'"', r'') + '.wav"\n'

				elif ( not re.search(r'[0-9A-z-_]', line) ):#英語&記号なし = セリフ
					line = line.replace(r'!', r'！').replace(r'?', r'？').replace(r'･', r'・')
					if debug:
						line = r';' + line

				else:
					#print( line.replace('\n', '') )
					if debug:
						print('WARNING:not defined - ' + re.match(r'(@?[0-9A-z-_]+)',line)[1])
					line = r';' + line#エラー防止の為コメントアウト
					pass

				if debug:#選択肢動作確認のため演出系削除
					c = False
					for b in [bg_line, sp_line, sp0_line, flash_line, ev1_line, ef2_line, shake_line, bgm1_line, se2_line]:
						if b:#
							c = True
					if c:
						line = r';' + line

				txt += line

	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換
		if e[1] == 'fade':
			add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'
		else:
			add0txt_effect +='effect '+str(i)+',18,'+e[0]+',"cg\\'+str(e[1]).replace('"','')+'.png"\n'

	txt = txt.replace('\n\\', '\\')#￥直前の改行を削除(pretextgosub対策)
	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)
	txt = txt.replace(r'▲氏▲', cfg_dict['Family'])
	txt = txt.replace(r'●名●', cfg_dict['Name'])

	if re.search('NijiOp', txt):#にじみて専用
		txt = txt.replace(r'<<-TITLE->>', r'虹を見つけたら教えて。')
		txt = txt.replace('\n;menu\n', '\ngoto *niji_title_menu\n*niji_title_menu_end\n')

	open(os.path.join(same_hierarchy,'0.txt'), 'w', encoding='cp932', errors='ignore').write(txt)

	return str2var_cnt, define_dict, cfg_dict, gosub_list


def file_check(DIR_CG, DIR_SCR, DIR_WAV):
	c = True
	for p in [DIR_CG, DIR_SCR, DIR_WAV]:
		if not os.path.exists(p):
			# print(p+ ' is not found!')
			c = False
	
	return c


def cfg_file(same_hierarchy, cfg_dict):
	ini = glob.glob(os.path.join(same_hierarchy, '*.ini'))[0]
	config = configparser.ConfigParser()
	config.read(ini)
	cfg_dict['Name'] = config['User']['Name']
	cfg_dict['Family'] = config['User']['Family']
	os.remove(ini)

	return cfg_dict


def end_check(str2var_cnt, gosub_list):
	# ここtrueになったらACTGS→NSCの変数名変換限界です
	# (NSC側のグローバル変数ずらせばいいだけなんだけどね...)
	c = True
	if (str2var_cnt['numalias'] >= 200):
		# print('WARNING:global var convert error!')
		c = False

	# gosubがうまく対になってないときエラー
	if (gosub_list):
		#print('WARNING:gosub convert error!')
		c = False

	return c


def junk_del(same_hierarchy):
	shutil.rmtree(os.path.join(same_hierarchy, 'wav'))
	shutil.rmtree(os.path.join(same_hierarchy, 'scr'))
	#os.remove(DEFAULT_TXT)


# メイン関数
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)
	
	debug = 0

	same_hierarchy = str(pre_converted_dir)#(os.path.dirname(sys.argv[0]))#同一階層のパスを変数へ代入
	#DEFAULT_TXT = os.path.join(same_hierarchy,'default.txt')

	if debug:
		same_hierarchy = os.path.join(same_hierarchy,'actress_nijimite_EXT')#debug

	DIR_WAV = os.path.join(same_hierarchy,'WAV')
	DIR_SCR = os.path.join(same_hierarchy,'scr')
	DIR_CG = os.path.join(same_hierarchy,'cg')

	define_dict = {}
	cfg_dict = {}
	gosub_list = []

	str2var_cnt = {#0始まりNG! 最低1から
		'numalias':50,
		'filename':1,
		'gotocnt':1,
	}
	
	if file_check(DIR_CG, DIR_SCR, DIR_WAV):
		cfg_dict = cfg_file(same_hierarchy, cfg_dict)
		define_dict = text_def(DIR_SCR, define_dict)
		str2var_cnt, define_dict, cfg_dict, gosub_list = text_cnv(DIR_SCR, debug, same_hierarchy, str2var_cnt, define_dict, cfg_dict, gosub_list)
		if not debug: music_cnv(values_ex, DIR_WAV)
		if end_check(str2var_cnt, gosub_list): junk_del(same_hierarchy)


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()