import tkinter.filedialog as filedialog
import tkinter
import dearpygui.dearpygui as dpg
import subprocess as sp
import webbrowser

from requiredfile_locations import location, exist
from hardwarevalues_config import gethardwarevalues_full
from process_notons import get_titledict
from conversion import convert_start
from utils import message_box


def open_input():
	root = tkinter.Tk()
	root.withdraw()
	_path = filedialog.askdirectory()
	root.destroy()
	dpg.set_value("input_dir", _path)


def open_output():
	root = tkinter.Tk()
	root.withdraw()
	_path = filedialog.askdirectory()
	root.destroy()
	dpg.set_value("output_dir", _path)


def open_garbro():
	if exist('GARbro_GUI'): sp.Popen([location('GARbro_GUI')], shell=True)
	else: message_box('警告', 'GARbro_GUIが見つかりません', 'warning', True)
	return


def open_repositorieslink():
	url = 'https://github.com/Prince-of-sea/ONScripter_Multi_Converter'
	webbrowser.open(url, new=1, autoraise=True)
	return


def copyrights():
	message_box('copyrights', 'ONScripter Multi Converter ver.{}\n(C) 2021-2025 Prince-of-sea / PC-CNT'.format(dpg.get_value('version')), 'info', True)
	return


def close():
	dpg.stop_dearpygui()


def refresh_state(sender, app_data, user_data):
	state = user_data.copy()
	if state.get("window_title"): dpg.set_viewport_title(state.pop("window_title"))
	for key, value in state.items(): dpg.set_value(key, value)
	return	


def gui_main(version, hw_key, input_dir_param, output_dir_param):
	hardwarevalues_full = gethardwarevalues_full()
	values_default = hardwarevalues_full[hw_key]['values_default']

	#ハード変更用
	for k in hardwarevalues_full.keys():
		hardwarevalues_full[k]['values_default']['window_title'] = "ONScripter Multi Converter for {k} ver.{version}".format(k = k, version = version)
		hardwarevalues_full[k]['values_default']['hardware'] = str(k)

	#個別
	title_list = (["未指定"] + list(get_titledict().keys()))
	
	dpg.create_context()

	with dpg.font_registry():
		with dpg.font(file=r"C:\Windows\Fonts\meiryo.ttc", size=16) as default_font:
			dpg.add_font_range_hint(dpg.mvFontRangeHint_Japanese)
		dpg.bind_font(default_font)

	window_title = hardwarevalues_full[hw_key]['values_default']['window_title']
	dpg.create_viewport(title=window_title, width=640, height=400, resizable=False)

	with dpg.window(label="Main Window", tag="Main Window", no_resize=True) as window:
		with dpg.menu_bar():
			with dpg.menu(label="設定"):
				dpg.add_menu_item(label="CPU使用率低減モード", check=True, default_value=False, tag="lower_cpu_usage")
				with dpg.menu(label="ハード変更"):
					dpg.add_menu_item(label="SONY PlayStation Portable", callback=refresh_state, user_data=hardwarevalues_full['PSP']['values_default'])
					dpg.add_menu_item(label="SONY PlayStation Vita", callback=refresh_state, user_data=hardwarevalues_full['PSVITA']['values_default'])
					dpg.add_menu_item(label="SHARP Brain(Windows CE 6.0)", callback=refresh_state, user_data=hardwarevalues_full['BRAIN']['values_default'])
					dpg.add_menu_item(label="Android OS汎用", callback=refresh_state, user_data=hardwarevalues_full['ANDROID']['values_default'])

				dpg.add_menu_item(label="終了", callback=close)

			with dpg.menu(label="ツール"):
				dpg.add_menu_item(label="GARBroを起動", callback=open_garbro)

			with dpg.menu(label="このソフトについて"):
				dpg.add_menu_item(label="サイトを開く", callback=open_repositorieslink)
				dpg.add_menu_item(label="権利者表記", callback=copyrights)

		with dpg.group(horizontal=True):
			dpg.add_text("入力元：　")
			dpg.add_input_text(tag="input_dir", readonly=True)
			dpg.add_button(label="Browse", callback=open_input, tag="input_browse_btn")

		with dpg.group(horizontal=True):
			dpg.add_text("出力先：　")
			dpg.add_input_text(tag="output_dir", readonly=True)
			dpg.add_button(label="Browse", callback=open_output, tag="output_browse_btn")

		with dpg.group(horizontal=True):
			dpg.add_text("個別設定：")
			dpg.add_combo(
				tag="title_setting",
				default_value="未指定",
				items=title_list,
			)

		# with dpg.child_window(height=220, border=False):
		with dpg.tab_bar():
			with dpg.tab(label="画像"):
				with dpg.child_window(height=200, border=False):
					with dpg.tree_node(label="基本設定", default_open=True):
						with dpg.group(horizontal=True):
							dpg.add_text("変換する際の解像度が複数選択可能な場合：")
							dpg.add_radio_button(
								items=("高解像度優先", "低解像度優先"),
								default_value=values_default["preferred_resolution"],
								horizontal=True,
								tag="preferred_resolution",
							)
						with dpg.group(horizontal=True):
							dpg.add_text("JPEG品質：")
							dpg.add_slider_int(
								label="",
								default_value=values_default["img_jpgquality_bar"],
								min_value=0,
								max_value=100,
								tag="img_jpgquality_bar",
							)
						with dpg.group(horizontal=True):
							dpg.add_checkbox(label="PNGを減色：", default_value=values_default["img_pngquantize_chk"], tag="img_pngquantize_chk")
							dpg.add_combo(
								label="色",
								items=("256", "192", "128"),
								default_value=values_default["img_pngquantize_num"],
								fit_width=True,
								tag="img_pngquantize_num",
							)
					with dpg.tree_node(label="詳細設定", default_open=True):
						dpg.add_checkbox(
							label="""透過形式"l","r"以外のBMPを検出しJPEGへ変換""",
							default_value=values_default["img_bmptojpg_chk"],
							tag="img_bmptojpg_chk",
						)
						with dpg.group(horizontal=True):
							dpg.add_checkbox(
								label="""一般的な非PNGの横解像度を特定の倍数にする：""",
								default_value=values_default["img_multi_chk"],
								tag="img_multi_chk",
							)
							dpg.add_combo(
								label="の倍数",
								items=(
									"1",
									"2",
									"3",
									"4",
								),
								default_value=values_default["img_multi_num"],
								fit_width=True,
								tag="img_multi_num",
							)

			with dpg.tab(label="音楽"):
				with dpg.child_window(height=200, border=False):
					with dpg.tree_node(label="基本設定", default_open=True):
						with dpg.group(horizontal=True):
							dpg.add_text("BGMフォーマット：")
							dpg.add_radio_button(
								items=("OGG", "MP3", "WAV"),
								default_value=values_default["aud_bgmfmt_radio"],
								horizontal=True,
								tag="aud_bgmfmt_radio",
							)
						with dpg.group(horizontal=True):
							dpg.add_text("SE/VOICEフォーマット：")
							dpg.add_radio_button(
								items=("OGG", "MP3", "WAV"),
								default_value=values_default["aud_sefmt_radio"],
								horizontal=True,
								tag="aud_sefmt_radio",
							)
						with dpg.group(horizontal=True):
							dpg.add_text("SE/BGMチャンネル数：")
							dpg.add_radio_button(
								items=("ステレオ", "モノラル"),
								default_value=values_default["aud_bgmch_radio"],
								horizontal=True,
								tag="aud_bgmch_radio",
							)
						with dpg.group(horizontal=True):
							dpg.add_text("SE/VOICEチャンネル数：")
							dpg.add_radio_button(
								items=("ステレオ", "モノラル"),
								default_value=values_default["aud_sech_radio"],
								horizontal=True,
								tag="aud_sech_radio",
							)
					with dpg.tree_node(label="詳細設定", default_open=True):
						with dpg.tree_node(label="OGG変換時", default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text("BGMビットレート：")
								dpg.add_combo(
									label="kbps",
									items=(
										"192",
										"160",
										"128",
										"112",
										"96",
										"64",
										"56",
										"48",
										"32",
									),
									default_value=values_default["aud_oggbgm_kbps"],
									fit_width=True,
									tag="aud_oggbgm_kbps",
								)
								dpg.add_combo(
									label="Hz",
									items=("44100", "22050", "11025"),
									default_value=values_default["aud_oggbgm_hz"],
									fit_width=True,
									tag="aud_oggbgm_hz",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("SE/VOICEビットレート：")
								dpg.add_combo(
									label="kbps",
									items=(
										"192",
										"160",
										"128",
										"112",
										"96",
										"64",
										"56",
										"48",
										"32",
									),
									default_value=values_default["aud_oggse_kbps"],
									fit_width=True,
									tag="aud_oggse_kbps",
								)
								dpg.add_combo(
									label="Hz",
									items=("44100", "22050", "11025"),
									default_value=values_default["aud_oggse_hz"],
									fit_width=True,
									tag="aud_oggse_hz",
								)
						with dpg.tree_node(label="MP3変換時", default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text("BGMビットレート：")
								dpg.add_combo(
									label="kbps",
									items=(
										"192",
										"160",
										"128",
										"112",
										"96",
										"64",
										"56",
										"48",
										"32",
									),
									default_value=values_default["aud_mp3bgm_kbps"],
									fit_width=True,
									tag="aud_mp3bgm_kbps",
								)
								dpg.add_combo(
									label="Hz",
									items=("44100", "22050", "11025"),
									default_value=values_default["aud_mp3bgm_hz"],
									fit_width=True,
									tag="aud_mp3bgm_hz",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("SE/VOICEビットレート：")
								dpg.add_combo(
									label="kbps",
									items=(
										"192",
										"160",
										"128",
										"112",
										"96",
										"64",
										"56",
										"48",
										"32",
									),
									default_value=values_default["aud_mp3se_kbps"],
									fit_width=True,
									tag="aud_mp3se_kbps",
								)
								dpg.add_combo(
									label="Hz",
									items=("44100", "22050", "11025"),
									default_value=values_default["aud_mp3se_hz"],
									fit_width=True,
									tag="aud_mp3se_hz",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("BGMカットオフ周波数：")
								dpg.add_combo(
									label="Hz",
									items=(
										"18000",
										"16500",
										"15000",
										"13500",
										"12000",
										"10500",
										"9000",
										"7500",
									),
									default_value=values_default["aud_mp3bgm_cutoff"],
									fit_width=True,
									tag="aud_mp3bgm_cutoff",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("SE/VOICEカットオフ周波数：")
								dpg.add_combo(
									label="Hz",
									items=(
										"18000",
										"16500",
										"15000",
										"13500",
										"12000",
										"10500",
										"9000",
										"7500",
									),
									default_value=values_default["aud_mp3se_cutoff"],
									fit_width=True,
									tag="aud_mp3se_cutoff",
								)
						with dpg.tree_node(label="WAV変換時", default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text("BGMビットレート：")
								dpg.add_combo(
									label="Hz",
									items=("44100", "22050", "11025"),
									default_value=values_default["aud_wavbgm_hz"],
									fit_width=True,
									tag="aud_wavbgm_hz",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("SE/VOICEビットレート：")
								dpg.add_combo(
									label="Hz",
									items=("44100", "22050", "11025"),
									default_value=values_default["aud_wavse_hz"],
									fit_width=True,
									tag="aud_wavse_hz",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("BGMコーデック：")
								dpg.add_radio_button(
									items=("pcm_s16le", "pcm_u8"),
									default_value=values_default["aud_bgmcodec_radio"],
									horizontal=True,
									tag="aud_bgmcodec_radio",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("SEコーデック：")
								dpg.add_radio_button(
									items=("pcm_s16le", "pcm_u8"),
									default_value=values_default["aud_secodec_radio"],
									horizontal=True,
									tag="aud_secodec_radio",
								)

			with dpg.tab(label="動画"):
				with dpg.child_window(height=200, border=False):
					with dpg.tree_node(label="基本設定", default_open=True):
						with dpg.group(horizontal=True):
							dpg.add_text("動画フォーマット：")
							dpg.add_radio_button(
								items=("連番画像", "MJPEG", "MP4", "変換しない"),
								default_value=values_default["vid_movfmt_radio"],
								horizontal=True,
								tag="vid_movfmt_radio",
							)
					with dpg.tree_node(label="詳細設定", default_open=True):
						with dpg.tree_node(label="連番画像変換時", default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text("画像フォーマット：")
								dpg.add_radio_button(
									items=("PNG", "JPEG"),
									default_value=values_default["vid_renbanfmt_radio"],
									horizontal=True,
									tag="vid_renbanfmt_radio",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("解像度 - %指定：")
								dpg.add_radio_button(
									items=(
										"100%(1/1)",
										"75%(3/4)",
										"66%(2/3)",
										"50%(1/2)",
										"33%(1/3)",
										"25%(1/4)",
									),
									default_value=values_default["vid_renbanres_radio"],
									horizontal=False,
									tag="vid_renbanres_radio",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(label="連番PNGを減色：",default_value=values_default["vid_renbanpngquantize_chk"], tag="vid_renbanpngquantize_chk")
								dpg.add_combo(
									label="色",
									items=("256", "192", "128", "96", "64", "32"),
									default_value=values_default["vid_renbanpngquantize_num"],
									fit_width=True,
									tag="vid_renbanpngquantize_num",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("JPEG利用時品質：")
								dpg.add_slider_int(
									label="",
									default_value=values_default["vid_renbanjpgquality_bar"],
									min_value=0,
									max_value=100,
									tag="vid_renbanjpgquality_bar",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("音声変換時の設定：")
								dpg.add_radio_button(
									items=("BGMに合わせる", "SE/VOICEに合わせる"),
									default_value=values_default["vid_renbanaudset_radio"],
									horizontal=False,
									tag="vid_renbanaudset_radio",
								)
						with dpg.tree_node(label="MJPEG変換時", default_open=True):
							with dpg.group(horizontal=False):
								dpg.add_text("動画品質 - 数字が少ないほど高品質：")
								dpg.add_slider_int(
									label="",
									default_value=values_default["vid_mjpegquality_bar"],
									min_value=1,
									max_value=30,
									tag="vid_mjpegquality_bar",
								)
						with dpg.tree_node(label="MP4変換時", default_open=True):
							with dpg.group(horizontal=False):
								dpg.add_text("動画品質 - 数字が少ないほど高品質：")
								dpg.add_slider_int(
									label="",
									default_value=values_default["vid_mp4quality_bar"],
									min_value=1,
									max_value=30,
									tag="vid_mp4quality_bar",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("音声ビットレート：")
								dpg.add_combo(
									label="kbps",
									items=(
										"192",
										"160",
										"128",
										"112",
										"96",
										"64",
										"56",
										"48",
										"32",
									),
									default_value=values_default["vid_mp4aud_kbps"],
									fit_width=True,
									tag="vid_mp4aud_kbps",
								)
								dpg.add_combo(
									label="Hz",
									items=("44100", "22050", "11025"),
									default_value=values_default["vid_mp4aud_hz"],
									fit_width=True,
									tag="vid_mp4aud_hz",
								)

			with dpg.tab(label="その他"):
				with dpg.child_window(height=200, border=False):
					with dpg.tree_node(label="基本設定", default_open=True):
						with dpg.tree_node(label="ファイル関連", default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text("画像圧縮先：")
								dpg.add_combo(
									label="",
									items=("arc.nsa", "arc1.nsa", "arc2.nsa", "圧縮しない"),
									default_value=values_default["etc_filecompimg_nsa"],
									fit_width=True,
									tag="etc_filecompimg_nsa",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("BGM圧縮先：")
								dpg.add_combo(
									label="",
									items=("arc.nsa", "arc1.nsa", "arc2.nsa", "圧縮しない"),
									default_value=values_default["etc_filecompbgm_nsa"],
									fit_width=True,
									tag="etc_filecompbgm_nsa",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("SE/VOICE圧縮先：")
								dpg.add_combo(
									label="",
									items=("arc.nsa", "arc1.nsa", "arc2.nsa", "圧縮しない"),
									default_value=values_default["etc_filecompse_nsa"],
									fit_width=True,
									tag="etc_filecompse_nsa",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("連番利用時動画圧縮先：")
								dpg.add_combo(
									label="",
									items=("arc.nsa", "arc1.nsa", "arc2.nsa", "圧縮しない"),
									default_value=values_default["etc_filecomprenban_nsa"],
									fit_width=True,
									tag="etc_filecomprenban_nsa",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="""拡張子".dll"のファイルを全て除外""",
									default_value=values_default["etc_fileexdll_chk"],
									tag="etc_fileexdll_chk",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="""ファイル"Thumbs.db"を全て除外""",
									default_value=values_default["etc_fileexdb_chk"],
									tag="etc_fileexdb_chk",
								)
						with dpg.tree_node(label="ons.ini関連(PSP用)", default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text("画面表示：")
								dpg.add_combo(
									label="",
									items=("拡大しない", "拡大(比率維持)", "拡大(フルサイズ)"),
									default_value=values_default["etc_iniscreen"],
									fit_width=True,
									tag="etc_iniscreen",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="常にメモリ内にフォントを読み込んでおく",
									default_value=values_default["etc_iniramfont_chk"],
									tag="etc_iniramfont_chk",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="マウスカーソルを利用",
									default_value=values_default["etc_inicursor_chk"],
									tag="etc_inicursor_chk",
								)
					with dpg.tree_node(label="詳細設定", default_open=True):
						with dpg.tree_node(label="0.txt関連", default_open=True):
							with dpg.group(horizontal=True):
								dpg.add_text("nbz変換設定：")
								dpg.add_radio_button(
									items=(
										"変換後のファイルを拡張子nbzとwavで両方用意しておく",
										"""0.txtを".nbz"->".wav"で一括置換""",
									),
									default_value=values_default["etc_0txtnbz_radio"],
									horizontal=False,
									tag="etc_0txtnbz_radio",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("avi命令->mpegplay命令変換：")
								dpg.add_combo(
									items=(
										"利用する(関数上書き)",
										"利用する(正規表現置換)",
										"利用しない",
									),
									default_value=values_default["etc_0txtavitompegplay"],
									fit_width=True,
									tag="etc_0txtavitompegplay",
								)
							with dpg.group(horizontal=True):
								dpg.add_text("screenshot系命令無効化：")
								dpg.add_combo(
									items=(
										"利用する(関数上書き)",
										"利用する(正規表現置換)",
										"利用しない",
									),
									default_value=values_default["etc_0txtnoscreenshot"],
									fit_width=True,
									tag="etc_0txtnoscreenshot",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="低容量RAM搭載端末用maxkaisoupage最大値指定：",
									default_value=values_default["etc_0txtmaxkaisoupage_chk"],
									tag="etc_0txtmaxkaisoupage_chk",
								)
								dpg.add_combo(
									items=("1", "3", "5", "10", "20"),
									default_value=values_default["etc_0txtmaxkaisoupage_num"],
									fit_width=True,
									tag="etc_0txtmaxkaisoupage_num",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="低解像度端末用setwindow/setwindow3文字潰れ防止",
									default_value=values_default["etc_0txtsetwindowbigfont_chk"],
									tag="etc_0txtsetwindowbigfont_chk",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="okcancelbox命令強制ok",
									default_value=values_default["etc_0txtskipokcancelbox_chk"],
									tag="etc_0txtskipokcancelbox_chk",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="yesnobox命令強制yes",
									default_value=values_default["etc_0txtskipyesnobox_chk"],
									tag="etc_0txtskipyesnobox_chk",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="rnd2命令->rnd命令変換",
									default_value=values_default["etc_0txtrndtornd2_chk"],
									tag="etc_0txtrndtornd2_chk",
								)
							with dpg.group(horizontal=True):
								dpg.add_checkbox(
									label="コメントアウト部分を削除",
									default_value=values_default["etc_0txtremovecommentout_chk"],
									tag="etc_0txtremovecommentout_chk",
								)
		with dpg.group(horizontal=True):
			dpg.add_progress_bar(default_value=0, tag="progress_bar", overlay="0%")
			dpg.add_button(label="Convert", callback=convert_start, tag="convert_button")
			dpg.add_text(default_value="", tag="progress_msg")

			#!!!ここもっと良い書き方募集中!!!
			dpg.add_text(default_value=" "*1000)#↓を画面に見せないようにするための無意味スペース
			dpg.add_text(default_value=values_default["hardware"], tag="hardware")#関数convertにhardwareを飛ばすため仕方なくこんな感じに
			dpg.add_text(default_value=version, tag="version")#同様

	dpg.set_value("input_dir", input_dir_param)
	dpg.set_value("output_dir", output_dir_param)

	dpg.set_primary_window("Main Window", True)
	dpg.setup_dearpygui()
	dpg.show_viewport()
	dpg.start_dearpygui()
	dpg.destroy_context()