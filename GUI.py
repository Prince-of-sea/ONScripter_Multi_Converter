import PySimpleGUI as sg


def gui_msg(msg, msg_title):
	sg.theme("DarkBlue12")  # テーマ設定
	sg.popup(msg, title=msg_title)

	return


def gui_main(window_title, default_input, default_output):
	sg.theme("DarkBlue12")  # テーマ設定

	kbps_list = ["128", "112", "96", "64", "56", "48", "32"]
	Hz_list = ["44100", "22050", "11025"]

	col_1 = [
		[
			sg.Text("入力先："),
			sg.InputText(
				k="input_dir",
				size=(67, 15),
				default_text=default_input,
				readonly=True,
				enable_events=True,
			),
			sg.FolderBrowse(),
		],
		[
			sg.Text("出力先："),
			sg.InputText(
				k="output_dir",
				size=(67, 15),
				default_text=default_output,
				readonly=True,
			),
			sg.FolderBrowse(),
		],
	]

	frame_1 = sg.Frame(
		"画像",
		[
			[
				sg.Text("未指定時JPG/BMP横解像度："),
				sg.Combo(
					values=(list(range(1, 9))),
					default_value="2",
					readonly=True,
					k="img_multi",
				),
				sg.Text("の倍数"),
			],
			[
				sg.Text("JPG品質-画像："),
				sg.Slider(
					range=(100, 1),
					default_value=95,
					k="jpg_quality_1",
					pad=((0, 0), (0, 0)),
					orientation="h",
				),
			],
			[
				sg.Text("JPG品質-動画："),
				sg.Slider(
					range=(100, 1),
					default_value=92,
					k="jpg_quality_2",
					pad=((0, 0), (0, 0)),
					orientation="h",
				),
			],
			[sg.Text("解像度指定(横)：")],
			[
				sg.Radio(text="640", group_id="A", k="res_640"),
				sg.Radio(text="384", group_id="A", k="res_384"),
				sg.Radio(text="360", group_id="A", k="res_360", default=True),
				sg.Radio(text="320", group_id="A", k="res_320"),
			],
			[sg.Checkbox("BMPをJPGに変換&拡張子偽装", k="jpg_mode", default=True)],
			[
				sg.Checkbox(
					"PNGの色数を削減し圧縮：", k="PNGcolor_comp", enable_events=True, default=True
				),
				sg.Combo(
					values=([2**i for i in range(8, 3, -1)]),
					default_value="256",
					readonly=True,
					k="PNGcolor_comp_num",
				),  # [256, 128, 64, 32, 16]
				sg.Text("色"),
			],
		],
		size=(300, 250),
	)

	frame_2 = sg.Frame(
		"音源",
		[
			[
				sg.Checkbox(
					"音源をOGGへ圧縮する", k="ogg_mode", enable_events=True, default=True
				)
			],
			[
				sg.Text("BGM："),
				sg.Combo(
					values=(kbps_list), default_value="96", readonly=True, k="BGM_kbps"
				),
				sg.Text("kbps"),
				sg.Combo(
					values=(Hz_list), default_value="44100", readonly=True, k="BGM_Hz"
				),
				sg.Text("Hz"),
			],
			[
				sg.Text("SE："),
				sg.Combo(
					values=(kbps_list), default_value="48", readonly=True, k="SE_kbps"
				),
				sg.Text("kbps"),
				sg.Combo(
					values=(Hz_list), default_value="22050", readonly=True, k="SE_Hz"
				),
				sg.Text("Hz"),
			],
		],
		size=(300, 132),
		pad=(0, 0),
	)

	frame_3 = sg.Frame(
		"その他",
		[
			[sg.Checkbox("常にメモリ内にフォントを読み込んでおく", k="ram_font", default=True)],
			[sg.Checkbox("nsaed.exeで出力ファイルを圧縮する", k="nsa_mode", default=True)],
			[sg.Checkbox("表示が小さすぎる文章を強制拡大", k="sw_txtsize", default=False)],
		],
		size=(300, 118),
		pad=(0, 0),
	)

	frame_4 = sg.Frame(
		"",
		[
			[
				sg.Text(" PSPでの画面表示："),
				sg.Radio(text="拡大しない", group_id="B", k="size_normal", default=True),
				sg.Radio(text="拡大(比率維持)", group_id="B", k="size_aspect"),
				sg.Radio(text="拡大(フルサイズ)", group_id="B", k="size_full"),
			],
		],
		size=(530, 40),
	)

	frame_5 = sg.Frame(
		"", [[sg.Button("convert", pad=(9, 6), disabled=True)]], size=(70, 40)
	)

	frame_in_2and3 = sg.Column([[frame_2], [frame_3]])

	progressbar = sg.Frame(
		"",
		[[sg.ProgressBar(10000, orientation="h", size=(60, 5), key="progressbar")]],
		size=(610, 15),
	)

	layout = [[col_1], [frame_1, frame_in_2and3], [frame_4, frame_5], [progressbar]]

	window = sg.Window(
		window_title, layout, size=(640, 400), element_justification="c", margins=(0, 0)
	)  # ウインドウを表示
	return window
