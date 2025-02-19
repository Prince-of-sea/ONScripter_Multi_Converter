#!/usr/bin/env python3
from pathlib import Path
import shutil, re


def title_info():
	return {
		'brand': 'いつものところ',
		'date': 19991226,
		'title': 'Kanoso ～思い出を壊す物語～',
		'requiredsoft': [],
		'is_4:3': True,
		
		'version': [
			'Kanoso ～思い出を壊す物語～ Web DL版(kanoso.zip)',# https://web.archive.org/web/20050803042427if_/http://www.cokage.ne.jp/~hiiragi/game/kanoso.zip
		],

		'notes': [
			'セーブ/ロードなどを右クリックから行えるように',
			'一部画像遷移が原作と若干違う',
			'元々CD-DAを使う作品です\nkanon(原作)のCDからWAV音源を抽出し、\n"cd/trackXX.wav"(XXはトラックの数字二桁)に\nセットしてから変換してください'
		]
	}


# メイン関数
def main(values: dict = {}, values_ex: dict = {}, pre_converted_dir: Path = Path.cwd()):

	if values:
		from utils import openread0x84bitxor # type: ignore

		input_dir = values['input_dir'] 

		for i in range(0,7):
			p1 = Path(input_dir / '{}.scp'.format(i))
			p2 = Path(pre_converted_dir / '{}.txt'.format(i))
			with open(p2, mode='w', encoding='cp932') as f: f.write(openread0x84bitxor(p1))

		for jpg_name in ['0107', '0108', '0109', '0110', '0111', '0112', '0113', '0114', '0115', '0116', '0117', '0118', '0119', '0120', '0121', '0122', '0123', '0124', '0125', '0126', '0127', '0128', '0129', '0130', '0131', 'a00', 'a01', 'a02', 'a03', 'a04', 'a05', 'a06', 'a07', 'a08', 'a09', 'a10', 'a11', 'a12', 'a13', 'a14', 'a15', 'a16', 'a17', 'a18', 'a19', 'a20', 'a21', 'a22', 'a23', 'a24', 'a25', 'a26', 'a27', 'a28', 'a29', 'a30', 'a31', 'a32', 'a33', 'a34', 'b01', 'b02', 'b03', 'b04', 'b05', 'b06', 'b07', 'b08', 'b09', 'b10', 'b11', 'b12', 'b13', 'b14', 'b15', 'b16', 'b17', 'b18', 'b19', 'b20', 'b21', 'b22', 'b23', 'b24', 'b25', 'b26', 'b27', 'b28', 'b29', 'b30', 'b31', 'b32', 'b33', 'b34', 'c01', 'c02', 'c03', 'c04', 'c05', 'c08', 'c18', 'c28', 'd09', 'd10', 'd11', 'd12', 'd13', 'd14', 'd15', 'd16', 'd17', 'd18', 'd19', 'd20', 'd33', 'e09', 'e10', 'e11', 'e12', 'e13', 'e14', 'e15', 'e16', 'e17', 'e18', 'e19', 'e20', 'e33', 'ed01', 'ed02', 'ed03', 'ed04', 'ed05', 'ed06', 'ed07', 'ed08', 'ed09', 'ed10', 'ed11', 'ed12', 'ed13', 'ed14', 'ed15', 'ed16', 'ed17', 'ed18', 'ed19', 'ed20', 'ed21', 'ed22', 'ed23', 'ed24', 'ed25', 'ed26', 'ed27', 'ed30', 'ed31', 'ed33', 'ed36', 'ed37', 'ed41', 'f01', 'f02', 'f03', 'f04', 'f05', 'f07', 'f09', 'f10', 'f14', 'f20', 'f21', 'f22', 'f23', 'f24', 'f25', 'f29', 'f30', 'f33', 'g01', 'g02', 'g03', 'g04', 'g05', 'g07', 'g09', 'g20', 'g21', 'g22', 'g23', 'g24', 'g25', 'g29', 'g30', 'g33', 'h01', 'h02', 'h09', 'h11', 'h13', 'h15', 'h16', 'h20', 'h21', 'h22', 'h23', 'h24', 'h25', 'h26', 'h27', 'h28', 'i01', 'i02', 'i09', 'i11', 'i13', 'i15', 'i16', 'i20', 'i22', 'i23', 'i24', 'i25', 'i26', 'i27', 'i28', 'j09', 'j11', 'j13', 'j15', 'j18', 'j22', 'j24', 'j33', 'JO', 'k01', 'k02', 'k03', 'k04', 'k05', 'k06', 'k07', 'k09', 'k11', 'k13', 'k18', 'k20', 'k21', 'k22', 'k23', 'k24', 'k25', 'k28', 'k33', 'l01', 'l02', 'l03', 'l04', 'l05', 'l06', 'l07', 'l08', 'l11', 'l20', 'l21', 'l22', 'l23', 'l24', 'l25', 'l28', 'l33', 'm09', 'm10', 'm11', 'm13', 'm15', 'm18', 'm20', 'm22', 'm28', 'm33', 'mo01', 'mo02', 'mo03', 'mo04', 'mo05', 'mo06', 'mo07', 'mo08', 'mo09', 'mo10', 'mo11', 'mo12', 'mo13', 'mo14', 'mo15', 'mo16', 'mo17', 'mo18', 'mo19', 'mo20', 'mo21', 'mo22', 'mo23', 'mo24', 'mo25', 'n09', 'n11', 'n13', 'n15', 'n17', 'n18', 'n19', 'n20', 'n22', 'n33', 'o02', 'o07', 'o09', 'o11', 'o13', 'o15', 'o18', 'o20', 'o21', 'o22', 'o23', 'o24', 'o25', 'o28', 'o29', 'o30', 'o33', 'op01', 'op02', 'op03', 'op04', 'op05', 'op06', 'op07', 'op08', 'op09', 'op10', 'op11', 'op12', 'op13', 'op14', 'op15', 'op16', 'op17', 'op18', 'op19', 'op20', 'op21', 'op22', 'op23', 'op24', 'op25', 'op26', 'op27', 'op28', 'op29', 'op30', 'op31', 'op32', 'op33', 'op34', 'op35', 'op36', 'op37', 'op38', 'op39', 'op40', 'op41', 'op42', 'op43', 'op44', 'op45', 'op46', 'op47', 'op48', 'op49', 'op50', 'op51', 'op52', 'op53', 'P01', 'P02', 'P03', 'P04', 'P05', 'P06', 'P07', 'P08', 'P20', 'P21', 'P22', 'P23', 'P24', 'P28', 'P29', 'P33', 'q02', 'q20', 'tai1', 'tai2', 'tai3', 'z001', 'z001a', 'z002', 'z002a', 'z003', 'z003a', 'z004', 'z004a', 'z005', 'z005a', 'z006', 'z007', 'z007a', 'z008', 'z008a', 'z101', 'z101a', 'z102', 'z102a', 'z103', 'z103a', 'z104', 'z104a', 'z105', 'z105a', 'z106', 'z106a', 'z107', 'z107a', 'z108', 'z108a', 'z109', 'z109a', 'z110', 'z110a', 'z111', 'z111a', 'z112', 'z113', 'z114', 'z114a', 'z115', 'z116', 'z117', 'z117a', 'z118', 'z118a', 'z201', 'z201a', 'z202', 'z202a', 'z202b', 'z202c', 'z203', 'z203a', 'z204', 'z204a', 'z205', 'z205a', 'z206', 'z206a', 'z207', 'z207a', 'z208', 'z208a', 'z209', 'z209a', 'z210', 'z211', 'z212', 'z213', 'z214', 'z215', 'z215a', 'z216', 'z216a', 'z217', 'z217a', 'z218', 'z218a', 'z219', 'z220', 'z221', 'z222', 'z223', 'z223a', 'z224', 'z225', 'z225a', 'z226', 'z226a', 'z301', 'z301a', 'z302', 'z302a', 'z303', 'z303a', 'z304', 'z305', 'z305a', 'z306', 'z306a', 'z307', 'z307a', 'z308', 'z309', 'z309a', 'z310', 'z310a', 'z311', 'z311a', 'z312', 'z312a', 'z313', 'z313a', 'z314', 'z314a', 'z315', 'z315a', 'z316', 'z316a', 'z317', 'z318', 'z318a', 'z319', 'z320', 'z321', 'z322', 'z323', 'z324', 'z325', 'z326', 'z326a', 'z401', 'z401a', 'z402', 'z402a', 'z403', 'z403a', 'z404', 'z404a', 'z405', 'z405a', 'z406', 'z406a', 'z407', 'z407a', 'z408', 'z408a', 'z409', 'z409a', 'z410', 'z410a', 'z411', 'z411a', 'z412', 'z412a', 'z413', 'z414', 'z415', 'z416', 'z417', 'z417a', 'z418', 'z418a', 'z419', 'z420', 'z420a', 'z421', 'z421a', 'z422', 'z423', 'z423a', 'z424', 'z425', 'z426', 'z426a', 'z501', 'z501a', 'z502', 'z502a', 'z503', 'z503a', 'z504', 'z504a', 'z506', 'z506a', 'z507', 'z507a', 'z508', 'z508a', 'z509', 'z509a', 'z510', 'z510a', 'z511', 'z511a', 'z512', 'z512a', 'z512b', 'z512c', 'z513', 'z513a', 'z514', 'z514a', 'z515', 'z515a', 'z516', 'z516a', 'z517', 'z518', 'z519', 'z519a', 'z520', 'z522', 'z523', 'z524', 'z524a']:
			shutil.copy(Path(input_dir / '{}.jpg'.format(jpg_name)), pre_converted_dir)
	
	debug = 0

	if debug:
		pre_converted_dir /= '_test'
		cmd_list = []
		eff_list = []

	txt = '''*define
rmenu "セーブ",save,"ロード",load,"スキップ",skip,"リセット",reset
transmode copy:globalon:saveon:windowback:savenumber 15

;よくわかんないのは全部n,10,500
effect 20,1
effect  3,10,500
effect  5, 6,500
effect  7, 8,500
effect 12,11,500
effect 13,13,500

numalias bgnum,50:numalias cdnum,51
numalias fontwsize ,60:numalias fonthsize ,61:numalias fontwspace,62:numalias fonthspace,63
numalias pagex,68:numalias pagey,69: numalias txtx,70:numalias txty,71

defsub setwin
defsub print_def

game
*setwin
	setwindow %pagex,%pagey,%txtx,%txty,%fontwsize,%fonthsize,%fontwspace,%fonthspace,1,1,1,#FFFFFF,0,0,639,479:return

*print_def
	getparam %1
	if $bgnum=="" print %1:return
	if $bgnum!="" bg $bgnum,%1:return

*start
bg black 1
'''

	for i in range(0,7):
		p = Path(pre_converted_dir / '{}.txt'.format(i))
		with open(p, encoding='cp932', errors='ignore') as f: s = f.read()

		select_cnt = 0
		a_z_lower = str.maketrans('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')

		for line in s.translate(a_z_lower).splitlines():
			cmd_line = re.match(r'([a-z]+)', line)

			if not line: pass
			elif line[0] == r'*':
				label_line = re.match(r'\*([A-z0-9]+)', line)
				line = '*label_{}\ntrap off'.format(label_line[1])

			elif select_cnt:
				select_cnt_line = re.match(r'"(.+?)",?\*([A-z0-9]+)', line)
				line = '"{}",*label_{},'.format(select_cnt_line[1], select_cnt_line[2])#onsだとダメなラベル数字スタートがたまにあるので前に"label_"
				select_cnt -= 1
				if not select_cnt : line = line[:-1]#これで最後の選択肢なら末尾","削除

			elif cmd_line:
				#参考: https://web.archive.org/web/20000930084234if_/http://www2.osk.3web.ne.jp:80/~naokikun/scr3.lzh
				match cmd_line[1]:
					case 'media': line = (';' + line)
					case 'quit': line = 'end'
					case 'end': line = 'reset'			
					case 'bg':#onsのbgと違ってセットするだけ
						bg_line = re.match(r'bg[\s\t]+(black|white|"(.+?)")', line)
						if bg_line[1] == 'black': arg = '>1000,1000,#000000'#本当は640x480で足りるけどここ結構バグる機種多いので念の為大きく取る
						elif bg_line[1] == 'white': arg = '>1000,1000,#FFFFFF'
						else: arg = bg_line[2]
						line = 'mov $bgnum,"{}"'.format(arg)

					case 'print':#第二引数は無視
						print_line = re.match(r'print[\s\t]+([0-9]+)', line)
						num = int(print_line[1]) if (not print_line[1] in ['0', '1']) else (int(print_line[1])+20)#0と1はonsで予約済みなので
						line = 'print_def {}'.format(num)
						if debug: eff_list.append(num)
						
					case 'bp':#bg/print複合、onsのbgに近い感じ(まぁlspで管理するけど)
						bp_line = re.match(r'bp[\s\t]+(black|white|"(.+?)"),([0-9]+)', line)
						if bp_line[1] == 'black': arg = '>1000,1000,#000000'#本当は640x480で足りるけどここ結構バグる機種多いので念の為大きく取る
						elif bp_line[1] == 'white': arg = '>1000,1000,#FFFFFF'
						else: arg = bp_line[2]
						num = int(bp_line[3]) if (not bp_line[3] in ['0', '1']) else (int(bp_line[3])+20)#0と1はonsで予約済みなので
						line = 'mov $bgnum,"{}":print_def {}'.format(arg, num)
						if debug: eff_list.append(num)
					
					case 'quakex':
						quakex_line = re.match(r'quakex[\s\t]+([0-9]+)', line)
						line = 'quakex {},500'.format(quakex_line[1])

					case 'quakey':
						quakey_line = re.match(r'quakey[\s\t]+([0-9]+)', line)
						line = 'quakey {},500'.format(quakey_line[1])
					
					case 'cd':
						cd_line = re.match(r'cd[\s\t]+([0-9]+)', line)
						line = 'mov $cdnum,"*{}"'.format(cd_line[1])
					
					case 'loop':
						loop_line = re.match(r'loop[\s\t]+(on|off)', line)
						if (loop_line[1] == 'on'): line = 'play $cdnum'
						else: line = 'playonce $cdnum'

					case 'font':
						font_line = re.match(r'font[\s\t]+([0-9]+),([0-9]+),([0-9]+),([0-9]+),', line)
						line = 'mov %fontwsize,{}:mov %fonthsize,{}:mov %fontwspace,{}:mov %fonthspace,{}'.format(
							font_line[1], font_line[2], font_line[3], font_line[4])

					case 'window':#なんか調子悪いのでコメントアウト
						# window_line = re.match(r'window[\s\t]+([0-9]+),([0-9]+),([0-9]+),([0-9]+)', line)
						# line = 'mov %winstartx,{}:mov %winstarty,{}:mov %winendx,{}:mov %winendy,{}'.format(
						# 	window_line[1], window_line[2], window_line[3], window_line[4])
						line = (';' + line)
						
					case 'page':
						page_line = re.match(r'page[\s\t]+([0-9]+),([0-9]+),([0-9]+),([0-9]+)', line)
						line = 'mov %pagex,{}:mov %pagey,{}:mov %txtx,{}:mov %txty,{}:setwin'.format(
							page_line[1], page_line[2], page_line[3], page_line[4])
					
					case 'goto':
						goto_line = re.match(r'goto[\s\t]\*([A-z0-9]+)', line)
						line = 'goto *label_{}'.format(goto_line[1])#onsだとダメなラベル数字スタートがたまにあるので前に"label_"
					
					case 'trap':
						trap_line = re.match(r'trap[\s\t]\*([A-z0-9]+)', line)
						line = 'trap *label_{}'.format(trap_line[1])#onsだとダメなラベル数字スタートがたまにあるので前に"label_"

					case 'select':
						select_line = re.match(r'select[\s\t]+([0-9]+)', line)
						select_cnt = int(select_line[1])
						line = 'select "",*start,'#行合わせのためダミー作っとく、どうせ選択肢空文字なら表示されないので

					case _:
						if (not cmd_line[1] in ['resettimer', 'waittimer', 'caption', 'stop', ]): pass#ほっといていいやつ
						else:
							line = (';' + line)
							if debug: cmd_list.append(cmd_line[1])
			
			else:#表示文字全角チェック - 本当はここもmaketrans使ったほうが良い(書いてから気づいた)
				for r in [['(', '（'], [')', '）'], ['/', '／'], ['^', '＾'], ['~', '～'], [':', '：'], [';', '；'], ]: line = line.replace(r[0], r[1])

			txt += (line + '\n')

	if debug:#デバッグ時
		print('\n未実装/未変換命令: {}\nsc3側利用effect: {}'.format(set(cmd_list), sorted(set(eff_list))))#命令周り表示
		with open(Path(pre_converted_dir / '00.txt'), mode='w', encoding='cp932') as f: f.write(txt)#00.txtに保存

	else:#通常時
		for i in range(0,7): Path(pre_converted_dir / '{}.txt'.format(i)).unlink()#元のtxt消す
		with open(Path(pre_converted_dir / '0.txt'), mode='w', encoding='cp932') as f: f.write(txt)#0.txtに保存

	return


#事前にシナリオ復号化(nscript.datと同じ)済みなら一応単体でも動作するようにしておく
if __name__ == "__main__":
	main()