#!/usr/bin/env python3
from PIL import Image
from pathlib import Path
import concurrent.futures
import subprocess as sp
import shutil, re

# めんどいので昔作ったソースできるだけ使いまわしてます
# 記法滅茶苦茶だけど多分動くからゆるして


def title_info():
	return {
		'brand': 'ステージ☆なな',
		'date': 20171229,
		'title': '冬のポラリス',
		'requiredsoft': ['mjdisasm'],
		'is_4:3': bool(not r'<ONS_RESOLUTION_CHECK_DISABLED>' in default_txt()),

		'version': [
			'Winter Polaris STEAM DL版(1150550 - Depot_1150553)',
		],

		'notes': [
			'原作よりシナリオ解放が厳しい、実質一本道仕様に(すべて読むこと自体はできます)',
			'雪や雨が降る場面が動かない(アニメーションしない)',
			'おまけ(スタッフルーム)の制作者選択肢を排除',
			'タイトルのwebサイトリンクが機能しない',
			'その他UI、演出、選択肢周りは大幅簡略化',
			'コンフィグ画面は音量調整のみ\nただし注意点としてPSP変換時はコンフィグ利用不可になります\n(座標合わせが面倒だったため実装諦めました ゆるして)'
		]
	}


def extract_resource(values: dict, values_ex: dict, pre_converted_dir: Path):
	from utils import extract_archive_garbro

	num_workers = values_ex['num_workers']
	input_dir = values['input_dir']

	with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
		futures = []

		for arc_name in ['data', 'fastdata', 'scenario', 'stream', 'update', 'voice']:
			p = Path(input_dir / Path(arc_name + '.arc'))
			e = Path(pre_converted_dir / arc_name)

			#なければ強制エラー
			if not p.exists(): raise ValueError(str(p)+' not found.')

			futures.append(executor.submit(extract_archive_garbro, p, e, 'png'))
		
		concurrent.futures.as_completed(futures)

	return



def default_txt():
	s = ''';$V2000G200S1024,576L10000
*define

caption "冬のポラリス for ONScripter"

rmenu "セーブする",save,"ロードする",load,"スキップする",skip,"メッセージログ",lookback,"タイトルに戻る",reset

savenumber 11
transmode alpha
globalon
rubyon
saveon
nsa
humanz 10
windowback

;自作PSP昆布用
; <ONS_RESOLUTION_CHECK_DISABLED>

effect 10,10, 500
;<<-EFFECT->>

defsub setwin
defsub msg
defsub bg_def
defsub bgm_def
defsub se_def
defsub voice_def
defsub push_def
defsub select_def
defsub bgmstopfadeout
defsub sestopfadeout
game
;----------------------------------------
;setwindow簡略化
*setwin
	getparam %1

	;横 31文字(ただし"。"とか"、"だとはみ出るもよう)
	;本来3行だけど念の為5くらいにしたほうが良き

	;通常時
	if %199==0 if %1==1 setwindow 260,390,32,5,18,18,1,4,10,1,1,#FFFFFF,0,0,1024,576
	if %199==1 if %1==1 setwindow  15,240,32,5,18,18,1,4,10,1,1,#FFFFFF,0,0, 640,363

	;二択
	if %199==0 if %1==2 setwindow 300,230,32,9,36,36,1,4,10,1,1,#999999,0,0,1024,576
	if %199==1 if %1==2 setwindow  15, 15,32,9,18,18,1,4,10,1,1,#999999,0,0, 640,363
	
return


;メッセージ周り
*msg
	;$10名前なんで結局つかわなさそう
	getparam $10,$11

	split $11,"|",$12,$13,$14

	$12
	$13
	$14
return


*bg_def
	getparam $0,%1

	mov %0,0
	if $0=="b" bg black,%1:goto *bgdefend

	fileexist %0,"update/"+$0+".png"
	if %0==1 goto *bgdefexist1
	fileexist %0,"fastdata/"+$0+".png"
	if %0==1 goto *bgdefexist2
	fileexist %0,"stream/"+$0+".png"
	if %0==1 goto *bgdefexist3
	fileexist %0,"data/"+$0+".png"
	if %0==1 goto *bgdefexist4
	fileexist %0,"voice/"+$0+".png"
	if %0==1 goto *bgdefexist5

	goto *bgdefend
	*bgdefexist1
	bg "update/"+$0+".png",%1:goto *bgdefend
	*bgdefexist2
	bg "fastdata/"+$0+".png",%1:goto *bgdefend
	*bgdefexist3
	bg "stream/"+$0+".png",%1:goto *bgdefend
	*bgdefexist4
	bg "data/"+$0+".png",%1:goto *bgdefend
	*bgdefexist5
	bg "voice/"+$0+".png",%1:goto *bgdefend

	*bgdefend
return


*bgm_def
	getparam $0

	mov %0,0
	fileexist %0,"update/"+$0+".ogg"
	if %0==1 goto *bgmdefexist1
	fileexist %0,"update/"+$0+".mp3"
	if %0==1 goto *bgmdefexist6
	fileexist %0,"fastdata/"+$0+".ogg"
	if %0==1 goto *bgmdefexist2
	fileexist %0,"fastdata/"+$0+".mp3"
	if %0==1 goto *bgmdefexist7
	fileexist %0,"stream/"+$0+".ogg"
	if %0==1 goto *bgmdefexist3
	fileexist %0,"stream/"+$0+".mp3"
	if %0==1 goto *bgmdefexist8
	fileexist %0,"data/"+$0+".ogg"
	if %0==1 goto *bgmdefexist4
	fileexist %0,"data/"+$0+".mp3"
	if %0==1 goto *bgmdefexist9
	fileexist %0,"voice/"+$0+".ogg"
	if %0==1 goto *bgmdefexist5
	fileexist %0,"voice/"+$0+".mp3"
	if %0==1 goto *bgmdefexist0

	goto *bgmdefend
	*bgmdefexist1
	bgm "update/"+$0+".ogg":goto *bgmdefend
	*bgmdefexist2
	bgm "fastdata/"+$0+".ogg":goto *bgmdefend
	*bgmdefexist3
	bgm "stream/"+$0+".ogg":goto *bgmdefend
	*bgmdefexist4
	bgm "data/"+$0+".ogg":goto *bgmdefend
	*bgmdefexist5
	bgm "voice/"+$0+".ogg":goto *bgmdefend
	*bgmdefexist6
	bgm "update/"+$0+".mp3":goto *bgmdefend
	*bgmdefexist7
	bgm "fastdata/"+$0+".mp3":goto *bgmdefend
	*bgmdefexist8
	bgm "stream/"+$0+".mp3":goto *bgmdefend
	*bgmdefexist9
	bgm "data/"+$0+".mp3":goto *bgmdefend
	*bgmdefexist0
	bgm "voice/"+$0+".mp3":goto *bgmdefend

	*bgmdefend
return


*se_def
	getparam $0,%1

	mov %0,0
	fileexist %0,"update/"+$0+".ogg"
	if %0==1 goto *sedefexist1
	fileexist %0,"update/"+$0+".wav"
	if %0==1 goto *sedefexist6
	fileexist %0,"fastdata/"+$0+".ogg"
	if %0==1 goto *sedefexist2
	fileexist %0,"fastdata/"+$0+".wav"
	if %0==1 goto *sedefexist7
	fileexist %0,"stream/"+$0+".ogg"
	if %0==1 goto *sedefexist3
	fileexist %0,"stream/"+$0+".wav"
	if %0==1 goto *sedefexist8
	fileexist %0,"data/"+$0+".ogg"
	if %0==1 goto *sedefexist4
	fileexist %0,"data/"+$0+".wav"
	if %0==1 goto *sedefexist9
	fileexist %0,"voice/"+$0+".ogg"
	if %0==1 goto *sedefexist5
	fileexist %0,"voice/"+$0+".wav"
	if %0==1 goto *sedefexist0

	goto *sedefend
	*sedefexist1
	if %1==0 dwave 1,"update/"+$0+".ogg":goto *sedefend
	if %1==1 dwaveloop 1,"update/"+$0+".ogg":goto *sedefend
	*sedefexist2
	if %1==0 dwave 1,"fastdata/"+$0+".ogg":goto *sedefend
	if %1==1 dwaveloop 1,"fastdata/"+$0+".ogg":goto *sedefend
	*sedefexist3
	if %1==0 dwave 1,"stream/"+$0+".ogg":goto *sedefend
	if %1==1 dwaveloop 1,"stream/"+$0+".ogg":goto *sedefend
	*sedefexist4
	if %1==0 dwave 1,"data/"+$0+".ogg":goto *sedefend
	if %1==1 dwaveloop 1,"data/"+$0+".ogg":goto *sedefend
	*sedefexist5
	if %1==0 dwave 1,"voice/"+$0+".ogg":goto *sedefend
	if %1==1 dwaveloop 1,"voice/"+$0+".ogg":goto *sedefend
	*sedefexist6
	if %1==0 dwave 1,"update/"+$0+".wav":goto *sedefend
	if %1==1 dwaveloop 1,"update/"+$0+".ogg":goto *sedefend
	*sedefexist7
	if %1==0 dwave 1,"fastdata/"+$0+".wav":goto *sedefend
	if %1==1 dwaveloop 1,"fastdata/"+$0+".ogg":goto *sedefend
	*sedefexist8
	if %1==0 dwave 1,"stream/"+$0+".wav":goto *sedefend
	if %1==1 dwaveloop 1,"stream/"+$0+".ogg":goto *sedefend
	*sedefexist9
	if %1==0 dwave 1,"data/"+$0+".wav":goto *sedefend
	if %1==1 dwaveloop 1,"data/"+$0+".ogg":goto *sedefend
	*sedefexist0
	if %1==0 dwave 1,"voice/"+$0+".wav":goto *sedefend
	if %1==1 dwaveloop 1,"voice/"+$0+".ogg":goto *sedefend

	*sedefend
return


*voice_def
	getparam $0

	mov %0,0
	fileexist %0,"update/"+$0+".ogg"
	if %0==1 goto *voicedefexist1
	fileexist %0,"update/"+$0+".wav"
	if %0==1 goto *voicedefexist6
	fileexist %0,"fastdata/"+$0+".ogg"
	if %0==1 goto *voicedefexist2
	fileexist %0,"fastdata/"+$0+".wav"
	if %0==1 goto *voicedefexist7
	fileexist %0,"stream/"+$0+".ogg"
	if %0==1 goto *voicedefexist3
	fileexist %0,"stream/"+$0+".wav"
	if %0==1 goto *voicedefexist8
	fileexist %0,"data/"+$0+".ogg"
	if %0==1 goto *voicedefexist4
	fileexist %0,"data/"+$0+".wav"
	if %0==1 goto *voicedefexist9
	fileexist %0,"voice/"+$0+".ogg"
	if %0==1 goto *voicedefexist5
	fileexist %0,"voice/"+$0+".wav"
	if %0==1 goto *voicedefexist0

	goto *voicedefend
	*voicedefexist1
	dwave 0,"update/"+$0+".ogg":goto *voicedefend
	*voicedefexist2
	dwave 0,"fastdata/"+$0+".ogg":goto *voicedefend
	*voicedefexist3
	dwave 0,"stream/"+$0+".ogg":goto *voicedefend
	*voicedefexist4
	dwave 0,"data/"+$0+".ogg":goto *voicedefend
	*voicedefexist5
	dwave 0,"voice/"+$0+".ogg":goto *voicedefend
	*voicedefexist6
	dwave 0,"update/"+$0+".wav":goto *voicedefend
	*voicedefexist7
	dwave 0,"fastdata/"+$0+".wav":goto *voicedefend
	*voicedefexist8
	dwave 0,"stream/"+$0+".wav":goto *voicedefend
	*voicedefexist9
	dwave 0,"data/"+$0+".wav":goto *voicedefend
	*voicedefexist0
	dwave 0,"voice/"+$0+".wav":goto *voicedefend

	*voicedefend
return


*push_def
	getparam $0
	if $71==""                                  mov $71,$0:goto *pushdefend
	if $71!="" if $72==""                       mov $72,$0:goto *pushdefend
	if $71!="" if $72!="" if $73==""            mov $73,$0:goto *pushdefend
	if $71!="" if $72!="" if $73!="" if $74=="" mov $74,$0:goto *pushdefend
	if $71!="" if $72!="" if $73!="" if $74!="" end
	*pushdefend
return


*select_def
	;選択肢出力は%79に0or1
	setwin 2
	select $73,*sel1,$74,*sel2

	*sel1
		mov %79,0:goto *selend
	*sel2
		mov %79,1:goto *selend
	
	*selend
	setwin 1
	mov $71,"":mov $72,"":mov $73,"":mov $74,""
return


*bgmstopfadeout
	getparam %0

	isskip %2
	if %2==1 stop:return

	resettimer
	*bsfoloop
		gettimer %1
		if %1>%0 mov %1,%0
		bgmvol %230*(%0-%1)/%0
		if %1==%0 goto *bsfoloop_end
	goto *bsfoloop
	*bsfoloop_end

	stop
	bgmvol %230
return

*sestopfadeout
	getparam %0

	isskip %2
	if %2==1 stop:return

	resettimer
	*bsfoloop
		gettimer %1
		if %1>%0 mov %1,%0
		sevol %231*(%0-%1)/%0
		if %1==%0 goto *bsfoloop_end
	goto *bsfoloop
	*bsfoloop_end

	dwavestop 1
	sevol %231
return
;----------------------------------------
*start

;解像度が本来のものに一致しない場合PSP仕様(%199に1代入)へ
lsph 0,"fastdata/大タイトル_null.png",0,0
getspsize 0,%0,%1
if %0==1024 mov %199,0
if %0!=1024 mov %199,1

;多分これで576pは誤魔化せる
;	普通の場合xy	:*5/%190
;	下辺合わせy		:*5/%190+%191
if %199==0 mov %190,5:mov %191,0
if %199==1 mov %190,8:mov %191,3

;初回起動時 - 初期値50/100/60
fileexist %130,"gloval.sav"
if %130==0 if %230==0 if %231==0 if %232==0 mov %230,50:mov %231,100:mov %232,60
bgmvol   %230
sevol    %231
voicevol %232

setwin 1
abssetcursor 0,":a/1,0,2;fastdata/wink.png",923*5/%190+%191,548*5/%190+%191
csp -1:print 1

bg "fastdata/大タイトル_null.png",10
wait 500
bg "fastdata/大タイトル_off.png",10

*Ltitle
bgm "stream/title.ogg"
if %199==0 strsp 30,"＞＞設定＜＜",30,520,8,1,24,24,2,3,0,1:vsp 30,0
lsph 31 "fastdata/大タイトル_on_start_.png",128*5/%190,236*5/%190
lsph 32 "fastdata/大タイトル_on_load_.png",128*5/%190,271*5/%190
lsph 33 "fastdata/大タイトル_on_end_.png",128*5/%190,306*5/%190
lsph 34 "fastdata/大タイトル_on_omake_.png",128*5/%190,341*5/%190

*Ltitle_loop
	bclear

	exbtn_d     "C30C31C32C33C34"
	exbtn 30,30,"P30C31C32C33C34"
	exbtn 31,31,"C30P31C32C33C34"
	exbtn 32,32,"C30C31P32C33C34"
	exbtn 33,33,"C30C31C32P33C34"
	exbtn 34,34,"C30C31C32C33P34"

	print 1

	btnwait %20
	if %20>=30 dwave 1,"fastdata/click.ogg"
	if %20==30 csp -1:bg black 10:goto *volmenu_GUI
	if %20==31 csp -1:goto *Stitle
	if %20==32 csp -1:lsp 97 "fastdata/sl_load_f.png",0,0:print 10:systemcall load:csp 97:print 10:goto *Ltitle
	if %20==33 csp -1:bg black 10:end
	if %20==34 csp -1:goto *staffroom

goto *Ltitle_loop
*Stitle
csp -1
bg "fastdata/小タイトル_null.png",10
if %300>=0  lsp 171 "fastdata/小タイトル_off_a1_.png", 50*5/%190,124*5/%190
if %300>=2  lsp 172 "fastdata/小タイトル_off_a2_.png",182*5/%190,124*5/%190
if %300>=4  lsp 173 "fastdata/小タイトル_off_a3_.png",314*5/%190,124*5/%190
if %300>=6  lsp 174 "fastdata/小タイトル_off_a4_.png",446*5/%190,124*5/%190
if %300>=8  lsp 175 "fastdata/小タイトル_off_a5_.png",578*5/%190, 40*5/%190
if %300>=10 lsp 176 "fastdata/小タイトル_off_a6_.png",700*5/%190, 40*5/%190
if %300>=12 lsp 177 "fastdata/小タイトル_off_a7_.png",842*5/%190, 40*5/%190
if %300>=14 lsp 178 "fastdata/小タイトル_off_a8_.png",578*5/%190,124*5/%190
if %300>=16 lsp 179 "fastdata/小タイトル_off_a9_.png",710*5/%190,124*5/%190
if %300>=1  lsp 181 "fastdata/小タイトル_off_b1_.png", 50*5/%190,230*5/%190
if %300>=3  lsp 182 "fastdata/小タイトル_off_b2_.png",182*5/%190,230*5/%190
if %300>=5  lsp 183 "fastdata/小タイトル_off_b3_.png",314*5/%190,230*5/%190
if %300>=7  lsp 184 "fastdata/小タイトル_off_b4_.png",446*5/%190,230*5/%190
if %300>=9  lsp 185 "fastdata/小タイトル_off_b5_.png",578*5/%190,230*5/%190
if %300>=11 lsp 186 "fastdata/小タイトル_off_b6_.png",710*5/%190,230*5/%190
if %300>=13 lsp 187 "fastdata/小タイトル_off_b7_.png",578*5/%190,308*5/%190
if %300>=15 lsp 188 "fastdata/小タイトル_off_b8_.png",710*5/%190,308*5/%190
if %300>=17 lsp 190 "fastdata/小タイトル_off_10_.png",839*5/%190,188*5/%190
if %300>=18 lsp 191 "fastdata/小タイトル_off_wp_.png",360*5/%190,430*5/%190
if %300>=0  lsp 192 "fastdata/小タイトル_off_re_.png",914*5/%190,331*5/%190

if %300>=0  lsph 71 "fastdata/小タイトル_on_a1_.png" , 50*5/%190,124*5/%190
if %300>=2  lsph 72 "fastdata/小タイトル_on_a2_.png" ,182*5/%190,124*5/%190
if %300>=4  lsph 73 "fastdata/小タイトル_on_a3_.png" ,314*5/%190,124*5/%190
if %300>=6  lsph 74 "fastdata/小タイトル_on_a4_.png" ,446*5/%190,124*5/%190
if %300>=8  lsph 75 "fastdata/小タイトル_on_a5_.png" ,578*5/%190, 40*5/%190
if %300>=10 lsph 76 "fastdata/小タイトル_on_a6_.png" ,700*5/%190, 40*5/%190
if %300>=12 lsph 77 "fastdata/小タイトル_on_a7_.png" ,842*5/%190, 40*5/%190
if %300>=14 lsph 78 "fastdata/小タイトル_on_a8_.png" ,578*5/%190,124*5/%190
if %300>=16 lsph 79 "fastdata/小タイトル_on_a9_.png" ,710*5/%190,124*5/%190
if %300>=1  lsph 81 "fastdata/小タイトル_on_b1_.png" , 50*5/%190,230*5/%190
if %300>=3  lsph 82 "fastdata/小タイトル_on_b2_.png" ,182*5/%190,230*5/%190
if %300>=5  lsph 83 "fastdata/小タイトル_on_b3_.png" ,314*5/%190,230*5/%190
if %300>=7  lsph 84 "fastdata/小タイトル_on_b4_.png" ,446*5/%190,230*5/%190
if %300>=9  lsph 85 "fastdata/小タイトル_on_b5_.png" ,578*5/%190,230*5/%190
if %300>=11 lsph 86 "fastdata/小タイトル_on_b6_.png" ,710*5/%190,230*5/%190
if %300>=13 lsph 87 "fastdata/小タイトル_on_b7_.png" ,578*5/%190,308*5/%190
if %300>=15 lsph 88 "fastdata/小タイトル_on_b8_.png" ,710*5/%190,308*5/%190
if %300>=17 lsph 90 "fastdata/小タイトル_on_10_.png" ,839*5/%190,188*5/%190
if %300>=18 lsph 91 "fastdata/小タイトル_on_wp_.png" ,360*5/%190,430*5/%190
if %300>=0  lsph 92 "fastdata/小タイトル_on_re_.png" ,914*5/%190,331*5/%190

;debug
;itoa2 $300,%300
;strsp 30,$300,0,0,99,99,24,24,2,3,0,1

print 10

*Stitle_loop
	bclear

	exbtn_d     "C71C72C73C74C75C76C77C78C79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 71,71,"P71C72C73C74C75C76C77C78C79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 72,72,"C71P72C73C74C75C76C77C78C79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 73,73,"C71C72P73C74C75C76C77C78C79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 74,74,"C71C72C73P74C75C76C77C78C79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 75,75,"C71C72C73C74P75C76C77C78C79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 76,76,"C71C72C73C74C75P76C77C78C79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 77,77,"C71C72C73C74C75C76P77C78C79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 78,78,"C71C72C73C74C75C76C77P78C79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 79,79,"C71C72C73C74C75C76C77C78P79C81C82C83C84C85C86C87C88C90C91C92"
	exbtn 81,81,"C71C72C73C74C75C76C77C78C79P81C82C83C84C85C86C87C88C90C91C92"
	exbtn 82,82,"C71C72C73C74C75C76C77C78C79C81P82C83C84C85C86C87C88C90C91C92"
	exbtn 83,83,"C71C72C73C74C75C76C77C78C79C81C82P83C84C85C86C87C88C90C91C92"
	exbtn 84,84,"C71C72C73C74C75C76C77C78C79C81C82C83P84C85C86C87C88C90C91C92"
	exbtn 85,85,"C71C72C73C74C75C76C77C78C79C81C82C83C84P85C86C87C88C90C91C92"
	exbtn 86,86,"C71C72C73C74C75C76C77C78C79C81C82C83C84C85P86C87C88C90C91C92"
	exbtn 87,87,"C71C72C73C74C75C76C77C78C79C81C82C83C84C85C86P87C88C90C91C92"
	exbtn 88,88,"C71C72C73C74C75C76C77C78C79C81C82C83C84C85C86C87P88C90C91C92"
	exbtn 90,90,"C71C72C73C74C75C76C77C78C79C81C82C83C84C85C86C87C88P90C91C92"
	exbtn 91,91,"C71C72C73C74C75C76C77C78C79C81C82C83C84C85C86C87C88C90P91C92"
	exbtn 92,92,"C71C72C73C74C75C76C77C78C79C81C82C83C84C85C86C87C88C90C91P92"


	print 1

	btnwait %21

	if %21==71 gosub *SCR_A01_start
	if %21==72 gosub *SCR_A02_start
	if %21==73 gosub *SCR_A03_start
	if %21==74 gosub *SCR_A04_start
	if %21==75 gosub *SCR_A05_start
	if %21==76 gosub *SCR_A06_start
	if %21==77 gosub *SCR_A07_start
	if %21==78 gosub *SCR_A08_start
	if %21==79 gosub *SCR_A09_start
	if %21==81 gosub *SCR_B01_start
	if %21==82 gosub *SCR_B02_start
	if %21==83 gosub *SCR_B03_start
	if %21==84 gosub *SCR_B04_start
	if %21==85 gosub *SCR_B05_start
	if %21==86 gosub *SCR_B06_start
	if %21==87 gosub *SCR_B07_start
	if %21==88 gosub *SCR_B08_start
	if %21==90 gosub *SCR_A10_start
	if %21==91 gosub *SCR_018_start
	if %21==92 csp -1:print 10:stop:bg "fastdata/大タイトル_off.png",10:goto *Ltitle
goto *Stitle_loop
;----------------------------------------
*SCR_A01_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A01
if %300==0 mov %300,1
csp -1:return *Stitle
;----------------------------------------
*SCR_B01_start
csp -1:bgmstopfadeout 1000:gosub *SCR_B01
if %300==1 mov %300,2
csp -1:return *Stitle
;----------------------------------------
*SCR_A02_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A02
if %300==2 mov %300,3
csp -1:return *Stitle
;----------------------------------------
*SCR_B02_start
csp -1:bgmstopfadeout 1000:gosub *SCR_B02
if %300==3 mov %300,4
csp -1:return *Stitle
;----------------------------------------
*SCR_A03_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A03
if %300==4 mov %300,5
csp -1:return *Stitle
;----------------------------------------
*SCR_B03_start
csp -1:bgmstopfadeout 1000:gosub *SCR_B03
if %300==5 mov %300,6
csp -1:return *Stitle
;----------------------------------------
*SCR_A04_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A04
if %300==6 mov %300,7
csp -1:return *Stitle
;----------------------------------------
*SCR_B04_start
csp -1:bgmstopfadeout 1000:gosub *SCR_B04
if %300==7 mov %300,8
csp -1:return *Stitle
;----------------------------------------
*SCR_A05_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A05
if %300==8 mov %300,9
csp -1:return *Stitle
;----------------------------------------
*SCR_B05_start
csp -1:bgmstopfadeout 1000:gosub *SCR_B05
if %300==9 mov %300,10
csp -1:return *Stitle
;----------------------------------------
*SCR_A06_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A06
if %300==10 mov %300,11
csp -1:return *Stitle
;----------------------------------------
*SCR_B06_start
csp -1:bgmstopfadeout 1000:gosub *SCR_B06
if %300==11 mov %300,12
csp -1:return *Stitle
;----------------------------------------
*SCR_A07_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A07
if %300==12 mov %300,13
csp -1:return *Stitle
;----------------------------------------
*SCR_B07_start
csp -1:bgmstopfadeout 1000:gosub *SCR_B07
if %300==13 mov %300,14
csp -1:return *Stitle
;----------------------------------------
*SCR_A08_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A08
if %300==14 mov %300,15
csp -1:return *Stitle
;----------------------------------------
*SCR_B08_start
csp -1:bgmstopfadeout 1000:gosub *SCR_B08
if %300==15 mov %300,16
csp -1:return *Stitle
;----------------------------------------
*SCR_A09_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A09
if %300==16 mov %300,17
csp -1:return *Stitle
;----------------------------------------
*SCR_A10_start
csp -1:bgmstopfadeout 1000:gosub *SCR_A10
if %300==17 mov %300,18
csp -1:return *Stitle
;----------------------------------------
*SCR_018_start
csp -1:bgmstopfadeout 1000:gosub *SCR_018
if %300==18 mov %300,19
csp -1:return *Stitle
;----------------------------------------
*staffroom

gosub *SCR_023:csp -1:bg black
gosub *SCR_022:csp -1:bg black
gosub *SCR_020:csp -1:bg black
gosub *SCR_019:csp -1:bg black
gosub *SCR_026:csp -1:bg black
gosub *SCR_025:csp -1:bg black
gosub *SCR_024:csp -1:bg black
gosub *SCR_021:csp -1:bg black

reset
;----------------------------------------
*volmenu_GUI
	;https://gist.github.com/Prince-of-sea/325b8ae6912ecf23316a71c3d008480c 改変版
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
	itoa2 $141,%230
	itoa2 $142,%231
	itoa2 $143,%232
	
	;バー代入
	if %230==  0 mov $146,$130
	if %230== 10 mov $146,$131
	if %230== 20 mov $146,$132
	if %230== 30 mov $146,$133
	if %230== 40 mov $146,$134
	if %230== 50 mov $146,$135
	if %230== 60 mov $146,$136
	if %230== 70 mov $146,$137
	if %230== 80 mov $146,$138
	if %230== 90 mov $146,$139
	if %230==100 mov $146,$140
	if %231==  0 mov $147,$130
	if %231== 10 mov $147,$131
	if %231== 20 mov $147,$132
	if %231== 30 mov $147,$133
	if %231== 40 mov $147,$134
	if %231== 50 mov $147,$135
	if %231== 60 mov $147,$136
	if %231== 70 mov $147,$137
	if %231== 80 mov $147,$138
	if %231== 90 mov $147,$139
	if %231==100 mov $147,$140
	if %232==  0 mov $148,$130
	if %232== 10 mov $148,$131
	if %232== 20 mov $148,$132
	if %232== 30 mov $148,$133
	if %232== 40 mov $148,$134
	if %232== 50 mov $148,$135
	if %232== 60 mov $148,$136
	if %232== 70 mov $148,$137
	if %232== 80 mov $148,$138
	if %232== 90 mov $148,$139
	if %232==100 mov $148,$140
	
	;画面作成
	lsp 130,":s;#FFFFFF［Ｃｏｎｆｉｇ］", 50+112, 50
	lsp 131,":s;#FFFFFF#666666リセット", 400+112,450
	lsp 132,":s;#FFFFFF#666666戻る",     550+112,450
	
	lsp 135,":s;#FFFFFFＢＧＭ",           50+112,150
	lsp 136,":s;#FFFFFF#666666＜",       200+112,150
	lsp 137,$146,                        250+112,150
	lsp 138,":s;#FFFFFF#666666＞",       550+112,150
	lsp 139,":s;#FFFFFF#666666"+$141,    600+112,150
	
	lsp 140,":s;#FFFFFFＳＥ",             50+112,250
	lsp 141,":s;#FFFFFF#666666＜",       200+112,250
	lsp 142,$147,                        250+112,250
	lsp 143,":s;#FFFFFF#666666＞",       550+112,250
	lsp 144,":s;#FFFFFF#666666"+$142,    600+112,250
	
	lsp 145,":s;#FFFFFFＶＯＩＣＥ",       50+112,350
	lsp 146,":s;#FFFFFF#666666＜",       200+112,350
	lsp 147,$148,                        250+112,350
	lsp 148,":s;#FFFFFF#666666＞",       550+112,350
	lsp 149,":s;#FFFFFF#666666"+$143,    600+112,350
	
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
	
	if %140==131 mov %230,100:mov %231,100:mov %232,100
	if %140==132 csp -1:reset
	if %140==136 if %230!=  0 sub %230,10
	if %140==138 if %230!=100 add %230,10
	if %140==141 if %231!=  0 sub %231,10
	if %140==143 if %231!=100 add %231,10
	if %140==146 if %232!=  0 sub %232,10
	if %140==148 if %232!=100 add %232,10
	
goto *volmenu_loop
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

	#天気系個別
	im1 = Image.open(PATH_DICT['fastdata'] / 'ame.png')
	im1_resize = im1.resize((3072, 237), Image.Resampling.LANCZOS)
	im1_resize.save(PATH_DICT['fastdata'] / 'ame_cnv.png')

	im2 = Image.open(PATH_DICT['fastdata'] / '夜ame.png')
	im2_resize = im2.resize((3072, 237), Image.Resampling.LANCZOS)
	im2_resize.save(PATH_DICT['fastdata'] / '夜ame_cnv.png')	

	im3 = Image.open(PATH_DICT['fastdata'] / 'parts_雪いっぱい.png')
	im3_resize = im3.resize((1024, 1024), Image.Resampling.LANCZOS)
	im3_crop = im3_resize.crop((0, 200, 1024, 437))
	im3_crop.save(PATH_DICT['fastdata'] / 'parts_雪いっぱい_cnv.png')

	#小タイトル
	s_title = {'a1':[ 50,124],'a2':[182,124],'a3':[314,124],'a4':[446,124],'a5':[578, 40],'a6':[700, 40],'a7':[842, 40],'a8':[578,124],'a9':[710,124],'b1':[ 50,230],'b2':[182,230],'b3':[314,230],'b4':[446,230],'b5':[578,230],'b6':[710,230],'b7':[578,308],'b8':[710,308],'10':[839,188,950,211],'wp':[360,430,650,520],'re':[914,331,992,362]}
	im4 = Image.open(PATH_DICT['fastdata'] / '小タイトル_off.png')
	im5 = Image.open(PATH_DICT['fastdata'] / '小タイトル_on.png')
	for k, v in s_title.items():
		x1 = v[0]
		y1 = v[1]
		x2 = v[2] if len(v)>2 else v[0]+120
		y2 = v[3] if len(v)>2 else v[1]+46
		im4.crop((x1, y1, x2, y2)).save(Path(PATH_DICT['fastdata'] / str('小タイトル_off_'+k+'_.png') ))
		im5.crop((x1, y1, x2, y2)).save(Path(PATH_DICT['fastdata'] / str('小タイトル_on_'+k+'_.png') ))

	#大タイトル
	l_title = {'start':[128,236],'load':[128,271],'end':[128,306],'omake':[128,341]}
	im6 = Image.open(PATH_DICT['fastdata'] / '大タイトル_on.png')
	for k, v in l_title.items():
		x1 = v[0]
		y1 = v[1]
		x2 = v[2] if len(v)>2 else v[0]+155
		y2 = v[3] if len(v)>2 else v[1]+24
		im6.crop((x1, y1, x2, y2)).save(Path(PATH_DICT['fastdata'] / str('大タイトル_on_'+k+'_.png') ))


#テキストデコード
def text_dec(PATH_DICT, values):
	if values: from utils import subprocess_args
	l = ['a01','a02','a03','a04','a05','a06','a07','a08','a09','a10','b01','b02','b03','b04','b05','b06','b07','b08','epilogue','スタッフルーム_まと','スタッフルーム_菊池','スタッフルームhieさん','スタッフルームとも','スタッフルームまとめ','スタッフルーム芹澤さん','スタッフルーム美鈴さん','ポラリススタッフルーム用_浅沼諒空']

	for n in l:
		p = (PATH_DICT['scenario'] / (n + '.mjo') )
		if values: sp.run([PATH_DICT['mjdisasm_exe'], p], shell=True, cwd=PATH_DICT['scenario'], **subprocess_args(True))
		else: sp.run([PATH_DICT['mjdisasm_exe'], p], shell=True, cwd=PATH_DICT['scenario'])



# 文字列置換
def message_replace(txt):
	cnvl = [
		['1', '１'], ['2', '２'], ['3', '３'], ['4', '４'], ['5', '５'], ['6', '６'], ['7', '７'], ['8', '８'], ['9', '９'], ['0', '０'],

		['a', 'ａ'], ['b', 'ｂ'], ['c', 'ｃ'], ['d', 'ｄ'], ['e', 'ｅ'], ['f', 'ｆ'], ['g', 'ｇ'], ['h', 'ｈ'], ['i', 'ｉ'], ['j', 'ｊ'],
		['k', 'ｋ'], ['l', 'ｌ'], ['m', 'ｍ'], ['n', 'ｎ'], ['o', 'ｏ'], ['p', 'ｐ'], ['q', 'ｑ'], ['r', 'ｒ'], ['s', 'ｓ'], ['t', 'ｔ'], 
		['u', 'ｕ'], ['v', 'ｖ'], ['w', 'ｗ'], ['x', 'ｘ'], ['y', 'ｙ'], ['z', 'ｚ'], 

		['A', 'Ａ'], ['B', 'Ｂ'], ['C', 'Ｃ'], ['D', 'Ｄ'], ['E', 'Ｅ'], ['F', 'Ｆ'], ['G', 'Ｇ'], ['H', 'Ｈ'], ['I', 'Ｉ'], ['J', 'Ｊ'], 
		['K', 'Ｋ'], ['L', 'Ｌ'], ['M', 'Ｍ'], ['N', 'Ｎ'], ['O', 'Ｏ'], ['P', 'Ｐ'], ['Q', 'Ｑ'], ['R', 'Ｒ'], ['S', 'Ｓ'], ['T', 'Ｔ'], 
		['U', '∪'], ['V', '∨'], ['W', 'Ｗ'], ['X', 'Ｘ'], ['Y', 'Ｙ'], ['Z', 'Ｚ'], 

		['%', '％'], ['!', '！'], ['?', '？'], [' ', '　'], ['ﾉ', 'ノ'], ['ｼ', 'シ'], ['{', '｛'], ['}', '｝'], ['(', '（'], [')', '）'], 
		['/', '／'], [';', '；'], [':', '：'], ['_', '＿'], ['.', '．'], ['-', '―'], ['ё', 'ｅ'], ['@', '＠'], ['*', '＊'], ['\\', '￥'], 
	]

	for v in cnvl: txt = txt.replace(v[0], v[1])
	return txt


# txt置換→0.txt出力関数
def text_cnv(DEBUG_MODE, zero_txt, scenario):

	effect_startnum = 10
	effect_list = []

	#default.txtを読み込み
	txt = default_txt()

	l = ['a01','a02','a03','a04','a05','a06','a07','a08','a09','a10','b01','b02','b03','b04','b05','b06','b07','b08','epilogue','スタッフルーム_まと','スタッフルーム_菊池','スタッフルームhieさん','スタッフルームとも','スタッフルームまとめ','スタッフルーム芹澤さん','スタッフルーム美鈴さん','ポラリススタッフルーム用_浅沼諒空']

	for cnt, n in enumerate(l):
		p_mjs = (scenario / (n + '.mjs') )
		p_sjs = (scenario / (n + '.sjs') )
		sjs_dict = {}

		#シナリオファイルを読み込み
		with open(p_mjs, encoding='cp932', errors='ignore') as f: fr_mjs = f.read()
		with open(p_sjs, encoding='cp932', errors='ignore') as f: fr_sjs = f.read()
		

		#行ごとfor
		for line in fr_sjs.splitlines():
			#テキスト辞書代入
			s_re = re.match(r'\<([0-9]{4})\> (.+)' ,line)
			sjs_dict[ s_re[1] ] = s_re[2]

		#デコード済みtxt一つごとに開始時改行&サブルーチン化
		if DEBUG_MODE: txt += '\n;--------------- '+ n +' ---------------'
		txt_name = n if (re.fullmatch(r'[a-z][0-9]{2}', n)) else str(cnt).zfill(3)
		txt += ('\n*SCR_'+ txt_name.upper() +'\n')

		#行ごとfor
		for line in fr_mjs.splitlines():

			#行頭スペース削除
			line = re.sub(r'(\s*)(.*)', r'\2', line)

			#空行ではない場合のみ処理
			if line:
				if line[0] == '#':
					#文字 例:res<0005>
					if line[:5] == '#res<':
						msg = message_replace( str(sjs_dict[ line[5:9] ]).replace(r'\n', r'|') )
						#print(msg.count(r'|'))#max2
						#print(msg.count(r'「'))#max1
						if '「' in msg:
							msg_split = msg.split('「')
							msg_name = (msg_split[0])
							msg_main = ('「'+msg_split[1])
						
						else:
							msg_name = ''
							msg_main = msg

						txt += ('msg "{msg_name}","{msg_main}"\n'.format(msg_name=msg_name, msg_main=msg_main))

					#エントリーポイント(?) 例:entrypoint $1d128f30
					elif line[:12] == '#entrypoint ':
						if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					else:
						print('ERROR: # - ' + str(line) )

				elif line[:9] == 'syscall<$':

					if line[9:17] == '15eedeaa':#bgmフェード停止?
						#例 - syscall<$15eedeaa> (2500)
						time = (line[20:24])
						if DEBUG_MODE: time = str(int(int(time)/10))#デバッグ時1/10
						txt += ('bgmstopfadeout {time}\n'.format(time=time))
						
					elif line[9:17] == '926c13e5':#SEフェードアウト?
						#例 - syscall<$926c13e5> (1200)
						time = (line[20:24])
						if DEBUG_MODE: time = str(int(int(time)/10))#デバッグ時1/10
						txt += ('sestopfadeout {time}\n'.format(time=time))

					elif line[9:17] == 'f62e3ca7':#SE?
						m = re.match(r'syscall<\$f62e3ca7> \((\'(.+?)\')(, 1)?\)', line)
						#例 - syscall<$f62e3ca7> ('door_close01')
						meirei = '1' if m[3] else '0'
						name =  m[2]
						txt += ('se_def "{name}",{meirei}\n'.format(name=name.replace('&','_'), meirei=meirei))#umi&tori対策

					# elif line[9:17] == '201d3d29':
					# 	#例 - 
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[9:17] == '5785a054':
					# 	#例 - 
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[9:17] == '718ef651':
					# 	#例 - 
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[9:17] == '83a53ffa':
					# 	#例 - 
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[9:17] == 'c0c15d7c':
					# 	#例 - 
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮


				elif line[:6] == 'call<$':


					if line[6:14] == '13059346':#wait?
						m = re.match(r'call<\$13059346, 0> \(([0-9]+)\)', line)
						#例 - call<$13059346, 0> (1000)
						time = m[1]
						if DEBUG_MODE: time = str(int(int(time)/10))#デバッグ時1/10
						txt += ('wait {time}\n'.format(time=time)) #仮

					elif line[6:14] == '13d4a7f9':#雪画像
						#例 - call<$13d4a7f9, 0>
						txt += ('lsp 98,"fastdata/parts_雪いっぱい_cnv.png",0,144*5/%190:print 10\n')

					elif line[6:14] == '2b7b2134':#雪削除?
						#例 - call<$2b7b2134, 0>
						txt += ('csp 98\n'.format(line=line))
						
					elif line[6:14] == '38ad4ae7':#雨画像
						m = re.match(r'call<\$38ad4ae7, 0> \((\'(.+?)\'|#res<([0-9]{4})>)(,\s(-)?([0-9]+))?\)', line)
						#例 - call<$38ad4ae7, 0> (#res<0299>, 1)
						#     call<$38ad4ae7, 0> ('ame', 1)
						name = (sjs_dict[ m[3] ]) if m[3] else m[2]
						txt += ('lsp 99,":a/3,100,1;fastdata/{name}_cnv.png",0,144*5/%190:print 10\n'.format(name=name))

					elif line[6:14] == '9e556879':#雨削除?
						#例 - call<$9e556879, 0> (1)
						txt += ('csp 99\n'.format(line=line))

					elif line[6:14] == '812afdf0':#声?
						m = re.match(r'call<\$812afdf0, 0> \((\'(.+?)\')\)', line)
						#例 - call<$812afdf0, 0> ('06tubaki_0110')
						name =  m[2]
						txt += ('voice_def "{name}"\n'.format(name=name))

					elif line[6:14] == 'a4eb1e4c':#背景?
						m = re.match(r'call<\$a4eb1e4c, 0> \((\'(.+?)\'(,\s(-)?([0-9]+))?|#res<([0-9]{4})>)\)', line)
						#例 - call<$a4eb1e4c, 0> ('bg1001', 1000)
						#     call<$a4eb1e4c, 0> ('bga6025', -100101)
						#     call<$a4eb1e4c, 0> ('b')
						name = (sjs_dict[ m[6] ]) if m[6] else m[2]
						time = m[5] if (m[5]!=None and m[4]==None) else '1000'
						s1, effect_startnum, effect_list = effect_edit(time, 'fade', effect_startnum, effect_list)
						txt += ('bg_def "{name}",{s1}\n'.format(name=name, s1=s1))

					elif line[6:14] == 'd334ba75':#bgm
						m = re.match(r'call<\$d334ba75, 0> \((\'(.+?)\'|#res<([0-9]{4})>)\)', line)
						#例 - call<$d334ba75, 0> ('bol_y02')
						name = (sjs_dict[ m[3] ]) if m[3] else m[2]
						txt += ('bgm_def "{name}"\n'.format(name=name))

					# elif line[6:14] == '0a4e49ab':
					# 	#例 - 
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '2828e49e':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '2f93f26a':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '3198fd01':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '35395c9f':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '5f271e74':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '6137cc81':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '7e8dee67':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '84779a85':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '8e803141':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == '9468cb12':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == 'bc417f7b':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == 'd175dfd4':
					# 	#例 - 	
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

					# elif line[6:14] == 'e9d62d7b':
					# 	#例 - 
					# 	if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

				elif line[:4] == 'push':
					m = re.match(r'push (\'([0-9]+)\'|#res<([0-9]{4})>)', line)
					text = (sjs_dict[ m[3] ]) if m[3] else m[2]
					txt += ('push_def "{text}"\n'.format(text=text))

				elif line[:1] == '@':
					txt += ('*jump_{txt_name}_{line1}\n'.format(txt_name=txt_name,line1=line[1]))

				elif line[:3] == 'jne':
					if line[5]=='1': txt += ('select_def\nif %79==1 goto *jump_{txt_name}_{line9}\n'.format(txt_name=txt_name,line9=line[9]))
					elif DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮

				elif line[:4] == 'goto':
					txt += ('goto *jump_{txt_name}_{line6}\n'.format(txt_name=txt_name,line6=line[6]))

				elif line == 'pause':
					txt += ('@\n')

				elif line == 'cls':
					txt += ('textclear\n')

				else:
					if DEBUG_MODE: txt += (';{line}\n'.format(line=line)) #仮
		
		#終わり
		txt += ('\nreturn')
	
	add0txt_effect = ''
	for i,e in enumerate(effect_list,effect_startnum+1):#エフェクト定義用の配列を命令文に&置換
		#if e[1]  ==  'fade':
			add0txt_effect +='effect '+str(i)+',10,'+e[0]+'\n'
		#else:#フェードしかないので
		#	add0txt_effect +='effect '+str(i)+',18,'+e[0]+',"'+str(e[1]).replace('"','')+'.png"\n'

	txt = txt.replace(r';<<-EFFECT->>', add0txt_effect)

	#手抜き修正
	txt = re.sub(r'@\nmsg', '@\ntextclear\nmsg', txt)

	#出力結果を書き込み
	open(zero_txt, 'w', errors='ignore').write(txt)

	return


#不要ファイル削除
def junk_del(PATH_DICT):

	shutil.rmtree(PATH_DICT['scenario'])

	for p in PATH_DICT['update'].glob('*.wav'):#updateのoggあるwav
		if Path(p.with_suffix('.ogg')).exists():Path(p).unlink()
	for p in PATH_DICT['voice'].glob('*.wav'):#voiceのoggあるwav
		if Path(p.with_suffix('.ogg')).exists():Path(p).unlink()
	for p in PATH_DICT['voice'].glob('*.ogg'):#update/voice被りogg
		if Path(PATH_DICT['update'] / p.name).exists():Path(p).unlink()
	for p in PATH_DICT['fastdata'].glob('*.cfg'):#fastdataのcfg
		Path(p).unlink()


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
		'fastdata' :(same_hierarchy / 'fastdata'),
		'data' :(same_hierarchy / 'data'),
		'scenario' :(same_hierarchy / 'scenario'),
		'stream' :(same_hierarchy / 'stream'),
		'voice' :(same_hierarchy / 'voice'),
		'update' :(same_hierarchy / 'update'),
	}

	PATH_DICT2 = {
		#変換後に出力されるファイル一覧
		'0_txt' :(same_hierarchy / '0.txt'),
	}

	if values:
		from requiredfile_locations import location
		PATH_DICT['mjdisasm_exe'] = location('mjdisasm')
	else:
		PATH_DICT['mjdisasm_exe'] = (same_hierarchy / 'mjdisasm.exe')

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

	#テキストデコード
	text_dec(PATH_DICT, values)

	#txt置換→0.txt出力
	text_cnv(debug, PATH_DICT2['0_txt'], PATH_DICT['scenario'])

	#umi&toriがffmpeg変換時"&"が原因で変換コケるのでリネーム
	Path(same_hierarchy / 'data' / 'umi&tori.wav').rename(
		Path(same_hierarchy / 'data' / 'umi_tori.wav')
	)

	#不要ファイル削除
	if not debug:junk_del(PATH_DICT)


#事前に展開済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()