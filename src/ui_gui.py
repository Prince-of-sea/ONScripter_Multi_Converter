#!/usr/bin/env python3
import win32console, win32gui, i18n
import dearpygui.dearpygui as dpg

from hardwarevalues_config import gethardwarevalues_full, gethardwarevalues
from utils import value_setting_update, get_titlesettingfull, get_meipass
from misc import get_uifontpath
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
	dpg.set_value('hardware', user_data[0])
	
	for key, value in gethardwarevalues(user_data[0], 'values_default').items():
		dpg.set_value(key, value)
	return	


def gui_main(version: str, charset_param: str, hw_key: str, input_dir_param: str, output_dir_param: str, title_setting_param: str, value_setting_param: str):

	#コマンドプロンプトのウィンドウハンドルを取得
	console_window = win32console.GetConsoleWindow()

	#ウィンドウを最小化
	win32gui.ShowWindow(console_window, 6) #SW_MINIMIZE
	print(i18n.t('ui.Launch_the_application'))

	#ハードウェア値取得
	hardwarevalues_full = gethardwarevalues_full()
	values_default = gethardwarevalues(hw_key, 'values_default')
	values_default = value_setting_update(values_default, value_setting_param)

	#個別設定名登録
	title_setting_list = ['None']
	if (charset_param == 'cp932'): title_setting_list += list(get_titledict().keys())#個別設定はcp932時のみ有効
	
	dpg.create_context()

	with dpg.font_registry():
		with dpg.font(file=get_uifontpath(), size=16) as default_font:
			dpg.add_font_range_hint(dpg.mvFontRangeHint_Japanese)#日本語フォントヒント(中国語も含む?)
			dpg.bind_font(default_font)

	dpg.create_viewport(title=f'ONScripter Multi Converter for {hw_key} ver.{version}',
						width=640, height=400, small_icon=str(get_meipass('__icon.ico')), large_icon=str(get_meipass('__icon.ico')), resizable=False)

	with dpg.window(label='Main Window', tag='Main Window', no_resize=True) as window:
		with dpg.menu_bar():
			with dpg.menu(label=i18n.t('ui.label_settings')):
				dpg.add_menu_item(label=i18n.t('ui.label_cpu_usage_reduction_mode'), check=True, default_value=False, tag='lower_cpu_usage')
				with dpg.menu(label=i18n.t('ui.label_hardware_selection')):
					for hwk, hwv in hardwarevalues_full.items():
						if (charset_param in hwv['values_ex']['support_charset']):
							dpg.add_menu_item(label=hwv['values_ex']['hardware_full'], user_data=(hwk, version), callback=refresh_state)

				dpg.add_menu_item(label=i18n.t('ui.label_end'), callback=close_dpg)

			with dpg.menu(label=i18n.t('ui.label_tools')):
				dpg.add_menu_item(label=i18n.t('ui.label_numbered_video_disable'), callback=ask_create_disabledvideofile)
				dpg.add_menu_item(label=i18n.t('ui.label_decoding_nscript_dat'), user_data=(charset_param), callback=ask_decode_nscriptdat)
				dpg.add_menu_item(label=i18n.t('ui.label_open_garbro'), callback=open_garbro)

			with dpg.menu(label=i18n.t('ui.label_about')):
				dpg.add_menu_item(label=i18n.t('ui.label_open_web'), callback=open_repositorieslink)
				dpg.add_menu_item(label=i18n.t('ui.label_copyrights'), user_data=(version), callback=copyrights)
				if get_meipass('licenses_py.txt').is_file(): dpg.add_menu_item(label=i18n.t('ui.label_license'), callback=open_licensespy)
		
		with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False):
			dpg.add_table_column(no_resize=True, width_fixed=True)
			dpg.add_table_column(no_resize=True)
			dpg.add_table_column(no_resize=True, width_fixed=True)
			dpg.add_table_column(no_resize=True, width_fixed=True)

			with dpg.table_row():
				dpg.add_text(i18n.t('ui.label_input'))
				dpg.add_input_text(tag='input_dir', readonly=True, width=430)
				dpg.add_button(label='Browse', callback=open_input, tag='input_browse_btn')
				dpg.add_button(label=i18n.t('ui.label_select_from_list'), user_data=(charset_param), callback=open_select, tag='input_select_btn')

			with dpg.table_row():
				dpg.add_text(i18n.t('ui.label_output'))
				dpg.add_input_text(tag='output_dir', readonly=True, width=430)
				dpg.add_button(label='Browse', callback=open_output, tag='output_browse_btn')
				dpg.add_button(label=i18n.t('ui.label_set_to_default'), callback=desktop_output, tag='output_desktop_btn')

			with dpg.table_row():
				dpg.add_text(i18n.t('ui.label_individual_settings'))
				dpg.add_combo(
					tag='title_setting',
					default_value=(get_titlesettingfull(title_setting_param) if charset_param=='cp932' else 'None'),
					items=title_setting_list,
					width=430
				)

		with dpg.tab_bar():
			with dpg.tab(label=i18n.t('ui.label_image')):
				with dpg.child_window(height=195, border=False):
					with dpg.tree_node(label=i18n.t('ui.label_basic_settings'), default_open=True):
						with dpg.group(horizontal=True):
							dpg.add_text(i18n.t('ui.label_image_preferred_format'))
							dpg.add_radio_button(
								items=(i18n.t('var.high_resolution_priority'), i18n.t('var.low_resolution_priority')),
								default_value=values_default['preferred_resolution'],
								horizontal=True,
								tag='preferred_resolution',
							)
						with dpg.group(horizontal=True):
							dpg.add_text(i18n.t('ui.label_image_quality'))
							dpg.add_slider_int(
								label='',
								default_value=values_default['img_jpgquality_bar'],
								min_value=0,
								max_value=100,
								tag='img_jpgquality_bar',
							)
						with dpg.group(horizontal=True):
							dpg.add_checkbox(label=i18n.t('ui.label_png_reduction'), default_value=values_default['img_pngquantize_chk'], tag='img_pngquantize_chk')
							dpg.add_combo(
								label=i18n.t('ui.label_color'),
								items=('256', '192', '128'),
								default_value=values_default['img_pngquantize_num'],
								width=50,
								tag='img_pngquantize_num',
							)
					with dpg.tree_node(label=i18n.t('ui.label_advanced_settings'), default_open=True):
						dpg.add_checkbox(
							label=i18n.t('ui.label_image_transparent'),
							default_value=values_default['img_bmptojpg_chk'],
							tag='img_bmptojpg_chk',
						)
						with dpg.group(horizontal=True):
							dpg.add_checkbox(
								label=i18n.t('ui.label_png_multi'),
								default_value=values_default['img_multi_chk'],
								tag='img_multi_chk',
							)
							dpg.add_combo(
								label=i18n.t('ui.label_png_multiple_size'),
								items=(
									'1',
									'2',
									'3',
									'4',
								),
								default_value=values_default['img_multi_num'],
								width=40,
								tag='img_multi_num',
							)

			with dpg.tab(label=i18n.t('ui.label_audio')):
				with dpg.child_window(height=195, border=False):
					with dpg.tree_node(label=i18n.t('ui.label_basic_settings'), default_open=True):
						with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False):
							dpg.add_table_column(no_resize=True, width_fixed=True)
							dpg.add_table_column(no_resize=True, width_fixed=True)
							with dpg.table_row():
								dpg.add_text(i18n.t('ui.label_bgm_format'))
								dpg.add_radio_button(
									items=('OGG', 'MP3', 'WAV'),
									default_value=values_default['aud_bgmfmt_radio'],
									horizontal=True,
									tag='aud_bgmfmt_radio',
								)
							with dpg.table_row():
								dpg.add_text(i18n.t('ui.label_se_format'))
								dpg.add_radio_button(
									items=('OGG', 'MP3', 'WAV'),
									default_value=values_default['aud_sefmt_radio'],
									horizontal=True,
									tag='aud_sefmt_radio',
								)
							with dpg.table_row():
								dpg.add_text(i18n.t('ui.label_bgm_channel'))
								dpg.add_radio_button(
									items=(i18n.t('var.stereo'), i18n.t('var.mono')),
									default_value=values_default['aud_bgmch_radio'],
									horizontal=True,
									tag='aud_bgmch_radio',
								)
							with dpg.table_row():
								dpg.add_text(i18n.t('ui.label_se_channel'))
								dpg.add_radio_button(
									items=(i18n.t('var.stereo'), i18n.t('var.mono')),
									default_value=values_default['aud_sech_radio'],
									horizontal=True,
									tag='aud_sech_radio',
								)
					with dpg.tree_node(label=i18n.t('ui.label_advanced_settings'), default_open=True):
						with dpg.tree_node(label=i18n.t('ui.label_ogg_conversion'), default_open=True):
							with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False):
								dpg.add_table_column(no_resize=True, width_fixed=True)
								dpg.add_table_column(no_resize=True, width_fixed=True)
								dpg.add_table_column(no_resize=True, width_fixed=True)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_bgm_bitrate'))
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
										width=50,
										tag='aud_oggbgm_kbps',
									)
									dpg.add_combo(
										label='Hz',
										items=('44100', '22050', '11025'),
										default_value=values_default['aud_oggbgm_hz'],
										width=70,
										tag='aud_oggbgm_hz',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_se_bitrate'))
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
										width=50,
										tag='aud_oggse_kbps',
									)
									dpg.add_combo(
										label='Hz',
										items=('44100', '22050', '11025'),
										default_value=values_default['aud_oggse_hz'],
										width=70,
										tag='aud_oggse_hz',
									)
						with dpg.tree_node(label=i18n.t('ui.label_mp3_conversion'), default_open=True):
							with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False):
								dpg.add_table_column(no_resize=True, width_fixed=True)
								dpg.add_table_column(no_resize=True, width_fixed=True)
								dpg.add_table_column(no_resize=True, width_fixed=True)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_bgm_bitrate'))
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
										width=50,
										tag='aud_mp3bgm_kbps',
									)
									dpg.add_combo(
										label='Hz',
										items=('44100', '22050', '11025'),
										default_value=values_default['aud_mp3bgm_hz'],
										width=70,
										tag='aud_mp3bgm_hz',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_se_bitrate'))
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
										width=50,
										tag='aud_mp3se_kbps',
									)
									dpg.add_combo(
										label='Hz',
										items=('44100', '22050', '11025'),
										default_value=values_default['aud_mp3se_hz'],
										width=70,
										tag='aud_mp3se_hz',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_bgm_cutoff_frequency'))
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
										width=70,
										tag='aud_mp3bgm_cutoff',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_se_cutoff_frequency'))
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
										width=70,
										tag='aud_mp3se_cutoff',
									)
						with dpg.tree_node(label=i18n.t('ui.label_wav_conversion'), default_open=True):
							with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False):
								dpg.add_table_column(no_resize=True, width_fixed=True)
								dpg.add_table_column(no_resize=True, width_fixed=True)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_bgm_bitrate'))
									dpg.add_combo(
										label='Hz',
										items=('44100', '22050', '11025'),
										default_value=values_default['aud_wavbgm_hz'],
										width=70,
										tag='aud_wavbgm_hz',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_se_bitrate'))
									dpg.add_combo(
										label='Hz',
										items=('44100', '22050', '11025'),
										default_value=values_default['aud_wavse_hz'],
										width=70,
										tag='aud_wavse_hz',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_bgm_codec'))
									dpg.add_radio_button(
										items=('pcm_s16le', 'pcm_u8'),
										default_value=values_default['aud_bgmcodec_radio'],
										horizontal=True,
										tag='aud_bgmcodec_radio',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_se_codec'))
									dpg.add_radio_button(
										items=('pcm_s16le', 'pcm_u8'),
										default_value=values_default['aud_secodec_radio'],
										horizontal=True,
										tag='aud_secodec_radio',
									)

			with dpg.tab(label=i18n.t('ui.label_video')):
				with dpg.child_window(height=195, border=False):
					with dpg.tree_node(label=i18n.t('ui.label_basic_settings'), default_open=True):
						with dpg.group(horizontal=True):
							dpg.add_text(i18n.t('ui.label_video_format'))
							dpg.add_radio_button(
								items=(i18n.t('var.numbered_images'), 'MJPEG', 'MP4', i18n.t('var.do_not_convert')),
								default_value=values_default['vid_movfmt_radio'],
								horizontal=True,
								tag='vid_movfmt_radio',
							)
					with dpg.tree_node(label=i18n.t('ui.label_advanced_settings'), default_open=True):
						with dpg.tree_node(label=i18n.t('ui.label_video_numbered'), default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text(i18n.t('ui.label_video_numbered_format'))
								dpg.add_radio_button(
									items=('PNG', 'JPEG'),
									default_value=values_default['vid_renbanfmt_radio'],
									horizontal=True,
									tag='vid_renbanfmt_radio',
								)
							with dpg.group(horizontal=True):
								dpg.add_text(i18n.t('ui.label_video_numbered_resolution'))
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
								dpg.add_checkbox(label=i18n.t('ui.label_video_numbered_reduction'), default_value=values_default['vid_renbanpngquantize_chk'], tag='vid_renbanpngquantize_chk')
								dpg.add_combo(
									label=i18n.t('ui.label_color'),
									items=('256', '192', '128', '96', '64', '32'),
									default_value=values_default['vid_renbanpngquantize_num'],
									width=50,
									tag='vid_renbanpngquantize_num',
								)
							with dpg.group(horizontal=True):
								dpg.add_text(i18n.t('ui.label_video_numbered_jpeg_quality'))
								dpg.add_slider_int(
									label='',
									default_value=values_default['vid_renbanjpgquality_bar'],
									min_value=0,
									max_value=100,
									tag='vid_renbanjpgquality_bar',
								)
							with dpg.group(horizontal=True):
								dpg.add_text(i18n.t('ui.label_video_numbered_audio_setting'))
								dpg.add_radio_button(
									items=(i18n.t('var.bgm_match'), i18n.t('var.se_voice_match')),
									default_value=values_default['vid_renbanaudset_radio'],
									horizontal=False,
									tag='vid_renbanaudset_radio',
								)
						with dpg.tree_node(label=i18n.t('ui.label_video_mjpeg'), default_open=True):
							with dpg.group(horizontal=False):
								dpg.add_text(i18n.t('ui.label_video_quality'))
								dpg.add_slider_int(
									label='',
									default_value=values_default['vid_mjpegquality_bar'],
									min_value=1,
									max_value=30,
									tag='vid_mjpegquality_bar',
								)
						with dpg.tree_node(label=i18n.t('ui.label_video_mp4'), default_open=True):
							with dpg.group(horizontal=False):
								dpg.add_text(i18n.t('ui.label_video_quality'))
								dpg.add_slider_int(
									label='',
									default_value=values_default['vid_mp4quality_bar'],
									min_value=1,
									max_value=30,
									tag='vid_mp4quality_bar',
								)
							with dpg.group(horizontal=True):
								dpg.add_text(i18n.t('ui.label_video_audio_bitrate'))
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
									width=50,
									tag='vid_mp4aud_kbps',
								)
								dpg.add_combo(
									label='Hz',
									items=('44100', '22050', '11025'),
									default_value=values_default['vid_mp4aud_hz'],
									width=70,
									tag='vid_mp4aud_hz',
								)

			with dpg.tab(label=i18n.t('ui.label_other')):
				with dpg.child_window(height=195, border=False):
					with dpg.tree_node(label=i18n.t('ui.label_basic_settings'), default_open=True):
						with dpg.tree_node(label=i18n.t('ui.label_file'), default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text(i18n.t('ui.label_if_nsa_ex2gb'))
								dpg.add_radio_button(
									items=(
										i18n.t('var.create_new_nsa_after_arc3'),
										i18n.t('var.do_not_compress'),
									),
									default_value=values_default['etc_over_2gb_nsa'],
									horizontal=False,
									tag='etc_over_2gb_nsa',
								)
							with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False):
								dpg.add_table_column(no_resize=True, width_fixed=True)
								dpg.add_table_column(no_resize=True, width_fixed=True)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_image_compression'))
									dpg.add_combo(
										label='',
										items=('arc.nsa', 'arc1.nsa', 'arc2.nsa', i18n.t('var.do_not_compress')),
										default_value=values_default['etc_filecompimg_nsa'],
										width=140,
										tag='etc_filecompimg_nsa',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_bgm_compression'))
									dpg.add_combo(
										label='',
										items=('arc.nsa', 'arc1.nsa', 'arc2.nsa', i18n.t('var.do_not_compress')),
										default_value=values_default['etc_filecompbgm_nsa'],
										width=140,
										tag='etc_filecompbgm_nsa',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_se_compression'))
									dpg.add_combo(
										label='',
										items=('arc.nsa', 'arc1.nsa', 'arc2.nsa', i18n.t('var.do_not_compress')),
										default_value=values_default['etc_filecompse_nsa'],
										width=140,
										tag='etc_filecompse_nsa',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_numvideo_compression'))
									dpg.add_combo(
										label='',
										items=('arc.nsa', 'arc1.nsa', 'arc2.nsa', i18n.t('var.do_not_compress')),
										default_value=values_default['etc_filecomprenban_nsa'],
										width=140,
										tag='etc_filecomprenban_nsa',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_dll_exclude'),
										default_value=values_default['etc_fileexdll_chk'],
										tag='etc_fileexdll_chk',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_exdb_exclude'),
										default_value=values_default['etc_fileexdb_chk'],
										tag='etc_fileexdb_chk',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_getgameicon'),
										default_value=values_default['etc_getgameicon_chk'],
										tag='etc_getgameicon_chk',
									)
						with dpg.tree_node(label=i18n.t('ui.label_onsini'), default_open=True):
							with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False):
								dpg.add_table_column(no_resize=True, width_fixed=True)
								dpg.add_table_column(no_resize=True, width_fixed=True)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_onsini_expansion'))
									dpg.add_combo(
										label='',
										items=(i18n.t('var.no_expansion'), i18n.t('var.maintain_ratio'), i18n.t('var.full_size')),
										default_value=values_default['etc_iniscreen'],
										width=120,
										tag='etc_iniscreen',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_ini_font'),
										default_value=values_default['etc_iniramfont_chk'],
										tag='etc_iniramfont_chk',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_ini_cursor'),
										default_value=values_default['etc_inicursor_chk'],
										tag='etc_inicursor_chk',
									)
					with dpg.tree_node(label=i18n.t('ui.label_advanced_settings'), default_open=True):
						with dpg.tree_node(label=i18n.t('ui.label_0txt'), default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text(i18n.t('ui.label_0txt_nbzconversion'))
								dpg.add_radio_button(
									items=(
										i18n.t('var.convert_and_keep_both'),
										i18n.t('var.replace_all_nbz_to_wav'),
									),
									default_value=values_default['etc_0txtnbz_radio'],
									horizontal=False,
									tag='etc_0txtnbz_radio',
								)
							with dpg.table(header_row=False, borders_innerH=False, borders_innerV=False):
								dpg.add_table_column(no_resize=True, width_fixed=True)
								dpg.add_table_column(no_resize=True, width_fixed=True)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_0txt_avitompegplay'))
									dpg.add_combo(
										items=(
											i18n.t('var.use_function_override'),
											i18n.t('var.use_regex_replace'),
											i18n.t('var.do_not_use'),
										),
										default_value=values_default['etc_0txtavitompegplay'],
										width=180,
										tag='etc_0txtavitompegplay',
									)
								with dpg.table_row():
									dpg.add_text(i18n.t('ui.label_0txt_noscreenshot'))
									dpg.add_combo(
										items=(
											i18n.t('var.use_function_override'),
											i18n.t('var.use_regex_replace'),
											i18n.t('var.do_not_use'),
										),
										default_value=values_default['etc_0txtnoscreenshot'],
										width=180,
										tag='etc_0txtnoscreenshot',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_0txt_maxkaisoupage'),
										default_value=values_default['etc_0txtmaxkaisoupage_chk'],
										tag='etc_0txtmaxkaisoupage_chk',
									)
									dpg.add_combo(
										items=[str(i) for i in range(1, 41)],#1から40をstr型で保持したlist
										default_value=values_default['etc_0txtmaxkaisoupage_num'],
										width=50,
										tag='etc_0txtmaxkaisoupage_num',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_0txt_overwritesavenumber'),
										default_value=values_default['etc_0txtoverwritesavenumber_chk'],
										tag='etc_0txtoverwritesavenumber_chk',
									)
									dpg.add_combo(
										items=[str(i) for i in range(1, 21)],#1から20をstr型で保持したlist
										default_value=values_default['etc_0txtoverwritesavenumber_num'],
										width=50,
										tag='etc_0txtoverwritesavenumber_num',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_0txt_setwindowbigfont'),
										default_value=values_default['etc_0txtsetwindowbigfont_chk'],
										tag='etc_0txtsetwindowbigfont_chk',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_0txt_skipokcancelbox'),
										default_value=values_default['etc_0txtskipokcancelbox_chk'],
										tag='etc_0txtskipokcancelbox_chk',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_0txt_skipyesnobox'),
										default_value=values_default['etc_0txtskipyesnobox_chk'],
										tag='etc_0txtskipyesnobox_chk',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_0txt_rndtornd2'),
										default_value=values_default['etc_0txtrndtornd2_chk'],
										tag='etc_0txtrndtornd2_chk',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_0txt_disabletextgosub'),
										default_value=values_default['etc_0txtdisabletextgosub_chk'],
										tag='etc_0txtdisabletextgosub_chk',
									)
								with dpg.table_row():
									dpg.add_checkbox(
										label=i18n.t('ui.label_0txt_removecommentout'),
										default_value=values_default['etc_0txtremovecommentout_chk'],
										tag='etc_0txtremovecommentout_chk',
									)
		with dpg.group(horizontal=True):
			dpg.add_progress_bar(default_value=0, tag='progress_bar', overlay='0%')
			dpg.add_button(label='Convert', user_data=(version, charset_param),
					callback=ask_convert_start, tag='convert_button')
			dpg.add_text(default_value='', tag='progress_msg')
			#!!!ここもっと良い書き方募集中!!!
			dpg.add_text(default_value=' '*1000)#↓を画面に見せないようにするための無意味スペース
			dpg.add_text(default_value=hw_key, tag='hardware')#関数convertにhardwareを飛ばすため仕方なくこんな感じに
			
	dpg.set_value('input_dir', input_dir_param)
	dpg.set_value('output_dir', output_dir_param)

	dpg.set_primary_window('Main Window', True)
	dpg.setup_dearpygui()
	dpg.show_viewport()
	dpg.start_dearpygui()
	dpg.destroy_context()
