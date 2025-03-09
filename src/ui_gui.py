#!/usr/bin/env python3
import win32console, win32gui
import dearpygui.dearpygui as dpg

from hardwarevalues_config import gethardwarevalues_full, gethardwarevalues
from utils import get_titlesettingfull, get_meipass
from ui_gui2 import (  #最低限以外のui周りはui_gui2でやる
	ask_create_disabledvideofile,
	ask_decode_nscriptdat,
	ask_convert_start,
	copyrights,
	open_garbro,
	open_repositorieslink,
	open_licensespy,
	open_input,
	open_select,
	open_output,
	desktop_output,
	close_dpg,
)
from process_notons import get_titledict


def refresh_state(sender, app_data, user_data):
	dpg.set_viewport_title(f'ONScripter Multi Converter for {user_data[0]} ver.{user_data[1]}')
	
	for key, value in gethardwarevalues(user_data[0], 'values_default').items():
		dpg.set_value(key, value)
	return	


def gui_main(version: str, charset_param: str, hw_key: str, input_dir_param: str, output_dir_param: str, title_setting_param: str):

	#コマンドプロンプトのウィンドウハンドルを取得
	console_window = win32console.GetConsoleWindow()

	#ウィンドウを最小化
	win32gui.ShowWindow(console_window, 6) #SW_MINIMIZE
	print('GUIモード起動中...\nこのウィンドウを閉じないようにしてください')

	#ハードウェア値取得
	hardwarevalues_full = gethardwarevalues_full()
	values_default = gethardwarevalues(hw_key, 'values_default')

	#個別設定名登録
	title_setting_list = ['None']
	if (charset_param == 'cp932'): title_setting_list += list(get_titledict().keys())#個別設定はcp932時のみ有効
	
	dpg.create_context()

	with dpg.font_registry():
		with dpg.font(file=r'C:/Windows/Fonts/meiryo.ttc', size=16) as default_font:
			dpg.add_font_range_hint(dpg.mvFontRangeHint_Japanese)
		dpg.bind_font(default_font)

	window_title = f'ONScripter Multi Converter for {hw_key} ver.{version}'

	dpg.create_viewport(title=window_title, width=640, height=400, small_icon=str(get_meipass('__icon.ico')), large_icon=str(get_meipass('__icon.ico')), resizable=False)

	with dpg.window(label='Main Window', tag='Main Window', no_resize=True) as window:
		with dpg.menu_bar():
			with dpg.menu(label='設定'):
				dpg.add_menu_item(label='CPU使用率低減モード', check=True, default_value=False, tag='lower_cpu_usage')
				with dpg.menu(label='ハード変更'):
					for hwk, hwv in hardwarevalues_full.items():
						if (charset_param in hwv['values_ex']['support_charset']):
							dpg.add_menu_item(label=hwv['values_ex']['hardware_full'], user_data=(hwk, version), callback=refresh_state)

				dpg.add_menu_item(label='終了', callback=close_dpg)

			with dpg.menu(label='ツール'):
				dpg.add_menu_item(label='連番動画無効化ファイル作成', callback=ask_create_disabledvideofile)
				dpg.add_menu_item(label='nscript.dat復号化', user_data=(charset_param), callback=ask_decode_nscriptdat)
				dpg.add_menu_item(label='GARbroを起動', callback=open_garbro)

			with dpg.menu(label='このソフトについて'):
				dpg.add_menu_item(label='サイトを開く', callback=open_repositorieslink)
				dpg.add_menu_item(label='権利者表記', user_data=(version), callback=copyrights)
				if get_meipass('licenses_py.txt').is_file(): dpg.add_menu_item(label='ライセンス', callback=open_licensespy)

		with dpg.group(horizontal=True):
			dpg.add_text('入力元：　')
			dpg.add_input_text(tag='input_dir', readonly=True)
			dpg.add_button(label='Browse', callback=open_input, tag='input_browse_btn')
			dpg.add_button(label='一覧から選択', user_data=(charset_param), callback=open_select, tag='input_select_btn')

		with dpg.group(horizontal=True):
			dpg.add_text('出力先：　')
			dpg.add_input_text(tag='output_dir', readonly=True)
			dpg.add_button(label='Browse', callback=open_output, tag='output_browse_btn')
			dpg.add_button(label='既定値に設定', callback=desktop_output, tag='output_desktop_btn')

		with dpg.group(horizontal=True):
			dpg.add_text('個別設定：')
			dpg.add_combo(
				tag='title_setting',
				default_value=(get_titlesettingfull(title_setting_param) if charset_param=='cp932' else 'None'),
				items=title_setting_list,
			)

		# with dpg.child_window(height=220, border=False):
		with dpg.tab_bar():
			with dpg.tab(label='画像'):
				with dpg.child_window(height=200, border=False):
					with dpg.tree_node(label='基本設定', default_open=True):
						with dpg.group(horizontal=True):
							dpg.add_text('変換する際の解像度が複数選択可能な場合：')
							dpg.add_radio_button(
								items=('高解像度優先', '低解像度優先'),
								default_value=values_default['preferred_resolution'],
								horizontal=True,
								tag='preferred_resolution',
							)
						with dpg.group(horizontal=True):
							dpg.add_text('JPEG品質：')
							dpg.add_slider_int(
								label='',
								default_value=values_default['img_jpgquality_bar'],
								min_value=0,
								max_value=100,
								tag='img_jpgquality_bar',
							)
						with dpg.group(horizontal=True):
							dpg.add_checkbox(label='PNGを減色：', default_value=values_default['img_pngquantize_chk'], tag='img_pngquantize_chk')
							dpg.add_combo(
								label='色',
								items=('256', '192', '128'),
								default_value=values_default['img_pngquantize_num'],
								fit_width=True,
								tag='img_pngquantize_num',
							)
					with dpg.tree_node(label='詳細設定', default_open=True):
						dpg.add_checkbox(
							label='''透過形式"l","r"以外のBMPを検出しJPEGへ変換''',
							default_value=values_default['img_bmptojpg_chk'],
							tag='img_bmptojpg_chk',
						)
						with dpg.group(horizontal=True):
							dpg.add_checkbox(
								label='''一般的な非PNGの横解像度を特定の倍数にする：''',
								default_value=values_default['img_multi_chk'],
								tag='img_multi_chk',
							)
							dpg.add_combo(
								label='の倍数',
								items=(
									'1',
									'2',
									'3',
									'4',
								),
								default_value=values_default['img_multi_num'],
								fit_width=True,
								tag='img_multi_num',
							)

			with dpg.tab(label='音楽'):
				with dpg.child_window(height=200, border=False):
					with dpg.tree_node(label='基本設定', default_open=True):
						with dpg.group(horizontal=True):
							dpg.add_text('BGMフォーマット：')
							dpg.add_radio_button(
								items=('OGG', 'MP3', 'WAV'),
								default_value=values_default['aud_bgmfmt_radio'],
								horizontal=True,
								tag='aud_bgmfmt_radio',
							)
						with dpg.group(horizontal=True):
							dpg.add_text('SE/VOICEフォーマット：')
							dpg.add_radio_button(
								items=('OGG', 'MP3', 'WAV'),
								default_value=values_default['aud_sefmt_radio'],
								horizontal=True,
								tag='aud_sefmt_radio',
							)
						with dpg.group(horizontal=True):
							dpg.add_text('SE/BGMチャンネル数：')
							dpg.add_radio_button(
								items=('ステレオ', 'モノラル'),
								default_value=values_default['aud_bgmch_radio'],
								horizontal=True,
								tag='aud_bgmch_radio',
							)
						with dpg.group(horizontal=True):
							dpg.add_text('SE/VOICEチャンネル数：')
							dpg.add_radio_button(
								items=('ステレオ', 'モノラル'),
								default_value=values_default['aud_sech_radio'],
								horizontal=True,
								tag='aud_sech_radio',
							)
					with dpg.tree_node(label='詳細設定', default_open=True):
						with dpg.tree_node(label='OGG変換時', default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text('BGMビットレート：')
								dpg.add_combo(
									label='kbps',
									items=(
										'192',
										'160',
										'128',
										'112',
										'96',
										'64',
										'56',
										'48',
										'32',
									),
									default_value=values_default['aud_oggbgm_kbps'],
									fit_width=True,
									tag='aud_oggbgm_kbps',
								)
								dpg.add_combo(
									label='Hz',
									items=('44100', '22050', '11025'),
									default_value=values_default['aud_oggbgm_hz'],
									fit_width=True,
									tag='aud_oggbgm_hz',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('SE/VOICEビットレート：')
								dpg.add_combo(
									label='kbps',
									items=(
										'192',
										'160',
										'128',
										'112',
										'96',
										'64',
										'56',
										'48',
										'32',
									),
									default_value=values_default['aud_oggse_kbps'],
									fit_width=True,
									tag='aud_oggse_kbps',
								)
								dpg.add_combo(
									label='Hz',
									items=('44100', '22050', '11025'),
									default_value=values_default['aud_oggse_hz'],
									fit_width=True,
									tag='aud_oggse_hz',
								)
						with dpg.tree_node(label='MP3変換時', default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text('BGMビットレート：')
								dpg.add_combo(
									label='kbps',
									items=(
										'192',
										'160',
										'128',
										'112',
										'96',
										'64',
										'56',
										'48',
										'32',
									),
									default_value=values_default['aud_mp3bgm_kbps'],
									fit_width=True,
									tag='aud_mp3bgm_kbps',
								)
								dpg.add_combo(
									label='Hz',
									items=('44100', '22050', '11025'),
									default_value=values_default['aud_mp3bgm_hz'],
									fit_width=True,
									tag='aud_mp3bgm_hz',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('SE/VOICEビットレート：')
								dpg.add_combo(
									label='kbps',
									items=(
										'192',
										'160',
										'128',
										'112',
										'96',
										'64',
										'56',
										'48',
										'32',
									),
									default_value=values_default['aud_mp3se_kbps'],
									fit_width=True,
									tag='aud_mp3se_kbps',
								)
								dpg.add_combo(
									label='Hz',
									items=('44100', '22050', '11025'),
									default_value=values_default['aud_mp3se_hz'],
									fit_width=True,
									tag='aud_mp3se_hz',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('BGMカットオフ周波数：')
								dpg.add_combo(
									label='Hz',
									items=(
										'18000',
										'16500',
										'15000',
										'13500',
										'12000',
										'10500',
										'9000',
										'7500',
									),
									default_value=values_default['aud_mp3bgm_cutoff'],
									fit_width=True,
									tag='aud_mp3bgm_cutoff',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('SE/VOICEカットオフ周波数：')
								dpg.add_combo(
									label='Hz',
									items=(
										'18000',
										'16500',
										'15000',
										'13500',
										'12000',
										'10500',
										'9000',
										'7500',
									),
									default_value=values_default['aud_mp3se_cutoff'],
									fit_width=True,
									tag='aud_mp3se_cutoff',
								)
						with dpg.tree_node(label='WAV変換時', default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text('BGMビットレート：')
								dpg.add_combo(
									label='Hz',
									items=('44100', '22050', '11025'),
									default_value=values_default['aud_wavbgm_hz'],
									fit_width=True,
									tag='aud_wavbgm_hz',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('SE/VOICEビットレート：')
								dpg.add_combo(
									label='Hz',
									items=('44100', '22050', '11025'),
									default_value=values_default['aud_wavse_hz'],
									fit_width=True,
									tag='aud_wavse_hz',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('BGMコーデック：')
								dpg.add_radio_button(
									items=('pcm_s16le', 'pcm_u8'),
									default_value=values_default['aud_bgmcodec_radio'],
									horizontal=True,
									tag='aud_bgmcodec_radio',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('SEコーデック：')
								dpg.add_radio_button(
									items=('pcm_s16le', 'pcm_u8'),
									default_value=values_default['aud_secodec_radio'],
									horizontal=True,
									tag='aud_secodec_radio',
								)

			with dpg.tab(label='動画'):
				with dpg.child_window(height=200, border=False):
					with dpg.tree_node(label='基本設定', default_open=True):
						with dpg.group(horizontal=True):
							dpg.add_text('動画フォーマット：')
							dpg.add_radio_button(
								items=('連番画像', 'MJPEG', 'MP4', '変換しない'),
								default_value=values_default['vid_movfmt_radio'],
								horizontal=True,
								tag='vid_movfmt_radio',
							)
					with dpg.tree_node(label='詳細設定', default_open=True):
						with dpg.tree_node(label='連番画像変換時', default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text('画像フォーマット：')
								dpg.add_radio_button(
									items=('PNG', 'JPEG'),
									default_value=values_default['vid_renbanfmt_radio'],
									horizontal=True,
									tag='vid_renbanfmt_radio',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('解像度 - %指定：')
								dpg.add_radio_button(
									items=(
										'100%(1/1)',
										'75%(3/4)',
										'66%(2/3)',
										'50%(1/2)',
										'33%(1/3)',
										'25%(1/4)',
									),
									default_value=values_default['vid_renbanres_radio'],
									horizontal=False,
									tag='vid_renbanres_radio',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(label='連番PNGを減色：',default_value=values_default['vid_renbanpngquantize_chk'], tag='vid_renbanpngquantize_chk')
								dpg.add_combo(
									label='色',
									items=('256', '192', '128', '96', '64', '32'),
									default_value=values_default['vid_renbanpngquantize_num'],
									fit_width=True,
									tag='vid_renbanpngquantize_num',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('JPEG利用時品質：')
								dpg.add_slider_int(
									label='',
									default_value=values_default['vid_renbanjpgquality_bar'],
									min_value=0,
									max_value=100,
									tag='vid_renbanjpgquality_bar',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('音声変換時の設定：')
								dpg.add_radio_button(
									items=('BGMに合わせる', 'SE/VOICEに合わせる'),
									default_value=values_default['vid_renbanaudset_radio'],
									horizontal=False,
									tag='vid_renbanaudset_radio',
								)
						with dpg.tree_node(label='MJPEG変換時', default_open=True):
							with dpg.group(horizontal=False):
								dpg.add_text('動画品質 - 数字が少ないほど高品質：')
								dpg.add_slider_int(
									label='',
									default_value=values_default['vid_mjpegquality_bar'],
									min_value=1,
									max_value=30,
									tag='vid_mjpegquality_bar',
								)
						with dpg.tree_node(label='MP4変換時', default_open=True):
							with dpg.group(horizontal=False):
								dpg.add_text('動画品質 - 数字が少ないほど高品質：')
								dpg.add_slider_int(
									label='',
									default_value=values_default['vid_mp4quality_bar'],
									min_value=1,
									max_value=30,
									tag='vid_mp4quality_bar',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('音声ビットレート：')
								dpg.add_combo(
									label='kbps',
									items=(
										'192',
										'160',
										'128',
										'112',
										'96',
										'64',
										'56',
										'48',
										'32',
									),
									default_value=values_default['vid_mp4aud_kbps'],
									fit_width=True,
									tag='vid_mp4aud_kbps',
								)
								dpg.add_combo(
									label='Hz',
									items=('44100', '22050', '11025'),
									default_value=values_default['vid_mp4aud_hz'],
									fit_width=True,
									tag='vid_mp4aud_hz',
								)

			with dpg.tab(label='その他'):
				with dpg.child_window(height=200, border=False):
					with dpg.tree_node(label='基本設定', default_open=True):
						with dpg.tree_node(label='ファイル関連', default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text('画像圧縮先：')
								dpg.add_combo(
									label='',
									items=('arc.nsa', 'arc1.nsa', 'arc2.nsa', '圧縮しない'),
									default_value=values_default['etc_filecompimg_nsa'],
									fit_width=True,
									tag='etc_filecompimg_nsa',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('BGM圧縮先：')
								dpg.add_combo(
									label='',
									items=('arc.nsa', 'arc1.nsa', 'arc2.nsa', '圧縮しない'),
									default_value=values_default['etc_filecompbgm_nsa'],
									fit_width=True,
									tag='etc_filecompbgm_nsa',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('SE/VOICE圧縮先：')
								dpg.add_combo(
									label='',
									items=('arc.nsa', 'arc1.nsa', 'arc2.nsa', '圧縮しない'),
									default_value=values_default['etc_filecompse_nsa'],
									fit_width=True,
									tag='etc_filecompse_nsa',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('連番利用時動画圧縮先：')
								dpg.add_combo(
									label='',
									items=('arc.nsa', 'arc1.nsa', 'arc2.nsa', '圧縮しない'),
									default_value=values_default['etc_filecomprenban_nsa'],
									fit_width=True,
									tag='etc_filecomprenban_nsa',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='''拡張子".dll"のファイルを全て除外''',
									default_value=values_default['etc_fileexdll_chk'],
									tag='etc_fileexdll_chk',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='''ファイル"Thumbs.db"を全て除外''',
									default_value=values_default['etc_fileexdb_chk'],
									tag='etc_fileexdb_chk',
								)
						with dpg.tree_node(label='ons.ini関連(PSP用)', default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text('画面表示：')
								dpg.add_combo(
									label='',
									items=('拡大しない', '拡大(比率維持)', '拡大(フルサイズ)'),
									default_value=values_default['etc_iniscreen'],
									fit_width=True,
									tag='etc_iniscreen',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='常にメモリ内にフォントを読み込んでおく',
									default_value=values_default['etc_iniramfont_chk'],
									tag='etc_iniramfont_chk',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='マウスカーソルを利用',
									default_value=values_default['etc_inicursor_chk'],
									tag='etc_inicursor_chk',
								)
					with dpg.tree_node(label='詳細設定', default_open=True):
						with dpg.tree_node(label='0.txt関連', default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text('nbz変換設定：')
								dpg.add_radio_button(
									items=(
										'変換後のファイルを拡張子nbzとwavで両方用意しておく',
										'''0.txtを".nbz"->".wav"で一括置換''',
									),
									default_value=values_default['etc_0txtnbz_radio'],
									horizontal=False,
									tag='etc_0txtnbz_radio',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('avi命令->mpegplay命令変換：')
								dpg.add_combo(
									items=(
										'利用する(関数上書き)',
										'利用する(正規表現置換)',
										'利用しない',
									),
									default_value=values_default['etc_0txtavitompegplay'],
									fit_width=True,
									tag='etc_0txtavitompegplay',
								)
							with dpg.group(horizontal=True):
								dpg.add_text('screenshot系命令無効化：')
								dpg.add_combo(
									items=(
										'利用する(関数上書き)',
										'利用する(正規表現置換)',
										'利用しない',
									),
									default_value=values_default['etc_0txtnoscreenshot'],
									fit_width=True,
									tag='etc_0txtnoscreenshot',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='maxkaisoupage最大値指定：',
									default_value=values_default['etc_0txtmaxkaisoupage_chk'],
									tag='etc_0txtmaxkaisoupage_chk',
								)
								dpg.add_combo(
									items=('1', '3', '5', '10', '20'),
									default_value=values_default['etc_0txtmaxkaisoupage_num'],
									fit_width=True,
									tag='etc_0txtmaxkaisoupage_num',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='savenumber上書き：',
									default_value=values_default['etc_0txtoverwritesavenumber_chk'],
									tag='etc_0txtoverwritesavenumber_chk',
								)
								dpg.add_combo(
									items=[str(i) for i in range(1, 21)],#1から20をstr型で保持したlist
									default_value=values_default['etc_0txtoverwritesavenumber_num'],
									fit_width=True,
									tag='etc_0txtoverwritesavenumber_num',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='setwindow/setwindow3文字潰れ防止',
									default_value=values_default['etc_0txtsetwindowbigfont_chk'],
									tag='etc_0txtsetwindowbigfont_chk',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='okcancelbox命令強制ok',
									default_value=values_default['etc_0txtskipokcancelbox_chk'],
									tag='etc_0txtskipokcancelbox_chk',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='yesnobox命令強制yes',
									default_value=values_default['etc_0txtskipyesnobox_chk'],
									tag='etc_0txtskipyesnobox_chk',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='rnd2命令->rnd命令変換',
									default_value=values_default['etc_0txtrndtornd2_chk'],
									tag='etc_0txtrndtornd2_chk',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='textgosub命令無効化',
									default_value=values_default['etc_0txtdisabletextgosub_chk'],
									tag='etc_0txtdisabletextgosub_chk',
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label='コメントアウト部分を削除',
									default_value=values_default['etc_0txtremovecommentout_chk'],
									tag='etc_0txtremovecommentout_chk',
								)
		with dpg.group(horizontal=True):
			dpg.add_progress_bar(default_value=0, tag='progress_bar', overlay='0%')
			dpg.add_button(label='Convert', user_data=(hw_key, version, charset_param),
					callback=ask_convert_start, tag='convert_button')
			dpg.add_text(default_value='', tag='progress_msg')

	dpg.set_value('input_dir', input_dir_param)
	dpg.set_value('output_dir', output_dir_param)

	dpg.set_primary_window('Main Window', True)
	dpg.setup_dearpygui()
	dpg.show_viewport()
	dpg.start_dearpygui()
	dpg.destroy_context()
