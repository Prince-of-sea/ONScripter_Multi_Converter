#!/usr/bin/env python3
from PIL import Image
from pathlib import Path
import subprocess as sp
import concurrent.futures
import tempfile, shutil, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'CUFFS',
		'date': 20060811,
		'title': 'ワンコとリリー (パッケージ版不可)',
		'cli_arg': 'cuffs_wankor',
		'requiredsoft': ['Kikiriki'],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),

		'version': [
			'ワンコとリリー FANZA DL版(cuffs_0023)',
		],

		'notes': [
			'おまけシナリオの出現条件を"全3種類のエンディングを見る"のみに緩和',
			'主人公の名前変更機能削除、初期状態(倉田 誠一)で固定',
			'UI周りはONS標準の最低限のみ、原作の仕様はほぼ無視',
			'wait処理の待ち時間や一部画面遷移が原作と違う',
			'クリック待ちカーソルが表示されない',
			'立ち絵の表示位置に多少のズレ有り',
			'スタッフロール若干仕様変更',
			'コンフィグ画面簡略化',
			'鑑賞モード未実装',
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from requiredfile_locations import location # type: ignore
	from utils import extract_archive_garbro, subprocess_args # type: ignore

	input_dir = values['input_dir']

	#"xp3群をkikirikiで展開→展開した'parts'をzip圧縮→parts.zipをGARbroへ→再度展開しながら変換"

	#入力パス
	data_Path = Path(input_dir / 'data.xp3')
	parts_Path = Path(input_dir / 'parts.xp3')

	#出力パス
	data_outdir = Path(pre_converted_dir / 'data')
	parts_outdir = Path(pre_converted_dir / 'parts')

	#存在チェック
	if not data_Path.is_file(): raise FileNotFoundError('data.xp3が見つかりません')
	if not parts_Path.is_file(): raise FileNotFoundError('parts.xp3が見つかりません')

	#パス取得
	Kikiriki_Path = location('Kikiriki')
	madCHook_Path = Path( Kikiriki_Path.parent / 'madCHook.dll')
	tpm_Path = Path(input_dir / 'plugin' / 'wankor.tpm')

	#展開ツール環境用一時ディレクトリ作成
	with tempfile.TemporaryDirectory() as temp_dir:
		temp_dir = Path(temp_dir)

		#コピー先パス
		Kikiriki_copy_Path = Path(temp_dir / 'kikiriki.exe')
		madCHook_copy_Path = Path(temp_dir / 'madCHook.dll')
		tpm_copy_Path = Path(temp_dir / 'wankor.tpm')

		#全部コピー
		shutil.copy(Kikiriki_Path, Kikiriki_copy_Path)
		shutil.copy(madCHook_Path, madCHook_copy_Path)
		shutil.copy(tpm_Path, tpm_copy_Path)

		#展開
		sp.run([Kikiriki_copy_Path, '-i', data_Path, '-o', data_outdir], **subprocess_args())
		sp.run([Kikiriki_copy_Path, '-i', parts_Path, '-o', parts_outdir], **subprocess_args())

	#(tlgをGARbroに変換させるため)dataをzipに圧縮
	shutil.make_archive(parts_outdir, format='zip', root_dir=parts_outdir)
	shutil.rmtree(parts_outdir)

	#GARbro展開変換
	parts_outzip = Path(pre_converted_dir / 'parts.zip')
	extract_archive_garbro(parts_outzip, parts_outdir, 'png')
	parts_outzip.unlink()

	return


def default_txt():
	s = ''';mode800
*define

caption "ワンコとリリー【Windows10対応版】 for ONScripter"
rmenu "セーブ",save,"ロード",load,"スキップ",skip,"タイトル",reset
savename "セーブ","ロード","ＤＡＴＡ"
savenumber 18
transmode alpha
globalon
rubyon
nsa
windowback

humanz 19
windowchip 10

;ほぼpsp対策 高性能な他機種の場合これ消して良いかも
;maxkaisoupage 5

effect 10,10,150
effect 11,10,500
effect 12,10,1000
effect 13,10,2000
effect 15,10,5000

pretextgosub *pretext_lb
defsub setwin
defsub def_cg
defsub def_talk
defsub def_staffroll
defsub def_char
defsub def_clearchar
defsub def_addselect
defsub def_startselect
defsub start_set
defsub vsp_cl_all
game
;----------------------------------------
*setwin
	getparam %1
	if %1==1 setwindow  82,472,27,4,24,24,0, 5,10,1,1,"parts/frame/frm_0102.png", 57,458
	if %1==2 setwindow 192,244,20,2,24,24,0,21, 0,1,1,#FFFFFF,               0,0,799,599
return
;----------------------------------------
*pretext_lb
	if %60==1 print 10:mov %60,0
	if $10=="" csp 10:print 1:saveon:return

	;キャラ名中央表示用座標取得
	;詳細はミクキスコンバータ参照
	len %1,$10
	mov %2,(306-(%1/2)*(32+2)-2)/2

	lsp 10,":s/32,32,0;#ffffff"+$10,%2,418:print 1
	saveon
return

*def_talk
	getparam $10
	if $10!="心の声" vsp 11,1
	if $10=="心の声" mov $10,"":vsp 11,0
return
;----------------------------------------
*def_char
	getparam $1,%1,%2
	;%55 番号カウンタ
	;%56 ワンコ(ca)lsp番号
	;%57 リリー(cc)lsp番号
	;%58 透子(cb)lsp番号
	;%59 今何人表示中か
	;%60 立ち絵変更フラグ(次回文章表示前にprint挟む)

	;文字列$1の0文字目から2文字分の部分文字列を$2に切り出す
	mid $2,$1,0,2

	;(%1*2/3) → これホントは絶対違うんだけど元の実装分からんしとりあえず
	if $2=="ca" if %56==0 mov %56,20+%55:inc %55:inc %59
	if $2=="ca" if %2==0  lsph %56,"parts/char/"+$1+".png",0,0:getspsize %56,%61,%62:amsp %56,400-(%61/2)+(%1*2/3),0:vsp %56,1
	if $2=="ca" if %2==1  lsph %56,"parts/char/"+$1+".png",0,0:getspsize %56,%61,%62:amsp %56,400-(%61/2)-(%1*2/3),0:vsp %56,1
	if $2=="cc" if %57==0 mov %57,20+%55:inc %55:inc %59
	if $2=="cc" if %2==0  lsph %57,"parts/char/"+$1+".png",0,0:getspsize %57,%61,%62:amsp %57,400-(%61/2)+(%1*2/3),0:vsp %57,1
	if $2=="cc" if %2==1  lsph %57,"parts/char/"+$1+".png",0,0:getspsize %58,%61,%62:amsp %58,400-(%61/2)-(%1*2/3),0:vsp %58,1
	if $2=="cb" if %58==0 mov %58,20+%55:inc %55:inc %59
	if $2=="cb" if %2==0  lsph %58,"parts/char/"+$1+".png",0,0:getspsize %58,%61,%62:amsp %58,400-(%61/2)+(%1*2/3),0:vsp %58,1
	if $2=="cb" if %2==1  lsph %58,"parts/char/"+$1+".png",0,0:getspsize %58,%61,%62:amsp %58,400-(%61/2)-(%1*2/3),0:vsp %58,1

	mov %60,1
return

*def_clearchar
	getparam $1
	if $1=="ワンコ" csp %56:mov %56,0:dec %59
	if $1=="リリー" csp %57:mov %57,0:dec %59
	if $1=="透子" csp %58:mov %58,0:dec %59
	if $1=="None" csp %56:csp %57:csp %58:mov %56,0:mov %57,0:mov %58,0:mov %59,0

	;表示中の立ち絵が消えたらカウンタリセット
	if %59==0 mov %55,0

	mov %60,1
return
;----------------------------------------
*def_cg
	getparam $20

	;とりあえず立ち絵消す - 多分立ち絵残して背景変更ってないと思うので
	def_clearchar "None"

	if $20=="black" bg black,10:return
	if $20=="white" bg white,10:return

	;文字列$20の0文字目から2文字分の部分文字列を$21に切り出す→"bg"なら背景
	mid $21,$20,0,2
	if $21=="bg" bg "parts/bg/"+$20+".png",10:return
	if $21!="bg" bg "parts/event/"+$20+".png",10:return
return

*def_addselect
	getparam $50
	;どうせ選択肢常に2択なんでこれでいい
	if $51=="" mov $51,$50
	if $51!="" mov $52,$50
	mov %51,0:mov %52,0
return

*def_startselect
	setwin 2
	;選択肢背景
	lsp 6,":a/2,0,3;parts/frame/frm_0104.png",143,253
	lsp 7,":a/2,0,3;parts/frame/frm_0104.png",143,299
	;メッセージウィンドウ偽装
	lsp 8,"parts/frame/frm_0102.png", 57,458:print 1

	select $51,*ss1,
	       $52,*ss2

	*ss1
		mov %51,1:goto *ssend
	*ss2
		mov %52,1

	*ssend
	setwin 1
	csp 6:csp 7:csp 8:print 1
	mov $50,"":mov $51,"":mov $52,""
return

*vsp_cl_all
	vsp 20 ,0:vsp 21 ,0:vsp 22 ,0:vsp 23 ,0:vsp 24 ,0:vsp 25 ,0:vsp 26 ,0:vsp 27 ,0:vsp 28 ,0:vsp 29 ,0
	vsp 30 ,0:vsp 31 ,0:vsp 32 ,0:vsp 33 ,0:vsp 34 ,0:vsp 35 ,0:vsp 36 ,0:vsp 37 ,0:vsp 38 ,0:vsp 39 ,0
	vsp 40 ,0:vsp 41 ,0:vsp 42 ,0:vsp 43 ,0:vsp 44 ,0:vsp 45 ,0:vsp 46 ,0:vsp 47 ,0:vsp 48 ,0:vsp 49 ,0
	vsp 50 ,0:vsp 51 ,0:vsp 52 ,0:vsp 53 ,0:vsp 54 ,0:vsp 55 ,0:vsp 56 ,0:vsp 57 ,0:vsp 58 ,0:vsp 59 ,0
	vsp 60 ,0:vsp 61 ,0:vsp 62 ,0:vsp 63 ,0:vsp 64 ,0:vsp 65 ,0:vsp 66 ,0:vsp 67 ,0:vsp 68 ,0:vsp 69 ,0
	vsp 70 ,0:vsp 71 ,0:vsp 72 ,0:vsp 73 ,0:vsp 74 ,0:vsp 75 ,0:vsp 76 ,0:vsp 77 ,0:vsp 78 ,0:vsp 79 ,0
	vsp 80 ,0:vsp 81 ,0:vsp 82 ,0:vsp 83 ,0:vsp 84 ,0:vsp 85 ,0:vsp 86 ,0:vsp 87 ,0:vsp 88 ,0:vsp 89 ,0
	vsp 90 ,0:vsp 91 ,0:vsp 92 ,0:vsp 93 ,0:vsp 94 ,0:vsp 95 ,0:vsp 96 ,0:vsp 97 ,0:vsp 98 ,0:vsp 99 ,0
	vsp 100,0:vsp 101,0:vsp 102,0:vsp 103,0:vsp 104,0:vsp 105,0:vsp 106,0:vsp 107,0:vsp 108,0:vsp 109,0
	vsp 110,0:vsp 111,0:vsp 112,0:vsp 113,0:vsp 114,0:vsp 115,0:vsp 116,0:vsp 117,0:vsp 118,0:vsp 119,0
	vsp 120,0:vsp 121,0
return
;----------------------------------------
*def_staffroll
	skipoff:saveoff:lookbackflush

	;%150 再生時間
	;%152 ロール画像y
	;%77 gettimer
	
	;ed曲の再生時間
	mov %150,97960

	bgmonce "parts/bgm/bgm_ed.ogg"
	resettimer

	lsp  1,"parts/frame/crd_0001.png",523,600:getspsize 1,%66,%151
	lsp  2,"parts/frame/crd_0002.png",523,600:getspsize 1,%66,%152
	lsp  3,"parts/frame/crd_0003.png",523,600:getspsize 1,%66,%153
	lsp  4,"parts/frame/crd_0004.png",523,600:getspsize 1,%66,%154
	lsp  5,"parts/frame/crd_0005.png",523,600:getspsize 1,%66,%155
	lsp  6,"parts/frame/crd_0006.png",523,600:getspsize 1,%66,%156
	lsp  7,"parts/frame/crd_0007.png",523,600:getspsize 1,%66,%157
	lsp  8,"parts/frame/crd_0008.png",523,600:getspsize 1,%66,%158
	lsp  9,"parts/frame/crd_0009.png",523,600:getspsize 1,%66,%159
	lsp 10,"parts/frame/crd_0010.png",523,600:getspsize 1,%66,%160
	lsp 11,"parts/frame/crd_0011.png",523,600:getspsize 1,%66,%161
	lsp 12,"parts/frame/crd_0012.png",523,600:getspsize 1,%66,%162
	lsp 13,"parts/frame/crd_0013.png",523,600:getspsize 1,%66,%163
	lsp 14,"parts/frame/crd_0014.png",523,600:getspsize 1,%66,%164
	lsp 15,"parts/frame/crd_0015.png",523,600:getspsize 1,%66,%165
	;lsp 16,"parts/frame/crd_0016.png",523,600:getspsize 1,%66,%166

	lsph 20  "parts/frame/part0001.png",30,150:lsph 21  "parts/frame/part0002.png",30,150:lsph 22  "parts/frame/part1001.png",30,150:lsph 23  "parts/frame/part1002.png",30,150:lsph 24  "parts/frame/part1003.png",30,150
	lsph 25  "parts/frame/part1004.png",30,150:lsph 26  "parts/frame/part1005.png",30,150:lsph 27  "parts/frame/part1006.png",30,150:lsph 28  "parts/frame/part2001.png",30,150:lsph 29  "parts/frame/part2002.png",30,150
	lsph 30  "parts/frame/part2003.png",30,150:lsph 31  "parts/frame/part2004.png",30,150:lsph 32  "parts/frame/part2005.png",30,150:lsph 33  "parts/frame/part3001.png",30,150:lsph 34  "parts/frame/part3002.png",30,150
	lsph 35  "parts/frame/part3003.png",30,150:lsph 36  "parts/frame/part3004.png",30,150:lsph 37  "parts/frame/part3005.png",30,150:lsph 38  "parts/frame/part3006.png",30,150:lsph 39  "parts/frame/part3007.png",30,150
	lsph 40  "parts/frame/part4001.png",30,150:lsph 41  "parts/frame/part4002.png",30,150:lsph 42  "parts/frame/part4003.png",30,150:lsph 43  "parts/frame/part4004.png",30,150:lsph 44  "parts/frame/part4005.png",30,150
	lsph 45  "parts/frame/part4006.png",30,150:lsph 46  "parts/frame/part4007.png",30,150:lsph 47  "parts/frame/part4008.png",30,150:lsph 48  "parts/frame/part4101.png",30,150:lsph 49  "parts/frame/part4102.png",30,150
	lsph 50  "parts/frame/part4103.png",30,150:lsph 51  "parts/frame/part4104.png",30,150:lsph 52  "parts/frame/part4105.png",30,150:lsph 53  "parts/frame/part4106.png",30,150:lsph 54  "parts/frame/part4107.png",30,150
	lsph 55  "parts/frame/part4108.png",30,150:lsph 56  "parts/frame/part4109.png",30,150:lsph 57  "parts/frame/part4110.png",30,150:lsph 58  "parts/frame/part4201.png",30,150:lsph 59  "parts/frame/part4202.png",30,150
	lsph 60  "parts/frame/part4203.png",30,150:lsph 61  "parts/frame/part4204.png",30,150:lsph 62  "parts/frame/part4205.png",30,150:lsph 63  "parts/frame/part4206.png",30,150:lsph 64  "parts/frame/part5001.png",30,150
	lsph 65  "parts/frame/part5002.png",30,150:lsph 66  "parts/frame/part5003.png",30,150:lsph 67  "parts/frame/part5004.png",30,150:lsph 68  "parts/frame/part5005.png",30,150:lsph 69  "parts/frame/part5006.png",30,150
	lsph 70  "parts/frame/part5007.png",30,150:lsph 71  "parts/frame/part5008.png",30,150:lsph 72  "parts/frame/part5101.png",30,150:lsph 73  "parts/frame/part5102.png",30,150:lsph 74  "parts/frame/part5103.png",30,150
	lsph 75  "parts/frame/part5104.png",30,150:lsph 76  "parts/frame/part5105.png",30,150:lsph 77  "parts/frame/part5106.png",30,150:lsph 78  "parts/frame/part5107.png",30,150:lsph 79  "parts/frame/part5108.png",30,150
	lsph 80  "parts/frame/part5109.png",30,150:lsph 81  "parts/frame/part5110.png",30,150:lsph 82  "parts/frame/part5201.png",30,150:lsph 83  "parts/frame/part5202.png",30,150:lsph 84  "parts/frame/part5203.png",30,150
	lsph 85  "parts/frame/part5204.png",30,150:lsph 86  "parts/frame/part5205.png",30,150:lsph 87  "parts/frame/part5206.png",30,150:lsph 88  "parts/frame/part5207.png",30,150:lsph 89  "parts/frame/part5208.png",30,150
	lsph 90  "parts/frame/part6001.png",30,150:lsph 91  "parts/frame/part6002.png",30,150:lsph 92  "parts/frame/part6101.png",30,150:lsph 93  "parts/frame/part6102.png",30,150:lsph 94  "parts/frame/part6103.png",30,150
	lsph 95  "parts/frame/part6104.png",30,150:lsph 96  "parts/frame/part6105.png",30,150:lsph 97  "parts/frame/part6106.png",30,150:lsph 98  "parts/frame/part6107.png",30,150:lsph 99  "parts/frame/part6201.png",30,150
	lsph 100 "parts/frame/part6202.png",30,150:lsph 101 "parts/frame/part6203.png",30,150:lsph 102 "parts/frame/part6204.png",30,150:lsph 103 "parts/frame/part6205.png",30,150:lsph 104 "parts/frame/part7001.png",30,150
	lsph 105 "parts/frame/part7101.png",30,150:lsph 106 "parts/frame/part7201.png",30,150:lsph 107 "parts/frame/part7202.png",30,150:lsph 108 "parts/frame/part7203.png",30,150:lsph 109 "parts/frame/part8001.png",30,150
	lsph 110 "parts/frame/part8101.png",30,150:lsph 111 "parts/frame/part8201.png",30,150:lsph 112 "parts/frame/part9001.png",30,150:lsph 113 "parts/frame/part9002.png",30,150:lsph 114 "parts/frame/part9003.png",30,150
	lsph 115 "parts/frame/part9004.png",30,150:lsph 116 "parts/frame/part9101.png",30,150:lsph 117 "parts/frame/part9201.png",30,150:lsph 118 "parts/frame/part9202.png",30,150:lsph 119 "parts/frame/part9203.png",30,150
	lsph 120 "parts/frame/part9901.png",30,150:lsph 121 "parts/frame/part9902.png",30,150
	
	*staffroll_loop0
		saveoff
		gettimer %77
		if %77>10000 goto *staffroll_end0
		wait 10
	goto *staffroll_loop0
	*staffroll_end0

	bg black,15
	waittimer 15000
	vsp 20,1:print 15

	*staffroll_loop1
		saveoff
		gettimer %77

		;なぜか関数作って飛ばすと安定しないのでベタ書き

		if %77> 30000 if %77<= 30500 if %10!=  1 mov %10,  1 :vsp_cl_all:vsp 20 ,1:print 1
		if %77> 30500 if %77<= 31000 if %10!=  2 mov %10,  2 :vsp_cl_all:vsp 21 ,1:print 1
		if %77> 31000 if %77<= 31500 if %10!=  3 mov %10,  3 :vsp_cl_all:vsp 22 ,1:print 1
		if %77> 31500 if %77<= 32000 if %10!=  4 mov %10,  4 :vsp_cl_all:vsp 23 ,1:print 1
		if %77> 32000 if %77<= 32500 if %10!=  5 mov %10,  5 :vsp_cl_all:vsp 24 ,1:print 1
		if %77> 32500 if %77<= 33000 if %10!=  6 mov %10,  6 :vsp_cl_all:vsp 25 ,1:print 1
		if %77> 33000 if %77<= 33500 if %10!=  7 mov %10,  7 :vsp_cl_all:vsp 26 ,1:print 1
		if %77> 33500 if %77<= 34000 if %10!=  8 mov %10,  8 :vsp_cl_all:vsp 27 ,1:print 1
		if %77> 34000 if %77<= 34500 if %10!=  9 mov %10,  9 :vsp_cl_all:vsp 28 ,1:print 1
		if %77> 34500 if %77<= 35000 if %10!= 10 mov %10, 10 :vsp_cl_all:vsp 29 ,1:print 1
		if %77> 35000 if %77<= 35500 if %10!= 11 mov %10, 11 :vsp_cl_all:vsp 30 ,1:print 1
		if %77> 35500 if %77<= 36000 if %10!= 12 mov %10, 12 :vsp_cl_all:vsp 31 ,1:print 1
		if %77> 36000 if %77<= 36500 if %10!= 13 mov %10, 13 :vsp_cl_all:vsp 32 ,1:print 1
		if %77> 36500 if %77<= 37000 if %10!= 14 mov %10, 14 :vsp_cl_all:vsp 33 ,1:print 1
		if %77> 37000 if %77<= 37500 if %10!= 15 mov %10, 15 :vsp_cl_all:vsp 34 ,1:print 1
		if %77> 37500 if %77<= 38000 if %10!= 16 mov %10, 16 :vsp_cl_all:vsp 35 ,1:print 1
		if %77> 38000 if %77<= 38500 if %10!= 17 mov %10, 17 :vsp_cl_all:vsp 36 ,1:print 1
		if %77> 38500 if %77<= 39000 if %10!= 18 mov %10, 18 :vsp_cl_all:vsp 37 ,1:print 1
		if %77> 39000 if %77<= 39500 if %10!= 19 mov %10, 19 :vsp_cl_all:vsp 38 ,1:print 1
		if %77> 39500 if %77<= 40000 if %10!= 20 mov %10, 20 :vsp_cl_all:vsp 39 ,1:print 1
		if %77> 40000 if %77<= 40500 if %10!= 21 mov %10, 21 :vsp_cl_all:vsp 40 ,1:print 1
		if %77> 40500 if %77<= 41000 if %10!= 22 mov %10, 22 :vsp_cl_all:vsp 41 ,1:print 1
		if %77> 41000 if %77<= 41500 if %10!= 23 mov %10, 23 :vsp_cl_all:vsp 42 ,1:print 1
		if %77> 41500 if %77<= 42000 if %10!= 24 mov %10, 24 :vsp_cl_all:vsp 43 ,1:print 1
		if %77> 42000 if %77<= 42500 if %10!= 25 mov %10, 25 :vsp_cl_all:vsp 44 ,1:print 1
		if %77> 42500 if %77<= 43000 if %10!= 26 mov %10, 26 :vsp_cl_all:vsp 45 ,1:print 1
		if %77> 43000 if %77<= 43500 if %10!= 27 mov %10, 27 :vsp_cl_all:vsp 46 ,1:print 1
		if %77> 43500 if %77<= 44000 if %10!= 28 mov %10, 28 :vsp_cl_all:vsp 47 ,1:print 1
		if %77> 44000 if %77<= 44500 if %10!= 29 mov %10, 29 :vsp_cl_all:vsp 48 ,1:print 1
		if %77> 44500 if %77<= 45000 if %10!= 30 mov %10, 30 :vsp_cl_all:vsp 49 ,1:print 1
		if %77> 45000 if %77<= 45500 if %10!= 31 mov %10, 31 :vsp_cl_all:vsp 50 ,1:print 1
		if %77> 45500 if %77<= 46000 if %10!= 32 mov %10, 32 :vsp_cl_all:vsp 51 ,1:print 1
		if %77> 46000 if %77<= 46500 if %10!= 33 mov %10, 33 :vsp_cl_all:vsp 52 ,1:print 1
		if %77> 46500 if %77<= 47000 if %10!= 34 mov %10, 34 :vsp_cl_all:vsp 53 ,1:print 1
		if %77> 47000 if %77<= 47500 if %10!= 35 mov %10, 35 :vsp_cl_all:vsp 54 ,1:print 1
		if %77> 47500 if %77<= 48000 if %10!= 36 mov %10, 36 :vsp_cl_all:vsp 55 ,1:print 1
		if %77> 48000 if %77<= 48500 if %10!= 37 mov %10, 37 :vsp_cl_all:vsp 56 ,1:print 1
		if %77> 48500 if %77<= 49000 if %10!= 38 mov %10, 38 :vsp_cl_all:vsp 57 ,1:print 1
		if %77> 49000 if %77<= 49500 if %10!= 39 mov %10, 39 :vsp_cl_all:vsp 58 ,1:print 1
		if %77> 49500 if %77<= 50000 if %10!= 40 mov %10, 40 :vsp_cl_all:vsp 59 ,1:print 1
		if %77> 50000 if %77<= 50500 if %10!= 41 mov %10, 41 :vsp_cl_all:vsp 60 ,1:print 1
		if %77> 50500 if %77<= 51000 if %10!= 42 mov %10, 42 :vsp_cl_all:vsp 61 ,1:print 1
		if %77> 51000 if %77<= 51500 if %10!= 43 mov %10, 43 :vsp_cl_all:vsp 62 ,1:print 1
		if %77> 51500 if %77<= 52000 if %10!= 44 mov %10, 44 :vsp_cl_all:vsp 63 ,1:print 1
		if %77> 52000 if %77<= 52500 if %10!= 45 mov %10, 45 :vsp_cl_all:vsp 64 ,1:print 1
		if %77> 52500 if %77<= 53000 if %10!= 46 mov %10, 46 :vsp_cl_all:vsp 65 ,1:print 1
		if %77> 53000 if %77<= 53500 if %10!= 47 mov %10, 47 :vsp_cl_all:vsp 66 ,1:print 1
		if %77> 53500 if %77<= 54000 if %10!= 48 mov %10, 48 :vsp_cl_all:vsp 67 ,1:print 1
		if %77> 54000 if %77<= 54500 if %10!= 49 mov %10, 49 :vsp_cl_all:vsp 68 ,1:print 1
		if %77> 54500 if %77<= 55000 if %10!= 50 mov %10, 50 :vsp_cl_all:vsp 69 ,1:print 1
		if %77> 55000 if %77<= 55500 if %10!= 51 mov %10, 51 :vsp_cl_all:vsp 70 ,1:print 1
		if %77> 55500 if %77<= 56000 if %10!= 52 mov %10, 52 :vsp_cl_all:vsp 71 ,1:print 1
		if %77> 56000 if %77<= 56500 if %10!= 53 mov %10, 53 :vsp_cl_all:vsp 72 ,1:print 1
		if %77> 56500 if %77<= 57000 if %10!= 54 mov %10, 54 :vsp_cl_all:vsp 73 ,1:print 1
		if %77> 57000 if %77<= 57500 if %10!= 55 mov %10, 55 :vsp_cl_all:vsp 74 ,1:print 1
		if %77> 57500 if %77<= 58000 if %10!= 56 mov %10, 56 :vsp_cl_all:vsp 75 ,1:print 1
		if %77> 58000 if %77<= 58500 if %10!= 57 mov %10, 57 :vsp_cl_all:vsp 76 ,1:print 1
		if %77> 58500 if %77<= 59000 if %10!= 58 mov %10, 58 :vsp_cl_all:vsp 77 ,1:print 1
		if %77> 59000 if %77<= 59500 if %10!= 59 mov %10, 59 :vsp_cl_all:vsp 78 ,1:print 1
		if %77> 59500 if %77<= 60000 if %10!= 60 mov %10, 60 :vsp_cl_all:vsp 79 ,1:print 1
		if %77> 60000 if %77<= 60500 if %10!= 61 mov %10, 61 :vsp_cl_all:vsp 80 ,1:print 1
		if %77> 60500 if %77<= 61000 if %10!= 62 mov %10, 62 :vsp_cl_all:vsp 81 ,1:print 1
		if %77> 61000 if %77<= 61500 if %10!= 63 mov %10, 63 :vsp_cl_all:vsp 82 ,1:print 1
		if %77> 61500 if %77<= 62000 if %10!= 64 mov %10, 64 :vsp_cl_all:vsp 83 ,1:print 1
		if %77> 62000 if %77<= 62500 if %10!= 65 mov %10, 65 :vsp_cl_all:vsp 84 ,1:print 1
		if %77> 62500 if %77<= 63000 if %10!= 66 mov %10, 66 :vsp_cl_all:vsp 85 ,1:print 1
		if %77> 63000 if %77<= 63500 if %10!= 67 mov %10, 67 :vsp_cl_all:vsp 86 ,1:print 1
		if %77> 63500 if %77<= 64000 if %10!= 68 mov %10, 68 :vsp_cl_all:vsp 87 ,1:print 1
		if %77> 64000 if %77<= 64500 if %10!= 69 mov %10, 69 :vsp_cl_all:vsp 88 ,1:print 1
		if %77> 64500 if %77<= 65000 if %10!= 70 mov %10, 70 :vsp_cl_all:vsp 89 ,1:print 1
		if %77> 65000 if %77<= 65500 if %10!= 71 mov %10, 71 :vsp_cl_all:vsp 90 ,1:print 1
		if %77> 65500 if %77<= 66000 if %10!= 72 mov %10, 72 :vsp_cl_all:vsp 91 ,1:print 1
		if %77> 66000 if %77<= 66500 if %10!= 73 mov %10, 73 :vsp_cl_all:vsp 92 ,1:print 1
		if %77> 66500 if %77<= 67000 if %10!= 74 mov %10, 74 :vsp_cl_all:vsp 93 ,1:print 1
		if %77> 67000 if %77<= 67500 if %10!= 75 mov %10, 75 :vsp_cl_all:vsp 94 ,1:print 1
		if %77> 67500 if %77<= 68000 if %10!= 76 mov %10, 76 :vsp_cl_all:vsp 95 ,1:print 1
		if %77> 68000 if %77<= 68500 if %10!= 77 mov %10, 77 :vsp_cl_all:vsp 96 ,1:print 1
		if %77> 68500 if %77<= 69000 if %10!= 78 mov %10, 78 :vsp_cl_all:vsp 97 ,1:print 1
		if %77> 69000 if %77<= 69500 if %10!= 79 mov %10, 79 :vsp_cl_all:vsp 98 ,1:print 1
		if %77> 69500 if %77<= 70000 if %10!= 80 mov %10, 80 :vsp_cl_all:vsp 99 ,1:print 1
		if %77> 70000 if %77<= 70500 if %10!= 81 mov %10, 81 :vsp_cl_all:vsp 100,1:print 1
		if %77> 70500 if %77<= 71000 if %10!= 82 mov %10, 82 :vsp_cl_all:vsp 101,1:print 1
		if %77> 71000 if %77<= 71500 if %10!= 83 mov %10, 83 :vsp_cl_all:vsp 102,1:print 1
		if %77> 71500 if %77<= 72000 if %10!= 84 mov %10, 84 :vsp_cl_all:vsp 103,1:print 1
		if %77> 72000 if %77<= 72500 if %10!= 85 mov %10, 85 :vsp_cl_all:vsp 104,1:print 1
		if %77> 72500 if %77<= 73000 if %10!= 86 mov %10, 86 :vsp_cl_all:vsp 105,1:print 1
		if %77> 73000 if %77<= 73500 if %10!= 87 mov %10, 87 :vsp_cl_all:vsp 106,1:print 1
		if %77> 73500 if %77<= 74000 if %10!= 88 mov %10, 88 :vsp_cl_all:vsp 107,1:print 1
		if %77> 74000 if %77<= 74500 if %10!= 89 mov %10, 89 :vsp_cl_all:vsp 108,1:print 1
		if %77> 74500 if %77<= 75000 if %10!= 90 mov %10, 90 :vsp_cl_all:vsp 109,1:print 1
		if %77> 75000 if %77<= 75500 if %10!= 91 mov %10, 91 :vsp_cl_all:vsp 110,1:print 1
		if %77> 75500 if %77<= 76000 if %10!= 92 mov %10, 92 :vsp_cl_all:vsp 111,1:print 1
		if %77> 76000 if %77<= 76500 if %10!= 93 mov %10, 93 :vsp_cl_all:vsp 112,1:print 1
		if %77> 76500 if %77<= 77000 if %10!= 94 mov %10, 94 :vsp_cl_all:vsp 113,1:print 1
		if %77> 77000 if %77<= 77500 if %10!= 95 mov %10, 95 :vsp_cl_all:vsp 114,1:print 1
		if %77> 77500 if %77<= 78000 if %10!= 96 mov %10, 96 :vsp_cl_all:vsp 115,1:print 1
		if %77> 78000 if %77<= 78500 if %10!= 97 mov %10, 97 :vsp_cl_all:vsp 116,1:print 1
		if %77> 78500 if %77<= 79000 if %10!= 98 mov %10, 98 :vsp_cl_all:vsp 117,1:print 1
		if %77> 79000 if %77<= 79500 if %10!= 99 mov %10, 99 :vsp_cl_all:vsp 118,1:print 1
		if %77> 79500 if %77<= 80000 if %10!=100 mov %10,100 :vsp_cl_all:vsp 119,1:print 1
		if %77> 80000 if %77<= 80500 if %10!=101 mov %10,101 :vsp_cl_all:vsp 120,1:print 1
		if %77> 80500 if %77<= 81000 if %10!=102 mov %10,102 :vsp_cl_all:vsp 121,1:print 1

		
		;if 経過時間 < ed再生時間 if 経過時間 > nミリ秒後に開始 if 経過時間<(nミリ秒後に開始 + nミリ秒かけて移動 * 2) - 移動にかける時間*2なら縦幅MAX600までは耐えられるはず
		;  縦window解像度 - ((縦window解像度 + 縦画像解像度 * 2 ) * (経過時間 - nミリ秒後に開始) / nミリ秒かけて移動)

		if %77<%150 if %77>31500 if %77<(31500+9000*2) amsp  1,523,600-((600+%151*2)*(%77-31500)/9000)
		if %77<%150 if %77>34000 if %77<(34000+9000*2) amsp  2,523,600-((600+%152*2)*(%77-34000)/9000)
		if %77<%150 if %77>36500 if %77<(36500+9000*2) amsp  3,523,600-((600+%153*2)*(%77-36500)/9000)
		if %77<%150 if %77>39000 if %77<(39000+9000*2) amsp  4,523,600-((600+%154*2)*(%77-39000)/9000)
		if %77<%150 if %77>43500 if %77<(43500+9000*2) amsp  5,523,600-((600+%155*2)*(%77-43500)/9000)
		if %77<%150 if %77>46000 if %77<(46000+9000*2) amsp  6,523,600-((600+%156*2)*(%77-46000)/9000)
		if %77<%150 if %77>48500 if %77<(48500+9000*2) amsp  7,523,600-((600+%157*2)*(%77-48500)/9000)
		if %77<%150 if %77>51000 if %77<(51000+9000*2) amsp  8,523,600-((600+%158*2)*(%77-51000)/9000)
		if %77<%150 if %77>55500 if %77<(55500+9000*2) amsp  9,523,600-((600+%159*2)*(%77-55500)/9000)
		if %77<%150 if %77>60000 if %77<(60000+9000*2) amsp 10,523,600-((600+%160*2)*(%77-60000)/9000)
		if %77<%150 if %77>64500 if %77<(64500+9000*2) amsp 11,523,600-((600+%161*2)*(%77-64500)/9000)
		if %77<%150 if %77>67000 if %77<(67000+9000*2) amsp 12,523,600-((600+%162*2)*(%77-67000)/9000)
		if %77<%150 if %77>70000 if %77<(70000+9000*2) amsp 13,523,600-((600+%163*2)*(%77-70000)/9000)
		if %77<%150 if %77>73000 if %77<(73000+9000*2) amsp 14,523,600-((600+%164*2)*(%77-73000)/9000)
		if %77<%150 if %77>75500 if %77<(75500+9000*2) amsp 15,523,600-((600+%165*2)*(%77-75500)/9000)

		print 1
		;12秒前にループ脱出
		if %77>(%150-12000) goto *staffroll_end1
	goto *staffroll_loop1
	*staffroll_end1

	vsp_cl_all:bg white,10

	;本当はcrd_0016もスクロールなんだけどもうしんどい
	lsp 16,"parts/frame/crd_0016.png",275,357
	bg "parts/frame/part9903.png",12

	waittimer %150
	bgmstop
	click
	saveon
return

;----------------------------------------
*start_set
	csp -1:print 10
	lsph 11,"parts/frame/frm_0101.png",69,411
	setwin 1
	print 1
return
;----------------------------------------
*start

;とりあえずどれか:%301
;Normal end:%313
;Happy end:%312
;True end:%311

;ending test
;bg white,1:def_staffroll:return

bg black,1
wait 50
bg "parts/frame/frm_0620.png",11
wait 1500
bg white,10
bgm "parts/bgm/bgm_op.ogg"

lsp 50,"parts/frame/frm_0602.png",12,42

lsp 51,":a/2,0,3;parts/frame/frm_0603.png",80,260
lsp 52,":a/2,0,3;parts/frame/frm_0604.png",80,286
lsp 53,":a/2,0,3;parts/frame/frm_0605.png",80,312
lsp 54,":a/2,0,3;parts/frame/frm_0607.png",80,338,128
if %301==1 lsp 55,":a/2,0,3;parts/frame/frm_0606.png",80,364
if %301!=1 lsp 55,":a/2,0,3;parts/frame/frm_0606.png",80,364,128
lsp 56,":a/2,0,3;parts/frame/frm_0608.png",80,390

;ここのbgが実質↑表示のprint代わり的な
bg "parts/frame/frm_0601.png",11

*title_loop
	bclear
	btrans

	spbtn 51,51
	spbtn 52,52
	spbtn 53,53
	;spbtn 54,54
	if %301==1 spbtn 55,55
	spbtn 56,56

	btnwait %10
	print 1

	if %10==51 start_set:bg black,12:wait 1000:goto *S001_A01
	if %10==52 systemcall load
	if %10==53 start_set:goto *volmenu_GUI
	if %10==54 stop:csp -1:bg black,10:gosub *def_staffroll:reset
	if %10==55 gosub *extra
	if %10==56 gosub *yesno_end
goto *title_loop
;----------------------------------------
*extra
msp 51,0,0,-128:msp 52,0,0,-128:msp 53,0,0,-128:msp 55,0,0,-128:msp 56,0,0,-128
lsp 71,":a/2,0,3;parts/frame/frm_0615.png",217,364
if %311==1 if %312==1 if %313==1 lsp 72,":a/2,0,3;parts/frame/frm_0616.png",347,364
if %311==1 if %312==1 if %313==1 lsp 73,":a/2,0,3;parts/frame/frm_0617.png",477,364
print 10

*extra_loop
	bclear
	btrans

	spbtn 71,71
	if %311==1 if %312==1 if %313==1 spbtn 72,72
	if %311==1 if %312==1 if %313==1 spbtn 73,73

	btnwait %10
	print 1

	if %10==71 start_set:bg black,12:wait 1000:goto *OM01_A01
	if %10==72 start_set:bg black,12:wait 1000:goto *OM01_B01
	if %10==73 start_set:bg black,12:wait 1000:goto *OM01_C01
	if %10!=71 if %10!=72 if %10!=73 goto *extra_end
goto *extra_loop

*extra_end
msp 51,0,0,128:msp 52,0,0,128:msp 53,0,0,128:msp 55,0,0,128:msp 56,0,0,128
csp 71:csp 72:csp 73
print 10
return
;----------------------------------------
*yesno_end
lsp 39,"parts/frame/black.png",0,0,128
lsp 38,"parts/frame/frm_0501.png",220,220

lsp 37,":a/2,0,3;parts/frame/frm_0502.png",220+67,220+114
lsp 36,":a/2,0,3;parts/frame/frm_0503.png",220+207,220+114
lsp 35,":s/24,24,0;#ffffffゲームを終了しますか？",279,268
print 10

*yesno_end_loop

	spbtn 36,36
	spbtn 37,37

	btnwait %10
	print 1
	
	if %10==36 csp 35:csp 36:csp 37:csp 38:csp 39:print 10:return
	if %10==37 start_set:bg "parts/frame/frm_0621.png",10:wait 2000:end
goto *yesno_end_loop
;----------------------------------------
*volmenu_GUI
	;https://gist.github.com/Prince-of-sea/325b8ae6912ecf23316a71c3d008480c
	;文字/数字/スプライト/ボタン
	;全部130~149までを使ってます - 競合に注意
	;改造版 voice削除

	bg #777f78,10
	
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

	print 1
	
	;ボタン定義
	bclear
	spbtn 131,131
	spbtn 132,132
	spbtn 136,136
	spbtn 138,138
	spbtn 141,141
	spbtn 143,143
	
	;入力待ち
	btnwait %140
	
	if %140==131 bgmvol 100:sevol 100:voicevol 100
	if %140==132 csp -1:reset
	if %140==136 if %130!=  0 sub %130,10:bgmvol %130
	if %140==138 if %130!=100 add %130,10:bgmvol %130
	if %140==141 if %131!=  0 sub %131,10:sevol %131
	if %140==143 if %131!=100 add %131,10:sevol %131
	
goto *volmenu_loop
;----------------------------------------

'''
	return s
#--------------------def--------------------
#吉里吉里の命令文及び変数指定をざっくりpythonの辞書に変換するやつ
def krcmd2krdict(c):
	kr_dict = {}

	for p in re.findall(r'([A-z0-9-_]+?)=(["|”|″](.*?)["|”|″]|([^\t\s]+))', c):
		kr_dict[p[0]] = p[2] if p[2] else p[3]

	return kr_dict



# ディレクトリの存在チェック関数
def dir_check(path_list):

	CHK = True
	for p in path_list:
		if not p.exists():
			print('ERROR: "' + str(p) + '" is not found!')
			CHK = False
			
	return CHK



def image_convert_main(f, cdfs):
	if not cdfs['diff']: return
	
	f_base = f.parent / (cdfs['base'] + '.png')

	im_base = Image.open(f_base)
	im_diff = Image.open(f)

	#解像度がcsv表記値と違う場合エラー(出ないはず)
	if im_diff.width != int(cdfs['w']): print('ERROR: width ' + f)
	elif im_diff.height != int(cdfs['h']): print('ERROR: height ' + f)

	im_base.paste(im_diff,(int(cdfs['x']), int(cdfs['y'])))
	im_base.save(f)



def image_convert(PATH_DICT):

	#csvから結合リスト作成
	char_dict = {}
	for f in PATH_DICT['char'].glob('*.csv'):
		with open(f, encoding='cp932', errors='ignore') as c: cr = c.read()
		f.unlink()
		for cl in cr.splitlines()[1:]:#0行目飛ばす
			cl_list = cl.split(',')

			char_dict[ cl_list[0] ] = {
				'base':cl_list[1],
				'diff':cl_list[2],
				'x':cl_list[3],
				'y':cl_list[4],
				'w':cl_list[5],
				'h':cl_list[6],
				'guidex':cl_list[7],
				'guidex':cl_list[8],
			}

	if char_dict != {}:#これ書いとくと変換後に昆布また走らせてもエラー起こさないので
		with concurrent.futures.ThreadPoolExecutor() as executor:#マルチスレッドで高速化
			futures = []
			for f in PATH_DICT['char'].glob('*.png'):
				futures.append(executor.submit(image_convert_main, f, char_dict[str(f.stem).upper()]))
			concurrent.futures.as_completed(futures)
	
	#(上の作業とは全く関係ないけど)メッセージウィンドウ右下空白作成 - PSP表示不具合対策
	msg_p = (PATH_DICT['frame'] / 'frm_0102.png')
	msg_im = Image.open(msg_p)
	if (msg_im.width == 800) and (msg_im.height == 400): return#変換済と思われる場合飛ばす
	msg_im2 = Image.new('RGBA', (800, 400), (0, 0, 0, 0))
	msg_im2.paste(msg_im, (0, 0))
	msg_im2.save(msg_p)

	

# txt置換→0.txt出力関数
def text_cnv(DEBUG_MODE, zero_txt, scenario):
	
	#if文変換時に使うgotoの連番 - 一桁はCtrl+F検索時面倒なので10スタート
	if_goto_cnt = 10
	end_goto_cnt = 10

	#default.txtを読み込み
	txt = default_txt()

	#シナリオファイル(ks)をglob
	for p in scenario.glob('*.ks'):

		#if入った際にelseの行き先とか突っ込んどく - 配列にすることでif内ifに対応
		if_list = []
		end_list = []

		#シナリオファイルを読み込み
		with open(p, encoding='cp932', errors='ignore') as f: fr = f.read()

		#デコード済みtxt一つごとに開始時改行&サブルーチン化
		if DEBUG_MODE: txt += '\n;--------------- '+ str(p.parent.name) + ' - ' + str(p.name) +' ---------------'
		txt += ('\n*'+ str(p.stem).upper() +'\n')

		#行ごとfor
		for line in fr.splitlines():

			#行頭タブ削除
			line = re.sub(r'(\t*)(.*)', r'\2', line)

			#空行ではない場合のみ処理
			if line:

				#命令
				if (line[0] == r'@'):
					line = line.lower()
					d = krcmd2krdict('kr_cmd=' + line[1:])
					kr_cmd = d['kr_cmd']
					
					#メッセージ表示後のid? とりあえず改ページ扱いで
					if (kr_cmd == 'hitret'):
						txt += ('\\\n')

					#別ks(ons基準だと別ラベル)へ飛ぶ
					elif (kr_cmd == 'change'):
						txt += ('goto *' + d['target'] + '\n')
					
					#変数ON1
					elif (kr_cmd == 'onflag'):
						id_num = int(d['id']) + 100#コンバータ側と競合を防ぐため+100
						txt += ('mov %' + str(id_num) + ',1\n')
						#print(d, line)

					#グローバル変数ON
					elif (kr_cmd == 'onglobalflag'):
						id_num = int(d['id']) + 300#コンバータ側と競合を防ぐため+300
						txt += ('mov %' + str(id_num) + ',1\n')
						#print(d, line)
					
					### if関係面倒なの ###
					elif (kr_cmd == 'if'):
						s = ''

						for e in (d['exp'].split(' && ')):
							chkflagon = re.findall(r'chkflagon\(([0-9]+)\)',e)
							chkselect = re.findall(r'chkselect\(([0-9]+)\)',e)
							chkglobalflagon = re.findall(r'chkglobalflagon\(([0-9]+)\)',e)

							if chkflagon: id_num = int(chkflagon[0]) + 100
							elif chkselect: id_num = int(chkselect[0]) + 50
							elif chkglobalflagon: id_num = int(chkglobalflagon[0]) + 300
							
							s += ('if %' + str(id_num) + '==1 ')

						s += ('goto *go' + str(if_goto_cnt) + '\n')
						s += ('goto *go' + str(if_goto_cnt+1) + '\n')
						s += ('*go' + str(if_goto_cnt) + '\n')

						if_list.append(if_goto_cnt+1)
						end_list.append(end_goto_cnt)
						if_goto_cnt += 2
						end_goto_cnt += 1

						txt += s

					elif (kr_cmd == 'elsif'):
						s = ('goto *ifend_' + str(end_list[-1]) + '\n')
						s += ('*go' + str(if_list[-1]) + '\n')
						if_list.pop()

						for e in (d['exp'].split(' && ')):
							chkflagon = re.findall(r'chkflagon\(([0-9]+)\)',e)
							chkselect = re.findall(r'chkselect\(([0-9]+)\)',e)
							chkglobalflagon = re.findall(r'chkglobalflagon\(([0-9]+)\)',e)

							if chkflagon: id_num = int(chkflagon[0]) + 100
							elif chkselect: id_num = int(chkselect[0]) + 50
							elif chkglobalflagon: id_num = int(chkglobalflagon[0]) + 300
							
							s += ('if %' + str(id_num) + '==1 ')

						s += ('goto *go' + str(if_goto_cnt) + '\n')
						s += ('goto *go' + str(if_goto_cnt+1) + '\n')
						s += ('*go' + str(if_goto_cnt) + '\n')

						if_list.append(if_goto_cnt+1)
						if_goto_cnt += 2
						txt += s
						
					elif (kr_cmd == 'else'):
						s = ('goto *ifend_' + str(end_list[-1]) + '\n')
						s += ('*go' + str(if_list[-1]) + '\n')

						if_list[-1] = 0
						txt += s
						#print(d)
						
					elif (kr_cmd == 'endif'):
						s = ''
						if if_list[-1] != 0: s += ('*go' + str(if_list[-1]) + '\n')
						s += ('*ifend_' + str(end_list[-1]) + '\n')
						
						if_list.pop()
						end_list.pop()
						txt += s
					### if関係面倒なのここまで ###

					#選択肢文章登録
					elif (kr_cmd == 'addselect'):
						txt += ('def_addselect "' + d['text'] + '"\n')

					#選択肢起動
					elif (kr_cmd == 'startselect'):
						txt += ('def_startselect\n')

					#スタッフロール
					elif (kr_cmd == 'staffroll'):
						txt += ('def_staffroll\n')

					#会話名前欄
					elif (kr_cmd == 'talk'):
						txt += ('def_talk "' + d['name'] + '"\n')

					#cgもしくは背景
					elif (kr_cmd == 'cg'):
						txt += ('def_cg "' + d['file'] + '"\n')

					#暗転
					elif (kr_cmd == 'blackout'):
						#txt += (';' + line + '\n')# 若干これでいいのか怪レい
						txt += ('def_cg "black"\n')

					#白塗り
					elif (kr_cmd == 'whiteout'):
						#txt += (';' + line + '\n')# 若干これでいいのか怪レい
						txt += ('def_cg "white"\n')

					#待ち
					elif (kr_cmd == 'wait'):
						txt += ('wait ' + d['time'] + '\n')

					#bgm再生
					elif (kr_cmd == 'playbgm'):
						txt += ('bgm "parts/bgm/' + d['file'] + '.ogg"\n')
					
					#効果音再生
					elif (kr_cmd == 'playse'):
						txt += ('dwave 1,"parts/se/' + d['file'] + '.ogg"\n')

					#繰り返し効果音(セミとか川)再生
					elif (kr_cmd == 'playenvse'):
						txt += ('dwaveloop 2,"parts/se/' + d['file'] + '.ogg"\n')
					
					#bgm停止
					elif (kr_cmd == 'stopbgm'):
						txt += ('bgmstop\n')

					#効果音停止
					elif (kr_cmd == 'stopse'):
						txt += ('dwavestop 1\n')

					#繰り返し効果音停止
					elif (kr_cmd == 'stopenvse'):
						txt += ('dwavestop 2\n')

					#キャラ表示
					elif (kr_cmd == 'char'):
						#ちなこれ中央座標っぽいで 0で真ん中
						d_x_ = d['x']
						#どうも負数を変数で管理するの挙動怪レいので別でフラグ作成
						if (d_x_[0] == '-'):
							d_x_ = d_x_[1:]
							mflug = '1'
						else:
							mflug = '0'
						txt += ('def_char "' + d['file'] + '",' + d_x_ +  ',' + mflug + '\n')

					#キャラ削除
					elif (kr_cmd == 'clearchar'):
						txt += ('def_clearchar "' + str(d.get('id')) + '"\n') #idない場合(None)あり

					#章ごとのサブタイトル的なもの？ 面倒なので無効化
					elif (kr_cmd == 'scene'):
						#txt += (';' + line + '\n')
						pass

					#Hシーン回想登録用関数っぽい 面倒なので無効化
					elif (kr_cmd == 'recollect_end'):
						#txt += (';' + line + '\n')
						pass

					#シナリオの一番初めに"time=0"とだけ よくわからん
					elif (kr_cmd == 'update'):
						#txt += (';' + line + '\n')
						pass

					#その他 - とりあえず表示(多分ない)
					else:
						print(d, line)
						txt += (';' + line + '\n')

				#命令以外
				else:
					#max27
					txt += (line + '\n')
		
		#シナリオそのまま終わってgoto先無いとき用
		txt += ('\nreset')
		
		#ifスタック消費しきってない場合バグなので表示
		if if_list != []: print('ERROR: if_conv ',if_list)

	#名前 - 初期設定へ置換
	txt = txt.replace(r'＠＠＠＠', r'倉田')
	txt = txt.replace(r'＊＊＊＊', r'誠一')
	
	#出力結果を書き込み
	open(zero_txt, 'w', encoding='cp932', errors='ignore').write(txt)

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
		'data' :(same_hierarchy / 'data'),
		'scenario' :(same_hierarchy / 'data' / 'scenario'),
		'bg' :(same_hierarchy / 'parts' / 'bg'),
		'bgm' :(same_hierarchy / 'parts' / 'bgm'),
		'char' :(same_hierarchy / 'parts' / 'char'),
		'event' :(same_hierarchy / 'parts' / 'event'),
		'frame' :(same_hierarchy / 'parts' / 'frame'),
		'se' :(same_hierarchy / 'parts' / 'se'),
	}

	PATH_DICT2 = {
		#変換後に出力されるファイル一覧
		'0_txt' :(same_hierarchy / '0.txt'),
	}

	#デバッグ用いろいろ
	if debug:
		if Path(same_hierarchy / 'stderr.txt').exists():Path(same_hierarchy / 'stderr.txt').unlink()
		if Path(same_hierarchy / 'stdout.txt').exists():Path(same_hierarchy / 'stdout.txt').unlink()
		if Path(same_hierarchy / 'envdata').exists():Path(same_hierarchy / 'envdata').unlink()
		if Path(same_hierarchy / 'gloval.sav').exists():Path(same_hierarchy / 'gloval.sav').unlink()

	#ディレクトリの存在チェック
	dir_check_result = dir_check(PATH_DICT.values())

	#存在しない場合終了
	if not dir_check_result: raise FileNotFoundError('ワンコとリリーの展開ファイルが不足しています')

	#一部画像変換
	image_convert(PATH_DICT)

	#txt置換→0.txt出力
	text_cnv(debug, PATH_DICT2['0_txt'], PATH_DICT['scenario'])

	#不要ファイル削除
	if not debug: shutil.rmtree(PATH_DICT['data'])


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()