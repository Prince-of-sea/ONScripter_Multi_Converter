#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import concurrent.futures
import shutil, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'Moviendo',
		'date': 20110527,
		'title': '処女回路',
		'requiredsoft': [],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),

		'version': [
			'処女回路 パッケージ版(2011/05/27)',
		],

		'notes': [
			'立ち絵の重なり順が違う&Y座標(=縦移動)がうまく動いてなさそう ※X座標(=横移動)はほぼ正常',
			'左下の顔画像表示がかなり適当、更新されなかったりそもそも出なかったり',
			'キャラの移動とメッセージ表示進行が同時に行えない(ONSの仕様)',
			'その他一部演出/セーブ/ロード/設定画面などは超簡略化',
			'スタッフロールが若干原作と違う',
			'全体的に改行がズレ気味',
			'ギャラリー未実装',
			'独自機能としてHシーンスキップ機能を(勝手に)実装',
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for xp3_name in ['bg','bgm','data','ev','face','fg','gui','rule','scenario','se','stand','voice']:
			p = Path(input_dir / Path(xp3_name + '.xp3'))
			e = Path(pre_converted_dir / xp3_name)

			#なければ強制エラー
			if not p.exists(): raise FileNotFoundError('{}が見つかりません'.format(str(p.name)))

			futures.append(executor.submit(extract_archive_garbro, p, e, 'png'))
		
		concurrent.futures.as_completed(futures)

	return


def default_txt():
	s = ''';mode800
*define

caption "処女回路 for ONScripter"

rmenu "ＳＡＶＥ",save,"ＬＯＡＤ",load,"ＳＫＩＰ",skip,"ＬＯＧ",lookback,"ＴＩＴＬＥ",reset

savenumber 18
transmode alpha
globalon
rubyon
saveon
nsa
humanz 10
windowback


;str用
numalias sename,190


;num用
numalias evmode,190
numalias ali,191
numalias min,192
numalias sal,193


;自分でもstrかnum用か把握してない立ち絵用の奴
numalias stand1name   ,160
numalias stand1costume,161
numalias stand1face   ,162
numalias stand1pose   ,163
numalias stand1yoko   ,164
numalias stand1top    ,165
numalias stand2name   ,170
numalias stand2costume,171
numalias stand2face   ,172
numalias stand2pose   ,173
numalias stand2yoko   ,174
numalias stand2top    ,175
numalias stand3name   ,180
numalias stand3costume,181
numalias stand3face   ,182
numalias stand3pose   ,183
numalias stand3yoko   ,184
numalias stand3top    ,185


;se_one,"se/sys_se_onenter.wav"- 起動menuの選択
;se_onc,"se/sys_se_onclick.wav"- 触れた時
;se_onc2,"se/sys_se_onenter2.wav"- 終了しますかyesnoとか

stralias se_one,"se/sys_se_onenter.wav"
stralias se_onc,"se/sys_se_onclick.wav"
stralias se_onc2,"se/sys_se_onenter2.wav"

effect  5,18,1000,"rule/rule_両側ブラインド2.png"
effect  6,18, 750,"rule/rule_out2in.png"
effect  7,18, 500,"rule/rule_out2in.png"
effect  8,18, 500,"rule/rule_雲1.png"
effect  9,10, 100
effect 10,10, 500
;<<-EFFECT->>

menuselectvoice "","",se_one,se_onc,"",se_onc2,se_onc2

defsub setwin
defsub facereset
defsub msgName
defsub seplay
defsub voplay
defsub sestopwait
defsub stand
defsub tatireset
defsub def_select
defsub btani_vsp0_all
defsub btani_csp_all
game
;----------------------------------------
;setwindow簡略化
*setwin
	getparam %1
	if %1==1 setwindow 190,480,24,3,24,24,0,5,10,1,1,"gui/sys_textwindow_bg.png",0,343
	if %1==2 setwindow 180,215,20,2,24,24,0,38, 0,1,1,#FFFFFF,0,0,799,599
return


;立ち絵周り全般
*stand
	;横位置 - None,左,右,中,数字ベタ書き(700とか)
	;未指定のものは前回指定から引き継ぎ、という判定みたい
	;一回だけlevel="-20"とかいうのある

	;#stand $命令,%sp番号,$名,$服,$顔,$ポーズ,$拡大,$横位置,%level,%time,%回数,%加速度,%top
	getparam $0,  %1,    $2, $3, $4, $5,    $6,   $7,    %8,    %9,   %10,  %11,   %12

	;------------------------------
	if $0!="" goto *standskip01
	;ここから立ち絵呼び出し

	;拡大(引き継ぎ保存されず)
	if $6!="" mov $15,"tb_"
	if $6=="" mov $15,""

	;stand1
	if $2!="" if %1==21 mov $stand1name,$2
	if $3!="" if %1==21 mov $stand1costume,$3
	if $4!="" if %1==21 mov $stand1face,$4
	if $5!="" if %1==21 mov $stand1pose,$5
	if $12!="" if %1==21 mov %stand1top,%12

	if $7=="左" if %1==21 mov %stand1yoko,-154
	if $7=="右" if %1==21 mov %stand1yoko,154
	if $7=="中" if %1==21 mov %stand1yoko,0
	if %1==21 if $7!="左" if $7!="右" if $7!="中" if $7!="" if $7!="0"  atoi %7,$7:mov %stand1yoko,%stand1yoko+%7

	if %1==21 mov $19,"stand/stand_"+$15+$stand1name+"_"+$stand1pose+"_"+$stand1costume+"_"+$stand1face+".png"
	if %1==21 lsp %1,$19,%stand1yoko,%stand1top:print 9

	
	;stand2
	if $2!="" if %1==22 mov $stand2name,$2
	if $3!="" if %1==22 mov $stand2costume,$3
	if $4!="" if %1==22 mov $stand2face,$4
	if $5!="" if %1==22 mov $stand2pose,$5
	if $12!="" if %1==22 mov %stand2top,%12

	if $7=="左" if %1==22 mov %stand2yoko,-154
	if $7=="右" if %1==22 mov %stand2yoko,154
	if $7=="中" if %1==22 mov %stand2yoko,0
	if %1==22 if $7!="左" if $7!="右" if $7!="中" if $7!="" if $7!="0"  atoi %7,$7:mov %stand2yoko,%stand2yoko+%7

	if %1==22 mov $19,"stand/stand_"+$15+$stand2name+"_"+$stand2pose+"_"+$stand2costume+"_"+$stand2face+".png"
	if %1==22 lsp %1,$19,%stand2yoko,%stand2top:print 9


	;stand3
	if $2!="" if %1==23 mov $stand3name,$2
	if $3!="" if %1==23 mov $stand3costume,$3
	if $4!="" if %1==23 mov $stand3face,$4
	if $5!="" if %1==23 mov $stand3pose,$5
	if $12!="" if %1==23 mov %stand3top,%12

	if $7=="左" if %1==23 mov %stand3yoko,-154
	if $7=="右" if %1==23 mov %stand3yoko,154
	if $7=="中" if %1==23 mov %stand3yoko,0
	if %1==23 if $7!="左" if $7!="右" if $7!="中" if $7!="" if $7!="0"  atoi %7,$7:mov %stand3yoko,%stand3yoko+%7

	if %1==23 mov $19,"stand/stand_"+$15+$stand3name+"_"+$stand3pose+"_"+$stand3costume+"_"+$stand3face+".png"
	if %1==23 lsp %1,$19,%stand3yoko,%stand3top:print 9

	
	;ここまで立ち絵呼び出し
	*standskip01
	;------------------------------
	if $0!="縦揺れ" goto *standskip02
	;ここから立ち絵縦揺れ

	;level0の場合とりあえず10に
	if %8==0 mov %8,10

	mov %17,0
	*styquakeloop
		resettimer
		*stymovloop
			;取得
			gettimer %16

			;超えさせない
			if %16>%9 mov %16,%9

			;sin使って滑らかに
			sin %18,180*%16/%9

			if %1==21 amsp %1,%stand1yoko,%stand1top-(%8*%18/1000):print 1
			if %1==22 amsp %1,%stand2yoko,%stand2top-(%8*%18/1000):print 1
			if %1==23 amsp %1,%stand3yoko,%stand3top-(%8*%18/1000):print 1

			print 1
			if %16==%9 goto *stymovloop_end
		goto *stymovloop
		*stymovloop_end

		inc %17
		if %17==%10 goto *styquakeloop_end
	goto *styquakeloop
	*styquakeloop_end

	;ここまで立ち絵縦揺れ
	*standskip02
	;------------------------------
	if $0!="横揺れ" goto *standskip03
	;ここから立ち絵横揺れ

	;level0の場合とりあえず10に
	if %8==0 mov %8,10

	;左右にふるため一回あたりのtimeは半分に
	mov %9,%9/2

	mov %17,0
	*stxquakeloop
		;左右にふるため二回やる - 1
		resettimer
		*stxmovloop1
			;取得
			gettimer %16

			;超えさせない
			if %16>%9 mov %16,%9

			;sin使って滑らかに
			sin %18,180*%16/%9

			if %1==21 amsp %1,%stand1yoko-(%8*%18/1000),%stand1top:print 1
			if %1==22 amsp %1,%stand2yoko-(%8*%18/1000),%stand2top:print 1
			if %1==23 amsp %1,%stand3yoko-(%8*%18/1000),%stand3top:print 1

			print 1
			if %16==%9 goto *stxmovloop1_end
		goto *stxmovloop1
		*stxmovloop1_end

		;左右にふるため二回やる - 2
		resettimer
		*stxmovloop2
			;取得
			gettimer %16

			;超えさせない
			if %16>%9 mov %16,%9

			;sin使って滑らかに
			sin %18,180*%16/%9

			if %1==21 amsp %1,%stand1yoko+(%8*%18/1000),%stand1top:print 1
			if %1==22 amsp %1,%stand2yoko+(%8*%18/1000),%stand2top:print 1
			if %1==23 amsp %1,%stand3yoko+(%8*%18/1000),%stand3top:print 1

			print 1
			if %16==%9 goto *stxmovloop2_end
		goto *stxmovloop2
		*stxmovloop2_end

		inc %17
		if %17==%10 goto *stxquakeloop_end
	goto *stxquakeloop
	*stxquakeloop_end

	;ここまで立ち絵横揺れ
	*standskip03
	;------------------------------
	if $0!="消去" goto *standskip04
	;ここから立ち絵消去
	if %1==21 mov %stand1yoko,0:mov %stand1top,0
	if %1==22 mov %stand2yoko,0:mov %stand2top,0
	if %1==23 mov %stand3yoko,0:mov %stand3top,0
	vsp %1,$10:print 9
	;ここまで立ち絵消去
	*standskip04
	;------------------------------
	if $0!="移動" goto *standskip05
	;ここから立ち絵移動

	;そのままだと遅いので半分
	mov %9,%9/2

	;元数値保管
	if %1==21 mov %17,%stand1yoko:mov %18,%stand1top
	if %1==22 mov %17,%stand2yoko:mov %18,%stand2top
	if %1==23 mov %17,%stand3yoko:mov %18,%stand3top

	;1
	if $7=="左" if %1==21 mov %stand1yoko,-154
	if $7=="右" if %1==21 mov %stand1yoko,154
	if $7=="中" if %1==21 mov %stand1yoko,0
	if %1==21 if $7!="左" if $7!="右" if $7!="中" if $7!="" if $7!="0" atoi %7,$7:mov %stand1yoko,%stand1yoko+%7

	;2
	if $7=="左" if %1==22 mov %stand2yoko,-154
	if $7=="右" if %1==22 mov %stand2yoko,154
	if $7=="中" if %1==22 mov %stand2yoko,0
	if %1==22 if $7!="左" if $7!="右" if $7!="中" if $7!="" if $7!="0" atoi %7,$7:mov %stand2yoko,%stand2yoko+%7

	;3
	if $7=="左" if %1==23 mov %stand3yoko,-154
	if $7=="右" if %1==23 mov %stand3yoko,154
	if $7=="中" if %1==23 mov %stand3yoko,0
	if %1==23 if $7!="左" if $7!="右" if $7!="中" if $7!="" if $7!="0" atoi %7,$7:mov %stand3yoko,%stand3yoko+%7
	
	resettimer

	*stmovloop
		;取得
		gettimer %16

		;超えさせない
		if %16>%9 mov %16,%9
		
		if %1==21 amsp %1, %17+(0+%stand1yoko-%17)*%16/%9, %18+(0+%stand1top-%18)*%16/%9
		if %1==22 amsp %1, %17+(0+%stand2yoko-%17)*%16/%9, %18+(0+%stand2top-%18)*%16/%9
		if %1==23 amsp %1, %17+(0+%stand3yoko-%17)*%16/%9, %18+(0+%stand3top-%18)*%16/%9


		print 1
		if %16==%9 goto *stmovloop_end
	goto *stmovloop
	
	*stmovloop_end


	;ここまで立ち絵移動
	*standskip05
	;------------------------------
	if $0!="停止待ち" goto *standskip06
	;ここから立ち絵停止待ち

	wait %9

	;ここまで立ち絵停止待ち
	*standskip06
	;------------------------------	
return

;フェイスリセット
*facereset
	vsp 2,0:vsp 3,0:vsp 4,0
return

;立ち絵リセット
*tatireset
	vsp 21,0:vsp 22,0:vsp 23,0
return

;キャラ名中央表示用座標取得
*msgName
	getparam $1

	;文字24px+幅2px=26px
	;len取得数/2=文字数(一文字で2判定っぽい)
	;文字数x26px-2px=名前全体の文字サイズ

	;キャラ名windowの横幅は165px
	;(キャラ名windowの横幅-名前全体の文字サイズ)/2=X座標

	len %1,$1
	mov %2,180+(165/2)-((%1/2)*(24+2)-2)/2

	lsp 6,"gui/sys_namebox_bg.png",180,420
	strsp 5,$1,%2,423,7,1,24,24,2,3,0,1

	;フェイス非表示
	facereset

return


;ボイス再生&フェイス
*voplay
	getparam $1
	dwave 0,"voice/"+$1+".ogg"

	;event画像表示時フェイス非表示
	if %evmode==1 vsp 2,0:vsp 3,0:vsp 4,0:return

	;$1の先頭から3文字を$2に格納する
	mid $2,$1,0,3

	if $2=="min" vsp 2,1:vsp 3,0:vsp 4,0
	if $2=="ali" vsp 2,0:vsp 3,1:vsp 4,0
	if $2=="sal" vsp 2,0:vsp 3,0:vsp 4,1

return


;効果音再生
*seplay
	getparam $1

	fileexist %1,"se/"+$1+".ogg"
	if %1==1 dwave 1,"se/"+$1+".ogg"
	if %1==0 dwave 1,"se/"+$1+".wav"

	mov $sename,$1

	resettimer
return


;効果音停止待ち
*sestopwait
	if $sename=="_sys_se_onenter2" mov %1,204
	if $sename=="se11" mov %1,1544
	if $sename=="se14" mov %1,413
	if $sename=="se18" mov %1,227
	if $sename=="se_bell01" mov %1,3631
	if $sename=="se_bgm_o_end" mov %1,114442
	if $sename=="se_bird01" mov %1,4783
	if $sename=="se_bird02" mov %1,3169
	if $sename=="se_book01" mov %1,444
	if $sename=="se_chime01" mov %1,3657
	if $sename=="se_chime02" mov %1,15975
	if $sename=="se_cloth01" mov %1,1795
	if $sename=="se_cloth02" mov %1,766
	if $sename=="se_cloth03" mov %1,2740
	if $sename=="se_cloth04" mov %1,2310
	if $sename=="se_clothing01" mov %1,3321
	if $sename=="se_clothing02" mov %1,3111
	if $sename=="se_clothing03" mov %1,9330
	if $sename=="se_dish01" mov %1,1167
	if $sename=="se_door01" mov %1,7314
	if $sename=="se_door01_1" mov %1,1921
	if $sename=="se_door01_2" mov %1,2403
	if $sename=="se_door02" mov %1,4750
	if $sename=="se_door03" mov %1,6817
	if $sename=="se_door03_1" mov %1,2653
	if $sename=="se_door03_2" mov %1,1248
	if $sename=="se_door04" mov %1,2827
	if $sename=="se_door05" mov %1,2467
	if $sename=="se_door06" mov %1,2037
	if $sename=="se_door07" mov %1,1625
	if $sename=="se_dosa01" mov %1,1018
	if $sename=="se_gata01" mov %1,3761
	if $sename=="se_gata02" mov %1,2142
	if $sename=="se_gata03" mov %1,287
	if $sename=="se_gu-01" mov %1,1080
	if $sename=="se_hyu-01" mov %1,4388
	if $sename=="se_ippon" mov %1,3918
	if $sename=="se_kagi" mov %1,940
	if $sename=="se_knob01" mov %1,708
	if $sename=="se_knock01" mov %1,757
	if $sename=="se_knock02" mov %1,2628
	if $sename=="se_knock03" mov %1,757
	if $sename=="se_knock04" mov %1,914
	if $sename=="se_kumo01" mov %1,2556
	if $sename=="se_moku" mov %1,943
	if $sename=="se_nagu01" mov %1,1541
	if $sename=="se_nagu02" mov %1,3552
	if $sename=="se_nagu03" mov %1,522
	if $sename=="se_nagu04" mov %1,1697
	if $sename=="se_onclick3" mov %1,250
	if $sename=="se_onenter3" mov %1,960
	if $sename=="se_piki01" mov %1,4101
	if $sename=="se_tell01" mov %1,15960
	if $sename=="se_tell02" mov %1,3162
	if $sename=="se_tell03" mov %1,115
	if $sename=="se_water01" mov %1,7133
	if $sename=="se_ちゃきーん" mov %1,1224
	if $sename=="se_キーボード1" mov %1,7056
	if $sename=="se_キーボード2" mov %1,3302
	if $sename=="se_ドア閉める音" mov %1,580
	if $sename=="se_ドア開ける音" mov %1,768
	if $sename=="se_ドォォォン！" mov %1,4481
	if $sename=="se_ドンッ！" mov %1,175
	if $sename=="se_バチバチバチバチッ！" mov %1,1871
	if $sename=="se_プシュー" mov %1,1350
	if $sename=="se_雷1" mov %1,2304
	if $sename=="se_魔法2" mov %1,1373
	if $sename=="sys_se_novoice" mov %1,207
	if $sename=="sys_se_onclick" mov %1,338
	if $sename=="sys_se_onclick2" mov %1,349
	if $sename=="sys_se_onclick3" mov %1,146
	if $sename=="sys_se_onenter" mov %1,46
	if $sename=="sys_se_onenter2" mov %1,207
	if $sename=="sys_se_slider" mov %1,18
	if $sename=="sys_se_slider2" mov %1,22
	*sestopwait_loop
		gettimer %2
		if %2>=%1 goto *sestopwait_end
		wait 1
	goto *sestopwait_loop

	*sestopwait_end
return

;選択肢UI - 以下ワンコとリリーコンバータから一部流用
*def_select
	getparam $61,$62,$63,$64
	mov %61,0:mov %63,0
	
	setwin 2
	;選択肢背景
	lsp 16,":a/3,0,3;gui/sys_selecter_bt.png",120,240
	lsp 17,":a/3,0,3;gui/sys_selecter_bt.png",120,300
	;メッセージウィンドウ偽装
	lsp 19,"gui/sys_textwindow_bg.png",0,343:print 1

	select $61,*ss1,
	       $63,*ss3

	*ss1
		setwin 1:csp 16:csp 17:csp 19:print 1:return $62
	*ss3
		setwin 1:csp 16:csp 17:csp 19:print 1:return $64
	
	;エラー時終了用end
end


*btani_vsp0_all
	vsp 200,0:vsp 201,0:vsp 202,0:vsp 203,0:vsp 204,0:vsp 205,0:vsp 206,0:vsp 207,0:vsp 208,0:vsp 209,0:vsp 210,0:vsp 211,0:vsp 212,0:vsp 213,0:vsp 214,0:vsp 215,0
	vsp 216,0:vsp 217,0:vsp 218,0:vsp 219,0:vsp 220,0:vsp 221,0:vsp 222,0:vsp 223,0:vsp 224,0:vsp 225,0:vsp 226,0:vsp 227,0:vsp 228,0:vsp 229,0:vsp 230,0:vsp 231,0
	vsp 232,0:vsp 233,0:vsp 234,0:vsp 235,0:vsp 236,0:vsp 237,0:vsp 238,0:vsp 239,0:vsp 240,0:vsp 241,0:vsp 242,0:vsp 243,0:vsp 244,0:vsp 245,0:vsp 246,0:vsp 247,0
return

*btani_csp_all
	csp 200:csp 201:csp 202:csp 203:csp 204:csp 205:csp 206:csp 207:csp 208:csp 209:csp 210:csp 211:csp 212:csp 213:csp 214:csp 215
	csp 216:csp 217:csp 218:csp 219:csp 220:csp 221:csp 222:csp 223:csp 224:csp 225:csp 226:csp 227:csp 228:csp 229:csp 230:csp 231
	csp 232:csp 233:csp 234:csp 235:csp 236:csp 237:csp 238:csp 239:csp 240:csp 241:csp 242:csp 243:csp 244:csp 245
	;246は最終結果なので取っておく
return
;----------------------------------------
*start
bg black,1

;文字スプライト読み込み→即削除 - 低スペック機でビットマップフォントを使った際ここで長めのロードが入る
mov %301,0:resettimer
lsph 0,":s/24,24,0;#ffffffてすと",1000,1000:csp 0:print 1


;↑の読み込みに750ms以上かかった場合低スペック機と判定
gettimer %140
if %140>750 mov %301,1


;2秒ごとに初期画面
lsp 290,"gui/sys_circlelogo_bg.png",0,0:print 10:wait 2000
lsp 290,"gui/sys_rinrilogo_1.png",0,0:print 10:wait 2000
lsp 290,"gui/sys_rinrilogo_2.png",0,0:print 10:wait 2000
lsp 290,"gui/sys_bg_white.png",0,0:print 10:wait 500


;bgm
bgm "bgm/bgm_s_01.ogg"


;ボタンアニメーション演出を先に一括読み込み
lsph 200 "gui/sys_title_btani_a_0.png" ,0,0
lsph 201 "gui/sys_title_btani_a_1.png" ,0,0
lsph 202 "gui/sys_title_btani_a_2.png" ,0,0
lsph 203 "gui/sys_title_btani_a_3.png" ,0,0
lsph 204 "gui/sys_title_btani_a_4.png" ,0,0
lsph 205 "gui/sys_title_btani_a_5.png" ,0,0
lsph 206 "gui/sys_title_btani_a_6.png" ,0,0
lsph 207 "gui/sys_title_btani_a_7.png" ,0,0
lsph 208 "gui/sys_title_btani_a_8.png" ,0,0
lsph 209 "gui/sys_title_btani_a_9.png" ,0,0
lsph 210 "gui/sys_title_btani_a_10.png",0,0
lsph 211 "gui/sys_title_btani_a_11.png",0,0
lsph 212 "gui/sys_title_btani_a_12.png",0,0
lsph 213 "gui/sys_title_btani_a_13.png",0,0
lsph 214 "gui/sys_title_btani_a_14.png",0,0
lsph 215 "gui/sys_title_btani_a_15.png",0,0
lsph 216 "gui/sys_title_btani_a_16.png",0,0
lsph 217 "gui/sys_title_btani_a_17.png",0,0
lsph 218 "gui/sys_title_btani_a_18.png",0,0
lsph 219 "gui/sys_title_btani_a_19.png",0,0
lsph 220 "gui/sys_title_btani_a_20.png",0,0
lsph 221 "gui/sys_title_btani_a_21.png",0,0
lsph 222 "gui/sys_title_btani_a_22.png",0,0
lsph 223 "gui/sys_title_btani_a_23.png",0,0
lsph 224 "gui/sys_title_btani_a_24.png",0,0
lsph 225 "gui/sys_title_btani_a_25.png",0,0
lsph 226 "gui/sys_title_btani_a_26.png",0,0
lsph 227 "gui/sys_title_btani_a_27.png",0,0
lsph 228 "gui/sys_title_btani_a_28.png",0,0
lsph 229 "gui/sys_title_btani_a_29.png",0,0
lsph 230 "gui/sys_title_btani_a_30.png",0,0
;lsph 231 "gui/sys_title_btani_a_31.png",0,0
lsph 232 "gui/sys_title_btani_a_32.png",0,0
lsph 233 "gui/sys_title_btani_a_33.png",0,0
lsph 234 "gui/sys_title_btani_a_34.png",0,0
lsph 235 "gui/sys_title_btani_a_35.png",0,0
lsph 236 "gui/sys_title_btani_a_36.png",0,0
lsph 237 "gui/sys_title_btani_a_37.png",0,0
lsph 238 "gui/sys_title_btani_a_38.png",0,0
lsph 239 "gui/sys_title_btani_a_39.png",0,0
lsph 240 "gui/sys_title_btani_a_40.png",0,0
lsph 241 "gui/sys_title_btani_a_41.png",0,0
lsph 242 "gui/sys_title_btani_a_42.png",0,0
lsph 243 "gui/sys_title_btani_a_43.png",0,0
lsph 244 "gui/sys_title_btani_a_44.png",0,0
lsph 245 "gui/sys_title_btani_a_45.png",0,0
lsph 246 "gui/sys_title_btani_a_46.png",0,0
;lsph 247 "gui/sys_title_btani_a_47.png",0,0


;ランダム背景
rnd %0,24
if %0==0  lsp 290,"bg/bg_並木_夕.png",0,0
if %0==1  lsp 290,"bg/bg_並木_夜.png",0,0
if %0==2  lsp 290,"bg/bg_並木_昼.png",0,0
if %0==3  lsp 290,"bg/bg_公園_夕.png",0,0
if %0==4  lsp 290,"bg/bg_公園_夕光.png",0,0
if %0==5  lsp 290,"bg/bg_公園_昼.png",0,0
if %0==6  lsp 290,"bg/bg_商店街_夕1.png",0,0
if %0==7  lsp 290,"bg/bg_商店街_夕2.png",0,0
if %0==8  lsp 290,"bg/bg_商店街_夜.png",0,0
if %0==9  lsp 290,"bg/bg_商店街_昼.png",0,0
if %0==10 lsp 290,"bg/bg_商店街_朝.png",0,0
if %0==11 lsp 290,"bg/bg_居間_夕.png",0,0
if %0==12 lsp 290,"bg/bg_居間_夜.png",0,0
if %0==13 lsp 290,"bg/bg_居間_昼.png",0,0
if %0==14 lsp 290,"bg/bg_研究室_夕.png",0,0
if %0==15 lsp 290,"bg/bg_研究室_夜.png",0,0
if %0==16 lsp 290,"bg/bg_研究室_昼.png",0,0
if %0==17 lsp 290,"bg/bg_空_夕.png",0,0
if %0==18 lsp 290,"bg/bg_空_夜.png",0,0
if %0==19 lsp 290,"bg/bg_空_昼.png",0,0
if %0==20 lsp 290,"bg/bg_部屋_夕.png",0,0
if %0==21 lsp 290,"bg/bg_部屋_夜.png",0,0
if %0==22 lsp 290,"bg/bg_部屋_昼.png",0,0
if %0==23 lsp 290,"bg/bg_部屋_朝.png",0,0


;上からロゴ
lsp 287,"gui/sys_title_fg_logo.png",0,0
lsp 289,"gui/sys_title_fg_logo_shadow.png",0,0

resettimer
*logo_loop
	gettimer %140
	if %140>2000 mov %140,2000
	
	amsp 287,0,-35+(35*%140/2000)
	amsp 289,0,0,128*%140/2000
	print 1

	if %140==2000 goto *logoloop_end
goto *logo_loop
*logoloop_end


;さっき読んだボタンアニメーション演出を再生
print 10
resettimer
*btani_loop
	gettimer %140
	if %140>3000 mov %140,3000
	
	mov %180,199+(48*%140/3000)
	
	;31と47は無なので
	if %180==231 mov %180,230
	if %180==247 mov %180,246

	;初回(200)は既に出てるので無視、それ以後
	if %180!=200 btani_vsp0_all:vsp %180,1:print 1
	
	if %140==3000 goto *btaniloop_end
goto *btani_loop
*btaniloop_end
btani_csp_all


;仮枠
lsp 288,"gui/sys_title_fg_main.png":print 10
wait 500


;枠&ロゴを差し替え
csp 287:csp 288:csp 289
lsp 280,"gui/sys_title_bg.png":print 5


;ボタン
csp 246
lsp 251,":a/3,0,3;gui/sys_title_bt_start.png"  ,317,337
lsp 252,":a/3,0,3;gui/sys_title_bt_load.png"   ,146,384
lsp 253,":a/3,0,3;gui/sys_title_bt_extra.png"  ,317,384
lsp 254,":a/3,0,3;gui/sys_title_bt_config.png" ,488,384
lsp 255,":a/3,0,3;gui/sys_title_bt_close.png"  ,317,431

;ボタン説明
lsph 271 "gui/sys_title_cap_start.png" ,255,530
lsph 272 "gui/sys_title_cap_load.png"  ,255,530
lsph 273 "gui/sys_title_cap_extra.png" ,255,530
lsph 274 "gui/sys_title_cap_config.png",255,530
lsph 275 "gui/sys_title_cap_end.png"   ,255,530
print 1

*endmenu_loop
	;ボタン定義
	bclear
	exbtn_d       "C271C272C273C274C275"
	exbtn 251,251,"P271C272C273C274C275"
	exbtn 252,252,"C271P272C273C274C275"
	exbtn 253,253,"C271C272P273C274C275"
	exbtn 254,254,"C271C272C273P274C275"
	exbtn 255,255,"C271C272C273C274P275"

	;入力待ち
	btnwait %190

	;デバッグ用スタッフロールテスト
	;if %190==251 dwave 1,se_onc2: gosub *SYS_STAFFROLL_KS:end

	if %190==251 dwave 1,se_onc2:goto *scenario_start
	if %190==252 dwave 1,se_onc2:gosub *load_menu
	if %190==253 dwave 1,se_onc2:gosub *extra_menu
	if %190==254 dwave 1,se_onc2:goto *volmenu_GUI
	if %190==255 dwave 1,se_onc2:gosub *end_menu
goto *endmenu_loop
;----------------------------------------
*scenario_start
setwin 1
lsp 198 "gui/_sys_dialog_base.png",0,0:print 6
lsp 197 "gui/sys_bg_black.png",0,0:print 6
csp -1:bg black 1:wait 500:stop
goto *SYS_MAIN_KS

end
;----------------------------------------
*load_menu

lsp 199,"gui/sys_common_bg.png",0,0
print 8
wait 100

systemcall load
csp 199
print 8
return
;----------------------------------------
*extra_menu

lsp 199,"gui/sys_common_bg.png",0,0
print 8
wait 100

lsp 198,"gui/_sys_dialog_base.png",0,0
strsp 197,"未実装です",400-(26*5)/2,300-(24/2),20,1,24,24,2,3,0,1
print 9
click

csp 197:csp 198
print 9

csp 199
print 8
return
;----------------------------------------
*volmenu_GUI
	;https://gist.github.com/Prince-of-sea/325b8ae6912ecf23316a71c3d008480c
	;文字/数字/スプライト/ボタン
	;全部130~159までを使ってます - 競合に注意
	
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

	lsp 199,"gui/sys_common_bg.png",0,0
	print 8
	wait 100

	lsp 198,"gui/_sys_dialog_base.png",0,0
	print 9
	
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

	;シーンスキップ
	if %300==1 mov $153,"ＯＮ"
	if %300==0 mov $153,"ＯＦＦ"
	
	;画面作成
	lsp 130,":s;#FFFFFF［Ｃｏｎｆｉｇ］", 50, 50
	lsp 131,":s;#FFFFFF#666666リセット", 400,550
	lsp 132,":s;#FFFFFF#666666戻る",     550,550
	
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

	lsp 155,":s;#FFFFFFＨシーンスキップ",   50,450
	lsp 156,":s;#FFFFFF#666666【ＯＮ】",   300,450
	lsp 158,":s;#FFFFFF#666666【ＯＦＦ】", 400,450
	lsp 159,":s;#FFFFFF#666666"+$153,     600,450

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
	spbtn 156,156
	spbtn 158,158
	
	;入力待ち
	btnwait %140
	
	if %140==131 dwave 1,se_onc2:bgmvol 100:sevol 100:voicevol 100:mov %300,0
	if %140==132 dwave 1,se_onc2:csp -1:reset
	if %140==136 dwave 1,se_onc2:if %130!=  0 sub %130,10:bgmvol %130
	if %140==138 dwave 1,se_onc2:if %130!=100 add %130,10:bgmvol %130
	if %140==141 dwave 1,se_onc2:if %131!=  0 sub %131,10:sevol %131
	if %140==143 dwave 1,se_onc2:if %131!=100 add %131,10:sevol %131
	if %140==146 dwave 1,se_onc2:if %132!=  0 sub %132,10:voicevol %132
	if %140==148 dwave 1,se_onc2:if %132!=100 add %132,10:voicevol %132
	if %140==156 dwave 1,se_onc2:mov %300,1
	if %140==158 dwave 1,se_onc2:mov %300,0
	
goto *volmenu_loop
;----------------------------------------
*end_menu

lsp 199,"gui/_sys_dialog_base.png",0,0
print 9

lsp 198,"gui/sys_dialog_bg.png",0,0
lsp 197,":a/3,0,3;gui/sys_dialog_bt_yes.png",288,218
lsp 196,":a/3,0,3;gui/sys_dialog_bt_no.png" ,425,218
strsp 195,"ゲームを終了しますか？",400-(26*11)/2,334,20,1,24,24,2,3,0,1
print 7

*endmenu_loop
	;ボタン定義
	bclear
	spbtn 197,197
	spbtn 196,196

	;入力待ち
	btnwait %190

	if %190==197 dwave 1,se_onc2:wait 300:end
	if %190==196 dwave 1,se_onc2:csp 199:csp 198:csp 197:csp 196:csp 195:print 1:return
goto *endmenu_loop
end
;----------------------------------------
*SYS_STAFFROLL_KS
;スタッフロール無理に変換せずにこっちで作っちゃおうという
csp -1:bg black,10:wait 1000

;%150 再生時間
;%151 ロール画像x - 使わん
;%152 ロール画像y
;%153 gettimer
;%154 下記参照

lsp 80,"gui/sys_staffroll_fg.png",0,0
lsp 82,"gui/sys_staffroll_bg.png",0,0
print 10
wait 500

lsp 81,"gui/sys_staffroll_text.png",0,0
getspsize 81,%151,%152

;bgm_edの再生時間
mov %150,121570
bgmonce "bgm/bgm_ed.ogg"

resettimer

*staffroll_loop
	gettimer %153

	if %153>%150 mov %153,%150
	
	;(経過時間/再生時間)*ロール画像y
	mov %154,%153*%152/%150
	
	if %153<=%150 amsp 81,0,0-%154:print 1
	if %153==%150 bgmstop:goto *staffroll_end
goto *staffroll_loop
*staffroll_end

wait 1000
csp -1
print 10

return
;----------------------------------------
'''
	return s
#--------------------def--------------------
#吉里吉里の命令文及び変数指定をざっくりpythonの辞書に変換するやつ改造版
def krcmd2krdict(c):
	kr_dict = {}

	for p in re.findall(r'([A-z0-9-_]+?|横位置|縦位置|拡大|回数|加速度|横|縦)=(["|”|″](.*?)["|”|″]|([^\t\s]+))', c):
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


#画像と長さからエフェクト番号自動生成
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


#画像変換
def image_convert(PATH_DICT):
	btani_path = (PATH_DICT['gui'] / r'sys_title_btani_a.png')	
	btani_im = Image.open(btani_path)

	k = 0

	#ここ並列にしようとするとim引数に突っ込んだタイミングでいくつか処理消えるのでしかたなくこの仕様
	for i in range( int(btani_im.height / 600) ):
		for j in range( int(btani_im.width / 800) ):
			btani_im_crop = btani_im.crop( ((j*800), (i*600), ((j+1)*800), ((i+1)*600)) )
			btani_im_crop.save( (PATH_DICT['gui'] / 'sys_title_btani_a_{k}.png'.format(k=k)))
			k += 1
	


# txt置換→0.txt出力関数
def text_cnv(DEBUG_MODE, zero_txt, scenario):
	
	#if文変換時に使うgotoの連番
	if_goto_cnt = 10
	end_goto_cnt = 10
	h_skip_cnt = 10

	effect_startnum = 10
	effect_list = []

	#default.txtを読み込み
	txt = default_txt()

	#変換ksリスト
	ks_list = [
		{'name':'sys_main.ks', 'encoding':'cp932'},
		{'name':'s_001_prologue.ks', 'encoding':'utf-16'},
		{'name':'s_002_day1.ks', 'encoding':'utf-16'},
		{'name':'s_002_day2.ks', 'encoding':'utf-16'},
		{'name':'s_002_day3.ks', 'encoding':'utf-16'},
		{'name':'s_002_day4.ks', 'encoding':'utf-16'},
		{'name':'s_002_day5.ks', 'encoding':'utf-16'},
		{'name':'s_002_day6.ks', 'encoding':'utf-16'},
		{'name':'s_003_end_alicia.ks', 'encoding':'utf-16'},
		{'name':'s_003_end_minato.ks', 'encoding':'utf-16'},
		{'name':'s_003_end_normal.ks', 'encoding':'utf-16'},
		{'name':'s_003_end_sala.ks', 'encoding':'utf-16'},
	]

	for di in ks_list:
		p = Path(scenario / di['name'])

		#if入った際にelseの行き先とか突っ込んどく - 配列にすることでif内ifに対応
		if_list = []
		end_list = []
		h_skip_stack = 0

		#iscript
		mode_iscript = False

		#シナリオファイルを読み込み
		with open(p, encoding=di['encoding'], errors='ignore') as f: fr = f.read()

		#シナリオ本編専用置換処理 - sys_main相手だとeval内の[0]とかで盛大に破綻するのでそれ回避
		if (not di['name'] == 'sys_main.ks'):
			fr = fr.replace(r'[「]', r'「')
			fr = fr.replace(r'[」]', r'」')
			fr = fr.replace(r'[', '\n[')
			fr = fr.replace(r']', ']\n')

		#patch修正分
		if (di['name'] == 's_001_prologue.ks'):
			fr = fr.replace('間接', '関節')

		#デコード済みtxt一つごとに開始時改行&サブルーチン化
		if DEBUG_MODE: txt += '\n;--------------- '+ str(p.parent.name) + ' - ' + str(p.name) +' ---------------'
		txt += ('\n*'+ str(p.name).upper().replace(r'.', r'_') +'\n')

		#行ごとfor
		for line in fr.splitlines():

			#行頭タブ削除
			line = re.sub(r'(\t*)(.*)', r'\2', line)

			#空行ではない場合のみ処理
			if line:

				#スクリプト処理
				if mode_iscript:
					if (line == r'@endscript'):
						mode_iscript = False
						if DEBUG_MODE: txt += (';;' + line + '\n')
					
					else:
						txt += (';;' + line + '\n')#仮 - やってるの変数定義だけだしこのままで良いかも
				
				#命令
				elif (line[0] == r'@') or (line[0] == r'['):
					line = line.lower()

					#@時→@消す([1:]) []時→[]消す([1:-1])
					if (line[0] == r'@'): d = krcmd2krdict('kr_cmd=' + line[1:])
					else: d = krcmd2krdict('kr_cmd=' + line[1:-1])

					kr_cmd = d['kr_cmd']
					
					#改ページ
					if (kr_cmd == 'plc'):
						txt += ('\\\n')

					#スクリプト開始
					elif (kr_cmd == 'iscript'):
						mode_iscript = True
						if DEBUG_MODE: txt += (';;' + line + '\n')

					#シナリオ呼び出し
					elif (kr_cmd == 'call'):
						storage = str(d['storage'])
						txt += (r'gosub *' + storage.upper().replace(r'.', r'_') + '\n')
					
					#gosubなどで呼ばれたシナリオ帰る
					elif (kr_cmd == 'return'):
						txt += ('return\n')

					#待ち
					elif (kr_cmd == 'wait'):
						time = str(d['time'])
						if DEBUG_MODE: time = str(int(int(time)/10))
						txt += (r'wait ' + time + '\n')

					#背景(スプライト管理)
					elif (kr_cmd == 'bg'):
						storage = str(d['storage'])
						txt += (r'lsp 255,"bg/' + storage + '.png":mov %evmode,0:facereset:tatireset\n')

					#背景(スプライト管理)
					elif (kr_cmd == 'イベント絵'):
						storage = str(d['storage'])
						txt += (r'lsp 255,"ev/' + storage + '.png":mov %evmode,1:facereset:tatireset\n')

					#変更
					elif (kr_cmd == 'tra'):
						rule = str(d.get('rule')) if d.get('rule') else 'fade'
						time = str(d.get('time')) if d.get('time') else '500'
						s1, effect_startnum, effect_list = effect_edit(time, rule, effect_startnum, effect_list)
						txt += ('print '+ s1 + '\n')

					#bgm
					elif (kr_cmd == 'bgm'):
						storage = str(d['storage'])
						txt += (r'bgm "bgm/' + storage + '.ogg"\n')

					#音楽
					elif (kr_cmd == '音楽'):
						storage = str(d['storage'])
						txt += (r'bgm "bgm/' + storage + '.ogg"\n')

					#音楽切替
					elif (kr_cmd == '音楽切替'):
						storage = str(d['storage'])
						txt += (r'bgm "bgm/' + storage + '.ogg"\n')

					#音楽停止
					elif (kr_cmd == '音楽停止'):
						txt += ('bgmstop\n')

					#音楽フェードアウト - めんどいので停止
					elif (kr_cmd == '音楽フェードアウト'):
						time = str(d.get('time')) if d.get('time') else '500'
						txt += ('wait ' + time + ':bgmstop\n')

					#voice
					elif (kr_cmd == 'voice'):
						storage = str(d['storage'])
						txt += (r'voplay "' + storage.lower() + '"\n')

					#効果音
					elif (kr_cmd == '効果音'):
						storage = str(d['storage'])
						txt += (r'seplay "' + storage.lower() + '"\n')

					#効果音フェードアウト - めんどいので停止
					elif (kr_cmd == '効果音停止'):
						txt += ('dwavestop 1\n')

					#効果音停止
					elif (kr_cmd == '効果音停止'):
						txt += ('dwavestop 1\n')

					#効果音停止待ち
					elif (kr_cmd == '効果音停止待ち'):
						txt += ('sestopwait\n')

					#名前欄
					elif (kr_cmd == 'name'):
						name = str(d['name'])
						txt += ('msgName "' + name + '"\n')

					#名前欄消す
					elif (kr_cmd == 'x'):
						txt += ('csp 5:csp 6:facereset\n')#名前window削除&フェイス非表示

					#画面左下フェイス
					elif (kr_cmd == 'face'):
						name = str(d['name'])
						costume = str(d['costume'])
						face = str(d['face'])
						pose = str(d['pose'])

						if name=='min':
							txt += (r'lsph 2,"face/face_' + name + '_' + pose + '_' + costume + '_' + face + '.png",-305,358\n')
						elif name=='ali':
							txt += (r'lsph 3,"face/face_' + name + '_' + pose + '_' + costume + '_' + face + '.png",-305,358\n')
						elif name=='sal':
							txt += (r'lsph 4,"face/face_' + name + '_' + pose + '_' + costume + '_' + face + '.png",-305,358\n')
						else:
							print('ERROR: no face')
					
					#暗転
					elif (kr_cmd == '暗転'):
						#win = str(d['win'])#たまにwin="true"表記 用途不明
						rule = str(d.get('rule')) if d.get('rule') else 'fade'
						time = str(d.get('time')) if d.get('time') else '1500'
						s1, effect_startnum, effect_list = effect_edit(time, rule, effect_startnum, effect_list)
						txt += ('lsp 255,"gui/sys_bg_black.png":csp 5:csp 6:mov %evmode,0:facereset:tatireset:print '+ s1 + '\n')

					#白転
					elif (kr_cmd == '白転'):
						#win = str(d['win'])#たまにwin="true"表記 用途不明
						rule = str(d.get('rule')) if d.get('rule') else 'fade'
						time = str(d.get('time')) if d.get('time') else '1500'
						s1, effect_startnum, effect_list = effect_edit(time, rule, effect_startnum, effect_list)
						txt += ('lsp 255,"gui/sys_bg_white.png":csp 5:csp 6:mov %evmode,0:facereset:tatireset:print '+ s1 + '\n')

					#フラッシュ
					elif (kr_cmd == 'フラッシュ'):
						time = str(d.get('time')) if d.get('time') else '100'
						s1, effect_startnum, effect_list = effect_edit(time, 'fade', effect_startnum, effect_list)
						txt += ('lsp 7,"gui/sys_bg_white.png",0,0:print '+ s1 + ':csp 7:print ' + s1 + '\n')

					#がくがく - 手抜き実装
					elif (kr_cmd == 'がくがく'):
						#yoko = str(d.get('横'))#横 0or5or10or15 めんどいので一律(onsでの)2
						#tate = str(d.get('縦'))#縦 0or5or10or15 めんどいので一律(onsでの)2
						time = str(d.get('time')) if d.get('time') else '250'
						layer = str(d.get('layer')) if d.get('layer') else 'none'

						#通常時quake
						if layer == 'none':
							txt += ('quake 2,' + time + '\n')

						#レイヤー指定時は立ち絵相手
						else:
							#立ち絵横揺れで代用(ホントは縦にも揺れるんだけどね)
							time = str(d.get('time')).replace(r'"','') if d.get('time') else '250'
							layer_ = str(24-int(layer)) #3→21 2→22 1→23 なので
							level = str(d.get('横'))
							count = str(int(int(time)/150))#100msで一回

							txt += ('stand "横揺れ",' + layer_ + ',"","","","","","0",' + level + '*2,150,' + count + ',0,0\n')

					#がくがく停止 - ons再現不可、無視
					elif (kr_cmd == 'がくがく停止'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#音楽フェードオン - めんどいので無視
					elif (kr_cmd == '音楽フェードオン'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#音楽フェードオフ - めんどいので無視
					elif (kr_cmd == '音楽フェードオフ'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#セピア
					elif (kr_cmd == 'セピア'):
						txt += ('monocro #CC8888\n')

					#色モードリセット
					elif (kr_cmd == '色モードリセット'):
						txt += ('monocro off\n')
						
					#立ち絵表示 -standは3まで 4はないよ
					elif (kr_cmd[:5] == 'stand'):

						if (kr_cmd == 'stand'): lsp_num = '21'
						elif (kr_cmd == 'stand2'): lsp_num = '22'
						elif (kr_cmd == 'stand3'): lsp_num = '23'
						else: print('ERROR: stand ',d)

						yoko_ = str(d.get('横位置')) if d.get('横位置') else '0'
						name = d['name']
						costume = d['costume']
						face = d['face']
						pose = d.get('pose') if d.get('pose') else ''
						zoom_ = d.get('拡大') if d.get('拡大') else ''
						level = d.get('level') if d.get('level') else '0'
						#page = d.get('page') if d.get('page') else '' #つかわなそう

						#stand $命令,%sp番号,$名,$服,$顔,$ポーズ,$拡大,%横位置,%level,%time,%回数,%加速度,%top
						txt += ('stand "",' + lsp_num + ',"' + name + '","' + costume + '","' + face + '","' + pose + '","' + zoom_ + '","' + yoko_ + '",' + level + ',0,0,0,0\n')
						
					#立ち絵
					elif (kr_cmd[:3] == '立ち絵'):
						st_eff = re.match(r'立ち絵(1|2|3)?(.+)', kr_cmd)

						lsp_num = st_eff[1] if st_eff[1] else '1'
						lsp_num = ('2' + lsp_num)#21~23に

						yoko_ = str(d.get('横位置')).replace(r'"','') if d.get('横位置') else '0'
						time = str(d.get('time')).replace(r'"','') if d.get('time') else '250'
						count = d.get('回数').replace(r'"','') if d.get('回数') else '0'
						accel = d.get('加速度').replace(r'"','') if d.get('加速度') else '0'
						level = d.get('level').replace(r'"','') if d.get('level') else '0'

						if d.get('top'): top = d.get('top').replace(r'"','')
						elif d.get('縦位置'): top = d.get('縦位置').replace(r'"','')
						else: top = '0'

						#stand $命令,%sp番号,$名,$服,$顔,$ポーズ,$拡大,%横位置,%level,%time,%回数,%加速度,%top
						txt += ('stand "' + st_eff[2] + '",' + lsp_num + ',"","","","","","' + yoko_ + '",' + level + ',' + time + ',' + count + ',' + accel + ',' + top + '\n')
					
					#jump
					elif (kr_cmd == 'jump'):
						#storage = d.get('storage')#sys_title.ks - タイトル画面に戻る、なんだけどsys_mainしか使われてないので放棄
						target = d.get('target')
						cond = d.get('cond')

						if cond: txt += ('if ' + str(cond).replace('f.','%') + ' ')
						if target:
							txt += ('goto ' + target + '\n')
							

					#フラグ
					elif (kr_cmd == 'フラグ'):
						#sf.～ のやつは無視
						st_eff = re.match(r'f\.(sal|min|ali)(\+\+|\+=2)', d['exp'])
						
						if st_eff:
							if st_eff[2] == '++': txt += ('mov %' + st_eff[1] + ',%' + st_eff[1] + '+1,\n')
							else: txt += ('mov %' + st_eff[1] + ',%' + st_eff[1] + '+2,\n')			

					#if
					elif (kr_cmd == 'if'):
						s = ''

						s += ('if ' + d['exp'].replace('f.','%') + ' ')

						s += ('goto *go' + str(if_goto_cnt) + '\n')
						s += ('goto *go' + str(if_goto_cnt+1) + '\n')
						s += ('*go' + str(if_goto_cnt) + '\n')

						if_list.append(if_goto_cnt+1)
						end_list.append(end_goto_cnt)
						if_goto_cnt += 2
						end_goto_cnt += 1

						txt += s

					#endif
					elif (kr_cmd == 'endif'):
						s = ''
						if if_list[-1] != 0: s += ('*go' + str(if_list[-1]) + '\n')
						#s += ('*ifend_' + str(end_list[-1]) + '\n')
						
						if_list.pop()
						end_list.pop()
						txt += s
					
					#選択肢 
					elif (kr_cmd == '選択肢'):
						#caption="(ここに選択肢１, 同２)" target="(*select_00x_1,*select_00x_2)"			
						cap_ma = re.match(r'\((.+?), (.+?)\)', d['caption']) #caption
						tg_ma = re.match(r'\((\*[A-z0-9-_]+?),(\*[A-z0-9-_]+?)\)', d['target']) #target

						txt += ('def_select "' + cap_ma[1] + '","' + tg_ma[1] + '","' + cap_ma[2] + '","' + tg_ma[2] + '"\n')

					#回想ここから
					elif (kr_cmd == '回想ここから'):
						if h_skip_stack == 0:
							h_skip_stack = h_skip_cnt
							txt += ('if %300!=0 strsp 0,"ｓｃｅｎｅ　ｓｋｉｐ．．．",400,550,20,1,24,24,2,3,0,1:print 10:wait 2000:goto *h_skip_' + str(h_skip_stack) + '\n')
						else:
							print('ERROR: h_skip start')

					#回想ここまで
					elif (kr_cmd == '回想ここまで'):
						if h_skip_stack != 0:
							txt += ('*h_skip_' + str(h_skip_stack) + '\n')
							txt += ('if %300!=0 csp 0:print 10\n')
							h_skip_stack = 0
							h_skip_cnt += 1
						else:
							print('ERROR: h_skip end')

					#全レイヤー消去
					elif (kr_cmd == '全レイヤー消去'):
						txt += ('csp -1\n')

					#ウィンドウ表示 - onsは勝手にやるので無効化しても問題なし
					elif (kr_cmd == 'ウィンドウ表示'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#ウィンドウ消去 - onsは勝手にやるので無効化しても問題なし
					elif (kr_cmd == 'ウィンドウ消去'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#eval - exモードとhシーンの開放変数の管理しかしてなさそうなので無効化しても問題なし
					elif (kr_cmd == 'eval'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#シナリオ開始 - 無効化しても問題なし
					elif (kr_cmd == 'シナリオ開始'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#シナリオ終了 - 無効化しても問題なし
					elif (kr_cmd == 'シナリオ終了'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#s - 無効化しても問題なし
					elif (kr_cmd == 's'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#選択肢終了待ち - 無効化しても問題なし
					elif (kr_cmd == '選択肢終了待ち'):
						if DEBUG_MODE: txt += (';' + line + '\n')

					#その他 - とりあえず表示(多分ない)
					else:
						#print(d)#, line)
						txt += (';' + line + '\n')

				#元々コメントアウト - デバッグ時強調、通常時非表示
				elif (line[0] == r';'):
					if DEBUG_MODE: txt += (';;;;' + line + '\n')

				#krkr側ラベル
				elif (line[0] == r'*'):
					if line[:7] != '*label_':
						kr_lb = re.match(r'(\*[A-z0-9-_]+)\|?(.+)?', line)
				
						#|手前のみ活かす
						if (kr_lb[1][:8]=='*select_') or (kr_lb[1]=='*end') or (kr_lb[1]=='*skipstaff'):
							txt += (kr_lb[1] + '\n')
						else:
							#print(line)
							txt += (';' + line + '\n')
					
					else:
						if DEBUG_MODE: txt += (';' + line + '\n')

				#命令以外
				else:
					#max27
					txt += (line + '\n')
		
		#シナリオそのまま終わってgoto先無いとき用
		txt += ('\nreset')
		
		#ifスタック消費しきってない場合バグなので表示
		if if_list != []: print('ERROR: if_conv ',if_list)
		if h_skip_stack != 0: print('ERROR: h_skip_conv ',if_list)
	
	
	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換
		if e[1] == 'fade':
			add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'
		else:
			add0txt_effect +='effect '+str(i)+',18,'+e[0]+',"rule/'+str(e[1]).replace('"','')+'.png"\n'

	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)

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
		'data' :(same_hierarchy / 'data'),
		'bg' :(same_hierarchy / 'bg'),
		'bgm' :(same_hierarchy / 'bgm'),
		'ev' :(same_hierarchy / 'ev'),
		'face' :(same_hierarchy / 'face'),
		'gui' :(same_hierarchy / 'gui'),
		'rule' :(same_hierarchy / 'rule'),
		'scenario' :(same_hierarchy / 'scenario'),
		'se' :(same_hierarchy / 'se'),
		'stand' :(same_hierarchy / 'stand'),
		'voice' :(same_hierarchy / 'voice'),
		
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
	if not dir_check_result: return

	#一部画像変換
	image_convert(PATH_DICT)

	#txt置換→0.txt出力
	text_cnv(debug, PATH_DICT2['0_txt'], PATH_DICT['scenario'])

	#不要ファイル削除
	if not debug:
		shutil.rmtree(PATH_DICT['data'])
		shutil.rmtree(PATH_DICT['scenario'])


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()