#!/usr/bin/env python3
from pathlib import Path
import concurrent.futures
import subprocess as sp
import soundfile as sf
import shutil, re, os

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'raiL-soft',
		'date': 20080725,
		'title': '霞外籠逗留記',
		'requiredsoft': ['gscScriptCompAndDecompiler-cli'],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),

		'version': [
			'霞外籠逗留記 FANZA DL版(bpartner_0001)',
		],

		'notes': [
			'クリック待ちと改ページ待ちの構文の違いが不明だったので\n強制的にすべての文章が改ページ待ちの状態に',
			'上記仕様により画面におけるスペースが余る＆\n低解像度機種での文字潰れを防ぐため文字は原作より大きめ',
			'ONScripterの縦書き表示は安定性が低いため\n文字表示は横書き固定、また文字サイズも変更不可',
			'共通ルートの好感度調整が機能していないため、\n個別ルート分岐時の選択肢は何選んでも全開放',
			'その他セーブ/ロード画面は超簡略化\nCG/回想モードなどに関しても未実装',
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	movout_dir = Path(pre_converted_dir / 'mov')
	movout_dir.mkdir()

	for file_name in ['0002.mpg', '0003.mpg']:
		p = Path(input_dir / 'mov' / file_name)
		
		#なければ強制エラー
		if not p.exists(): raise ValueError(str(p)+' not found.')
		
		shutil.copy(p, movout_dir)

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for xfl_name in ['wav', 'voice', 'scr', 'grps', 'grpo_bu', 'grpo', 'grpe', 'bgm']:
			p = Path(input_dir / Path(xfl_name + '.xfl'))
			e = Path(pre_converted_dir / xfl_name)

			#なければ強制エラー
			if not p.exists(): raise ValueError(str(p)+' not found.')

			futures.append(executor.submit(extract_archive_garbro, p, e, 'png'))
		
		concurrent.futures.as_completed(futures)

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for xfl_name in ['1', '2', '3', '4', '5']:
			p = Path(pre_converted_dir / 'voice' / Path(xfl_name + '.xfl'))
			e = Path(pre_converted_dir / 'voice' / xfl_name)

			futures.append(executor.submit(extract_archive_garbro, p, e, 'png'))
		
		concurrent.futures.as_completed(futures)

	for xfl_name in ['1', '2', '3', '4', '5']:
		p = Path(pre_converted_dir / 'voice' / Path(xfl_name + '.xfl'))
		p.unlink()

	return


def default_txt():
	return ''';mode800
*define

caption "霞外籠逗留記 for ONScripter"

rmenu "セーブ",save,"ロード",load,"スキップ",skip,"ログ",lookback,"リセット",reset
savename "ＳＡＶＥ","ＬＯＡＤ","ＤＡＴＡ"
savenumber 18
transmode alpha
globalon
rubyon
nsa
humanz 10
windowback

effect 10,10,500
effect 11,10,1000

;エイリアス
numalias select_var,77
numalias select_cnt,78


;サブルーチン
pretextgosub *pretext_lb
defsub setwin_def
defsub RSC_MESSAGE
defsub RSC_select
defsub RSC_IMAGE_GET
defsub RSC_SPRITE
defsub RSC_BGM
defsub RSC_SE
defsub RSC_MOVIE

defsub RSC_select_chara
defsub RSC_select_chara2

defsub start_set
defsub bgmfadeout_def

game
;----------------------------------------
*pretext_lb
	if $10!="" dwave 0,"voice\\"+$10+".wav"
	mov $10,""
	saveon ;pretextgosub利用時最後にsaveon必須
return


*bgmfadeout_def
	getparam %177
	dwavestop 1
	bgmfadeout %177
	bgmstop
	bgmfadeout 0
return


*setwin_def
	getparam %20
	if %250==0 mov %150,5
	if %250==1 mov %150,145
	if %250==2 mov %150,290
	
	if %20==0 tateyoko %251:setwindow3 %150,  5,21,20,24,24,0,6,14,0,1,#999999,0,  0,799,599;ほんへ
	if %20==1 tateyoko 0   :setwindow3    5,477,21,20,24,24,0,5,40,0,1,#999999,0,470,799,599;選択肢
return


*RSC_MESSAGE
	getparam $10
	
	;取得した数字の桁数
	len %24,$10
	
	;0埋め
	for %0=0 to 3-%24
		mov $10,"0"+$20
	next
return


*RSC_select
	;mov %21,8011:mov %22,8012:mov %23,0
	
	setwin_def 1
	
	itoa $21,%21
	itoa $22,%22
	itoa $23,%23
	
	lsp 40 "grpo\\8000.png",66,131
	lsp 30 "grpo\\8002.png",66,131
	
	if %21==0 mov $31,""  :lsp 31 "grpo\\8001.png"   ,66+167        ,131
	if %21!=0 mov $31,"１":lsp 31 "grpo\\"+$21+".png",66+167        ,131:lsp 34,":s#FFFFFF１",66+167        ,101
	if %22==0 mov $32,""  :lsp 32 "grpo\\8002.png"   ,66+167+167    ,131
	if %22!=0 mov $32,"２":lsp 32 "grpo\\"+$22+".png",66+167+167    ,131:lsp 35,":s#FFFFFF２",66+167+167    ,101
	if %23==0 mov $33,""  :lsp 33 "grpo\\8001.png"   ,66+167+167+167,131
	if %23!=0 mov $33,"３":lsp 33 "grpo\\"+$23+".png",66+167+167+167,131:lsp 36,":s#FFFFFF３",66+167+167+167,101
	
	print 10
	
	select $31,*RSC_sel1,
	       $32,*RSC_sel2,
	       $33,*RSC_sel3
	
	;選択肢1/2のときはvar1/0で動く
	;選択肢1/2/3のときは知らん
	*RSC_sel1
		mov %select_var,1
		vsp 31,0
		print 10
	goto *RSC_selEND
	
	*RSC_sel2
		mov %select_var,0
		vsp 32,0
		print 10
	goto *RSC_selEND
	
	*RSC_sel3
		mov %select_var,9
		vsp 33,0
		print 10
	goto *RSC_selEND
	
	
	
	*RSC_selEND
	csp 30:csp 31:csp 32:csp 33:csp 34:csp 35:csp 36:csp 37:csp 38:csp 39:csp 40
	print 10
	setwin_def 0
	
return

*RSC_select_chara
	mov %select_cnt,0
	if %select_var==1 return *JUMP_7_1016_gsc
	if %select_var==0 return *JUMP_10_1016_gsc
	if %select_var==9 return *JUMP_9_1016_gsc
return


*RSC_select_chara2
	if %select_var==1 return *JUMP_5_0050_gsc
	if %select_var==0 return *JUMP_8_0050_gsc
	if %select_var==9 return *JUMP_9_0050_gsc
return


*RSC_IMAGE_GET
	getparam %20
	itoa $20,%20
	
	;取得した数字の桁数
	len %25,$20
	
	;0埋め
	for %0=0 to 3-%25
		mov $20,"0"+$20
	next
	
	if %20!=0 bg "grpe\\"+$20+".png",10
return


*RSC_SPRITE
	getparam %20
	itoa $20,%20
	
	;取得した数字の桁数
	len %25,$20
	
	;0埋め
	for %0=0 to 3-%25
		mov $20,"0"+$20
	next
	
	;中央表示
	lsph 50,"grpo_bu\\"+$20+".png",0,0
	getspsize 50,%11,%12
	amsp 50,400-(%11/2),0
	vsp 50,1
	
	print 10
return


*RSC_BGM
	getparam %20
	itoa $20,%20
	
	;取得した数字の桁数
	len %25,$20
	
	;0埋め
	for %0=0 to 1-%25
		mov $20,"0"+$20
	next
	
	;bgm逝ってるので一旦コメントアウト
	bgm "bgm\\Track"+$20+".wav"
return


*RSC_SE
	getparam %20
	itoa $20,%20
	
	;取得した数字の桁数
	len %25,$20
	
	;0埋め
	for %0=0 to 1-%25
		mov $20,"0"+$20
	next
	
	dwave 1,"wav\\"+$20+".wav"
return


*RSC_MOVIE
	getparam %20,%60
	itoa $20,%20
	
	;取得した数字の桁数
	len %25,$20
	
	;0埋め
	for %0=0 to 3-%25
		mov $20,"0"+$20
	next
	
	mpegplay "mov\\"+$20+".mpg",%79
	
	;クリア判定
	if %60==1 mov %211,1;令嬢
	if %60==2 mov %212,1;司書
	if %60==3 mov %213,1;法師
	if %60==4 mov %214,1;渡し守 - 抱く
	if %60==5 mov %215,1;渡し守 - 抱かない
	
return


*start_set
	bgmfadeout_def 300
	dwave 1,"wav\\0001.wav"
	csp -1
	bg black,11
return
;----------------------------------------
*start

;エンディングムービースキップ変数(デバッグ用)
;mov %79,1

bg black,1
mpegplay "mov\\0002.mpg",1

*title

bgm "bgm\\Track12.wav"
bg "grpe\\9001.png",11


if %211==1 if %212==1 if %213==1 mov %180,1

if %180==1 goto *watashimori_on
if %180!=1 goto *watashimori_off
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
*watashimori_on

lsp 41,"grpo\\9011.png",250,250
lsp 42,"grpo\\9017.png",200,250
lsp 43,"grpo\\9012.png",150,250
lsp 44,"grpo\\9111.png",100,250
lsp 45,"grpo\\9013.png", 50,250
lsp 46,"grpo\\9015.png",  0,250

lsp 51,"grpo\\9001.png",250,250
lsp 52,"grpo\\9007.png",200,250
lsp 53,"grpo\\9002.png",150,250
lsp 54,"grpo\\9101.png",100,250
lsp 55,"grpo\\9003.png", 50,250
lsp 56,"grpo\\9005.png",  0,250

print 1:goto *title_loop
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
*watashimori_off

lsp 41,"grpo\\9011.png",250,250
lsp 43,"grpo\\9012.png",200,250
lsp 44,"grpo\\9111.png",150,250
lsp 45,"grpo\\9013.png",100,250
lsp 46,"grpo\\9015.png", 50,250

lsp 51,"grpo\\9001.png",250,250
lsp 53,"grpo\\9002.png",200,250
lsp 54,"grpo\\9101.png",150,250
lsp 55,"grpo\\9003.png",100,250
lsp 56,"grpo\\9005.png", 50,250

print 1:goto *title_loop
;;;;;;;;;;;;;;;


*title_loop
	bclear
	btrans
	
	if %180==1 goto *watashimori_on_exbtn
	if %180!=1 goto *watashimori_off_exbtn
	
	*watashimori_on_exbtn
	exbtn_d     "C41C42C43C44C45C46"
	exbtn 41,41,"P41C42C43C44C45C46"
	exbtn 42,42,"C41P42C43C44C45C46"
	exbtn 43,43,"C41C42P43C44C45C46"
	exbtn 44,44,"C41C42C43P44C45C46"
	exbtn 45,45,"C41C42C43C44P45C46"
	exbtn 46,46,"C41C42C43C44C45P46"
	goto *end_exbtn
	
	*watashimori_off_exbtn
	exbtn_d     "C41C43C44C45C46"
	exbtn 41,41,"P41C43C44C45C46"
	exbtn 43,43,"C41P43C44C45C46"
	exbtn 44,44,"C41C43P44C45C46"
	exbtn 45,45,"C41C43C44P45C46"
	exbtn 46,46,"C41C43C44C45P46"
	goto *end_exbtn
	
	
	*end_exbtn
	print 1
	btnwait %50
	if %50==41 start_set:setwin_def 0:gosub *SCR_0050_gsc:goto *title
	if %50==42 start_set:setwin_def 0:gosub *SCR_0051_gsc:goto *title
	if %50==43 start_set:wait 500:bg #8474a4,10:systemcall load:bg black,10:goto *title
	if %50==44 start_set:gosub *movie_mode:goto *title
	if %50==45 start_set:goto *volmenu_GUI:goto *title
	if %50==46 start_set:wait 500:end
goto *title_loop


;----------------------------------------
*movie_mode
mpegplay "mov\\0002.mpg",1:click
if %211==1 mpegplay "mov\\0003.mpg",1:click:return
if %212==1 mpegplay "mov\\0003.mpg",1:click:return
if %213==1 mpegplay "mov\\0003.mpg",1:click:return
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
	
	lsp 140,":s;#FFFFFFＳＥ",             50,200
	lsp 141,":s;#FFFFFF#666666＜",       200,200
	lsp 142,$147,                        250,200
	lsp 143,":s;#FFFFFF#666666＞",       550,200
	lsp 144,":s;#FFFFFF#666666"+$142,    600,200
	
	lsp 145,":s;#FFFFFFＶＯＩＣＥ",       50,250
	lsp 146,":s;#FFFFFF#666666＜",       200,250
	lsp 147,$148,                        250,250
	lsp 148,":s;#FFFFFF#666666＞",       550,250
	lsp 149,":s;#FFFFFF#666666"+$143,    600,250
	
	lsp 150,":s;#FFFFFF文字位置",               50,300
	if %250==0 lsp 151,":s;#FFFFFF#666666左",  200,300
	if %250==1 lsp 151,":s;#FFFFFF#666666中央",200,300
	if %250==2 lsp 151,":s;#FFFFFF#666666右",  200,300
	
	lsp 155,":s;#FFFFFF文字表示",               50,350
	if %251==0 lsp 156,":s;#FFFFFF#666666横",  200,350
	if %251==1 lsp 156,":s;#FFFFFF#666666縦",  200,350
	
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
	spbtn 138,138
	
	spbtn 151,151
	spbtn 152,152
	spbtn 153,153
	spbtn 156,156
	spbtn 158,158
	
	;入力待ち
	btnwait %140
	
	if %140==131 bgmvol 100:sevol 100:voicevol 100:mov %250,0:mov %251,0
	if %140==132 csp -1:reset
	if %140==136 if %130!=  0 sub %130,10:bgmvol %130
	if %140==138 if %130!=100 add %130,10:bgmvol %130
	if %140==141 if %131!=  0 sub %131,10:sevol %131
	if %140==143 if %131!=100 add %131,10:sevol %131
	if %140==146 if %132!=  0 sub %132,10:voicevol %132
	if %140==148 if %132!=100 add %132,10:voicevol %132
	
	if %140==151 if %250==2 mov %250,0:wait 100:goto *volmenu_loop
	if %140==151 if %250==0 mov %250,1:wait 100:goto *volmenu_loop
	if %140==151 if %250==1 mov %250,2:wait 100:goto *volmenu_loop
	if %140==156 if %251==1 mov %251,0:wait 100:goto *volmenu_loop
	if %140==156 if %251==0 mov %251,1:wait 100:goto *volmenu_loop
	
goto *volmenu_loop
;----------ここまでdefault.txt----------
'''

# [!]SEVEN-BRIDGEコンバータに比べればまだ汎用性は考えてあるものの、それでも解析途中です
# これをそのまま他作品に使い回さないでください

# voiceディレクトリ内メモ
# 1.令嬢
# 2.司書
# 3.法師
# 4.渡し守
# 5.お手伝いさん


# ディレクトリの存在チェック関数
def dir_check(path_list):

	CHK = True
	for p in path_list:
		if not p.exists():
			print('ERROR: "' + str(p) + '" is not found!')
			CHK = False
			
	return CHK


# シナリオを平文にデコードする関数 - 本体
def text_dec_main(p, gsc_exe, ex_gsc, scr_dec, values_ex):
	if values_ex: from utils import subprocess_args
	#不要gscはここで除外
	if not (str(p.stem) in ex_gsc):
		#デコード処理(ライセンスとか面倒なのでsubprocessで、ネイティブで動かしたい人は勝手に作って)
		if values_ex: sp.run([str(gsc_exe), '-m', 'decompile', '-i', str(p)], shell=True, cwd=scr_dec , **subprocess_args(True))
		else: sp.run([str(gsc_exe), '-m', 'decompile', '-i', str(p)], shell=True, cwd=scr_dec )
	return


# シナリオを平文にデコードする関数
def text_dec(gsc_exe, scr, scr_dec, values_ex):
	num_workers = values_ex.get('num_workers', os.cpu_count() + 4)

	#デコード先のディレクトリを作成
	scr_dec.mkdir(parents=True, exist_ok=True)

	#gsc除外リスト作成 - kagerou専用
	ex_gsc = ['0000', '0001', '0040', '0099', '9999']

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:#シナリオデコード- マルチスレッドで高速化
		futures = []
		
		for p in scr.glob('*.gsc'):#gscをglob
			futures.append(executor.submit(text_dec_main, p, gsc_exe, ex_gsc, scr_dec, bool(values_ex)))
		
		concurrent.futures.as_completed(futures)

	#txt(さっきデコードしたやつ)をglob
	for p in scr.glob('*.txt'):

		#scr_decへ移動(Pathlibのrenameを利用)
		p_move = (scr_dec / p.name)
		p.rename(p_move)

	return


# 音楽変換関数 - 本体
def music_cnv_main(p):
	#wav化した際のパスを作成
	p_wav = p.with_suffix('.wav')

	#wavがまだない場合に限り処理
	if not p_wav.exists():
		
		#ogg読み込み
		sd = sf.read(p)

		#wavに変換
		sf.write(p_wav, sd[0], sd[1])

		#元のoggを削除
		p.unlink()


# 音楽変換関数
def sound_dec(decode_list, values_ex):
	num_workers = values_ex.get('num_workers', os.cpu_count() + 4)
	#リスト内のディレクトリパスでfor
	for d in decode_list:
	
		with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:#garbroで取り出した音源のヘッダが仕様怪しいのでsoundfile通してwavへ変換 - マルチスレッドで高速化
			futures = []

			#ディレクトリパス内のファイル一覧でfor
			for p in d.glob('**/*.ogg'):
				futures.append(executor.submit(music_cnv_main, p))
			
			concurrent.futures.as_completed(futures)
	return


# txt置換→0.txt出力関数
def text_cnv(DEBUG_MODE, zero_txt, scr_dec, path_dict_keys):

	#シナリオ文判定初期化
	mes_max = 0
	movie_cnt = 1

	#default.txtを読み込み
	# with open(default, encoding='cp932', errors='ignore') as f:
	# 	txt = f.read()
	txt = default_txt()

	#デコード済みtxtをforで回す
	for p in scr_dec.glob('*.txt'):

		#デコード済みtxtを読み込み
		with open(p, encoding='cp932', errors='ignore') as f:

			#デコード済みtxt一つごとに開始時改行&サブルーチン化
			if DEBUG_MODE:
				txt += '\n;--------------- '+ str(p.name) +' ---------------'
			txt += '\n*SCR_'+ str(p.stem).replace('.', '_') +'\n\n'

			#シナリオ文判定初期化
			line_message = False
			mes_cnt = 0

			for line in f:

				line_hash = re.search(r'#([A-z0-9]+?)\n', line)# "#xxxx~" みたいな命令文
				line_label = re.search(r'\@([0-9]+)', line)# "@(数字)" JUMPの飛び先 ラベル

				#前の行及び今の行のシナリオ文判定
				last_message = line_message
				line_message = False

				#空行 - そのまま放置
				if re.match('\n', line):
					pass

				#>-1とか - なんだろうこれ
				elif re.match(r'>', line):
					line = (';' + line) if DEBUG_MODE else ''

				#select命令
				elif re.match(r'select', line):
					line = 'RSC_select\n'

				#ディレクトリ名呼び出し系
				elif (line.replace('\n', '')) in path_dict_keys:
					line = (';' + line) if DEBUG_MODE else ''

				#命令文 - "last_hash"変数に保持
				elif line_hash:
					line = (';' + line) if DEBUG_MODE else ''
					last_hash = line_hash[1]

				#JUMPの飛び先はNSCのラベル仕様に置換
				elif line_label:
					line = ('*JUMP_' + line_label[1] + '_' + str(p.stem).replace('.', '_') +'\n')

				#命令文の次の行
				elif last_hash:

					#命令の引数(?)を配列に変換しconvert_listへ代入
					try:
						convert_list = eval(line.replace('\n', ''))
					except:
						convert_list = False

					#失敗した失敗した失敗した配列変換に失敗した
					if not convert_list:
						
						if (r'[]' in line):

							#IMAGE_SET スプライト除去(こいつ基本空配列なんで)
							if last_hash == 'IMAGE_SET':
								line = ('csp -1:print 10' + '\n')

						else:

							#空配列変換失敗はありがちなので除外
							print('CnvListErr:' + line.replace('\n', ''))

						if not (last_hash == 'IMAGE_SET'):
							line = (';' + line) if DEBUG_MODE else ''

					#MESSAGE メッセージ表示&ボイス
					elif last_hash == 'MESSAGE':

						#convert_listからボイスの有無を取得
						voice_num = convert_list[1]

						#あれば命令化、なければ無視 - kagerou専用
						if len(str(voice_num)) == 5:
							line = 'RSC_MESSAGE "' + str(voice_num)[0] + '\\' + str(voice_num)[1:] + '"\n'#最初の1桁がディレクトリ、残り4がファイル名
						else:
							line = (';' + line) if DEBUG_MODE else ''

					#PAUSE 待ち
					elif last_hash == 'PAUSE':

						#適正値は数字*100だが、それだと結構テンポ悪いので
						line = 'wait ' + str(convert_list[0] * 20) + '\n'

					#JUMP_UNLESS 飛び先指定(select直後)
					elif last_hash == 'JUMP_UNLESS':
						line = (r'mov %select_cnt,%select_var' + '\n')
						line+= (r'if %select_cnt==0 goto *JUMP_' + str(convert_list[0]) + '_' + str(p.stem).replace('.', '_') + '\n')
						line+= (r'if %select_cnt!=0 sub %select_cnt,1' + '\n')
					
					#JUMP 飛び先指定					
					elif last_hash == 'JUMP':
						line = (r'if %select_cnt==0 goto *JUMP_' + str(convert_list[0]) + '_' + str(p.stem).replace('.', '_') + '\n')
						line+= (r'if %select_cnt!=0 sub %select_cnt,1' + '\n')

					#READ_SCENARIO gosub的な
					elif last_hash == 'READ_SCENARIO':
						line = ('gosub *SCR_' + str(convert_list[1]) + '_gsc\n' )

					#15 select前画像決定部分
					elif last_hash == '15':
						line = ('mov %21,' + str(convert_list[2]) + ':mov %22,' + str(convert_list[3]) + ':mov %23,' + str(convert_list[4]) + '\n')

					#IMAGE_GET grpe 背景
					elif last_hash == 'IMAGE_GET':
						line = ('RSC_IMAGE_GET ' + str(convert_list[0]) + '\n')

					#SPRITE grpo_bu 立ち絵？
					elif last_hash == 'SPRITE':
						line = ('RSC_SPRITE ' + str(convert_list[2]) + '\n')

					#60 BGM？
					elif last_hash == '60':
						line = ('RSC_BGM ' + str(convert_list[0]) + '\n')

					#62 効果音？
					elif last_hash == '62':
						line = ('RSC_SE ' + str(convert_list[0]) + '\n')

					#36 スプライト除去
					elif last_hash == '36':
						line = ('csp -1' + '\n')

					# (多分)暗転
					elif last_hash == '21':
						line = ('bg black,10\n')

					#61 BGMのフェードアウト
					elif last_hash == '61':
						line = ('bgmfadeout 1000\n')						

					#65 動画？
					elif last_hash == '65':
						line = ('RSC_MOVIE ' + str(convert_list[0]) + ',' + str(movie_cnt) +'\n')
						movie_cnt += 1

					#多分無視して良いと思われる命令のみなさん！！！！！！！！レスキュー開始！！！！
					elif last_hash in [
							'6144',#場面ごとのセーブ時サムネイル切り替えに使われているもよう
							'BLEND_IMG',#画像周りなんだろうけどNSCに対応する命令が見つからない
							'CLEAR_MESSAGE_WINDOW',#このコンバータ毎回画面クリアしてるんで...
						]:
						line = (';' + line) if DEBUG_MODE else ''

					#その他 - 知らんのでprint出す
					else:
						if DEBUG_MODE:
							print('UnknownCMD:' + last_hash)
						line = (';' + line) if DEBUG_MODE else ''

					#処理終了後"last_hash"をもどす
					last_hash = False
				
				#その他 - エラー防止の為コメントアウト
				else:

					#ルビをNSC形式へ置換
					line = re.sub(r'\|(.+?)\[(.+?)?\]', r'(\1/\2)', line)
					line = re.sub(r'(.)\[(.+?)?\]', r'(\1/\2)', line)

					#原作のdelayらしきものを抹消(実装面倒なので)
					line = re.sub(r'\^d([0-9]+)', '', line)
					line = line.replace(r'^', '')

					#ここ半角英数字の入ったシナリオ文へのごまかし - kagerou専用
					line = line.replace(r'!', r'！')
					line = line.replace(r'?', r'？')
					line = line.replace(r'essence', r'ｅｓｓｅｎｃｅ')

					#半角英数字が入ってる場合 - シナリオ文ではないと判定
					if re.search(r'[A-z0-9]', line):
						print('UnknownSTR:' + line.replace('\n', ''))
						line = (';' + line) if DEBUG_MODE else ''
						
					#半角英数字が入ってない場合 - シナリオ文です
					else:
						line_message = True
						mes_cnt += 1
				
				#シナリオ文終了時
				if (not line_message) and (last_message):
					#改ページ
					line = ('\\\n' + line)

					#行数カウント 最大数の場合代入
					if (mes_cnt > mes_max):
						mes_max = mes_cnt
					
					#行数カウント 初期化
					mes_cnt = 0

				txt += line

			#デコード済みtxt一つごとに終了時return
			txt += '\nreturn'

	#ガ バ ガ バ 修 正
	txt = txt.replace(r'gosub *SCR_1000_gsc', r'gosub *SCR_0999_gsc:gosub *SCR_1000_gsc')#"はじめから"時の最初の「～遍く活字愛好家に捧ぐ～」に飛ばす
	txt = txt.replace(r'gosub *SCR_1132_gsc', r'gosub *SCR_1132_gsc:return')#個別ルート終了時次の個別ルートにそのまま飛ぶのを防ぐ
	txt = txt.replace(r'gosub *SCR_1134_gsc', r'gosub *SCR_1134_gsc:return')#同上
	txt = txt.replace(r'gosub *SCR_1240_gsc', r'gosub *SCR_1240_gsc:return')#同上
	txt = txt.replace(r'gosub *SCR_1242_gsc', r'gosub *SCR_1242_gsc:return')#同上
	txt = txt.replace(r'gosub *SCR_1016_gsc', r'gosub *SCR_1016_gsc:RSC_select_chara2')
	txt = txt.replace(r'渡し守にそう問いかけられて、築宮の中に咄嗟に浮かんだのは―――', r'渡し守にそう問いかけられて、築宮の中に咄嗟に浮かんだのは―――' + '\\\ngoto *skip_fix1')#個別ルート分岐ごまかし1
	txt = txt.replace(r'mov %21,8061:mov %22,8062:mov %23,8063', '*skip_fix1\n' + r'mov %21,8061:mov %22,8062:mov %23,8063:RSC_select:RSC_select_chara')#個別ルート分岐ごまかし2

	#出力結果を書き込み
	open(zero_txt, 'w', errors='ignore').write(txt)

	#デバッグ時のみ最大行数を表示
	if DEBUG_MODE:
		print('最大行数:' + str(mes_max))

	return


def junk_del(delete_list, delete_list2):

	#リスト内のディレクトリパスでfor
	for d in delete_list:

		#ディレクトリパス内のファイル一覧でfor
		for p in d.glob('*'):

			#削除
			p.unlink()
		
		#ディレクトリも削除
		d.rmdir()

	#リスト内のディレクトリパスでfor
	for d in delete_list2:

		#ディレクトリパス内のファイル(lwg)一覧でfor
		for p in d.glob('*.lwg'):

			#削除
			p.unlink()

	return


# メイン関数
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	#(マルチコンバータ利用時)自動展開
	if values: extract_resource(values, values_ex, pre_converted_dir)

	#デバッグ
	debug = 0

	#同一階層のパスを変数へ代入
	same_hierarchy = pre_converted_dir#Path.cwd()

	#debug時にtestフォルダに入れないやつ(default.txt等)はこっちを利用
	same_hierarchy_const = same_hierarchy

	if debug:
		#デバッグ時はtestディレクトリ直下
		same_hierarchy = (same_hierarchy / 'test')

	#利用するパスを辞書に入れ一括代入
	PATH_DICT = {
		#先に準備しておくべきファイル一覧 - kagerou専用
		'bgm'    :(same_hierarchy / 'bgm'),
		'grpe'   :(same_hierarchy / 'grpe'),
		'grpo'   :(same_hierarchy / 'grpo'),
		'grpo_bu':(same_hierarchy / 'grpo_bu'),
		'grps'   :(same_hierarchy / 'grps'),
		'scr'    :(same_hierarchy / 'scr'),
		'voice'  :(same_hierarchy / 'voice'),
		'wav'    :(same_hierarchy / 'wav'),
		'mov'    :(same_hierarchy / 'mov'),

		#'gsc_exe':(same_hierarchy_const / 'gscScriptCompAndDecompiler.exe'),
		#'default':(same_hierarchy_const / 'default.txt'),
	}

	PATH_DICT2 = {
		#変換後に出力されるファイル一覧
		'scr_dec':(same_hierarchy / 'scr_dec'),
		'0_txt'  :(same_hierarchy / '0.txt'),
	}

	if values:
		from requiredfile_locations import location
		PATH_DICT['gsc_exe'] = location('gscScriptCompAndDecompiler-cli')

	else:
		PATH_DICT['gsc_exe'] = (same_hierarchy_const / 'gscScriptCompAndDecompiler.exe')

	#ディレクトリの存在チェック
	dir_check_result = dir_check(PATH_DICT.values())

	#存在しない場合終了
	if not dir_check_result:
		return

	#シナリオを平文にデコードする
	text_dec(PATH_DICT['gsc_exe'], PATH_DICT['scr'], PATH_DICT2['scr_dec'], values_ex )

	#GARBroでぶっこ抜いたogg何故かONSで使えないのでデコード
	sound_dec([
		PATH_DICT['bgm'],
		PATH_DICT['wav'],
		PATH_DICT['voice'],
	], values_ex)

	#txt置換→0.txt出力
	text_cnv(debug, PATH_DICT2['0_txt'], PATH_DICT2['scr_dec'], PATH_DICT.keys())

	#不要データ削除
	junk_del([
		PATH_DICT['scr'],
		PATH_DICT2['scr_dec'],
	], [
		PATH_DICT['grps'],
	])


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()