# ONScripter_Multi_Converter
## ツールについて
 ONScripter for PSP向けに~~今更~~制作された総合変換ツールです。<br>
 一応[C&D; Tools Win GUI](https://web.archive.org/web/20170419120050fw_/http://www.geocities.jp/stm_torm/ons/tool.html)の後継を目指し作りました<br>
 <br>
 元々Python完全初心者が見切り発車で始めたものなので<br>
 ソースの可読性の低さについてはご了承ください<br>

## 動作環境
 対応OS等の細かい検証は特に行っていません<br>
 多分今どきのwindowsなら普通に動くと思います<br>
 <br>
 [制作/検証に使用した作者のPC環境]<br>
 PCスペック:<br>
 [![CPU-Z](https://valid.x86.fr/cache/banner/cgwavn-2.png)](https://valid.x86.fr/cgwavn)<br>
 FFmpeg-version:2021-05-05-git-7c451b609c<br>
 Python-version:Python 3.7.7<br>

## 動作に必要なもの
 - ["ONScripter_Multi_Converter" exe本体](https://github.com/Prince-of-sea/ONScripter_Multi_Converter/releases/latest)
 - [smjpeg_encode.exe(すとーむ様作成)](http://web.archive.org/web/20130203074100/http://www.geocities.jp/stm_torm/ons/smjpeg4.zip)
 - [nsaed.exe(すとーむ様作成)](https://web.archive.org/web/20130328141650/http://www.geocities.jp/stm_torm/nsaed2.zip)
 - [GARBro.Console(게지네様作成)](https://drive.google.com/file/d/1gH9nNRxaz8GexN0B1hWyUc3o692bkWXX/view)
 - [FFmpeg](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z)
 - [NScripterで制作されたゲーム](https://erogamescape.dyndns.org/~ap2/ero/toukei_kaiseki/attlist.php?att[66]=on)(当然ですが...)

[動作確認済みタイトルはこちら](./TITLELIST.md)

## 使い方
### 変換前準備
 DLしたファイルをそれぞれの場所に展開/移動し、<br>
 最終的にファイルを以下のような配置にして準備完了です<br>
 (ディレクトリの場所は問いません)
```
[パスの通ってるディレクトリ]
   ffmpeg.exe
   ffprobe.exe


[適当な名前のツール用ディレクトリ]
│  NSC2ONS4PSP.exe
│  
└─tools
    │  nsaed.exe
    │  smjpeg_encode.exe
    │
    └─Garbro_console
        │  GARbro.Console.exe
        │  {その他大量のファイル}
        │
        └─  {その他いくつかのディレクトリ}
```

### ツールの設定
 [![インターフェース](./tools/md_ui.png)](./tools/md_ui_full.png)<br>
 ※画像は古いバージョンの場合があります<br>

#### 上段メニュー
 - **入力先**<br>
[Browse]からゲーム用ディレクトリを指定します<br>

 - **出力先**<br>
[Browse]から出力先の任意のディレクトリを指定します<br>
実際は「(選択したディレクトリ)\result」へ保存されます<br>
また、ディレクトリが競合した場合**勝手に消す**ので注意！<br>

#### 画像
 - **変換する解像度を指定**<br>
 変換後のゲームの解像度を指定します<br>
 基本的には"360x270"のままで問題ありません<br>

 - **JPG品質**<br>
 JPGに変換された画像の品質を指定します<br>
 数値が低いほど容量が少なく、高いほど画質がきれいです<br>

 - **無透過のBMPをJPGに変換&拡張子偽装**<br>
 背景が透過されていないBMPに対して、JPG変換を行います<br>

 - **透過用BMPの横解像度を偶数に指定**<br>
 [「画像の左半分にイラスト、右半分に透過処理」](http://binaryheaven.ivory.ne.jp/o_show/nscripter/syo/05.htm)<br>
 が描かれている(と思われる)画像を大雑把に抽出し、<br>
 画像の横解像度を偶数にすることによって、<br>
 "立ち絵の横に謎の縦線が表示される"不具合を回避します<br>

 - **表示が小さすぎる文字を強制拡大**<br>
 PSPで表示する際に小さすぎて読めないと思われる文字を<br>
 強制的に文字が潰れない程度のサイズまで拡大します<br>

#### 音源
 - **音源をOGGへ圧縮する**<br>
 FFmpegを使用し、ゲーム内の全ての音源データを変換します<br>
 BGMとSE(というかBGM以外)で別々に設定を行うことができます<br>
 (BGMとSEの区別は「パス名に"bgm"と入っているか」です)<br>

#### その他
 - **smjpeg_encode.exeで動画を変換する**<br>
 シナリオ内の"avi"または"mpegplay"命令で再生する動画を<br>
 "smjpeg_encode.exe"を使ってPSP向けの形式に変換します<br>

 - **nsaed.exeで出力ファイルを圧縮する**<br>
 全ての画像/音源ファイルの変換処理が終了した後に、<br>
 それらを画像、BGM、BGM以外 の3つに分けて <br>
 複数の"arc.nsa"へ分割、圧縮を行います<br>

#### 下段メニュー
 - **PSPでの画面表示**<br>
 ons.iniの"SURFACE"と"ASPECT"を書き換え、<br>
 PSP表示時に画面を拡大するかどうかを選択できます<br>

 - **convert**<br>
 ここを押すと変換開始<br>

[convert]を押してしばらく(数分～1.5時間)待ったあと、<br>
"処理が終了しました"と表示されたら変換完了です<br>
[ONScripter for PSPのEBOOT.PBP](https://archive.org/download/ons.-7z/Old%20Versions/onscripter-20110111_psp.zip)と[default.ttf](https://www.google.com/search?q=PSP+default.ttf)を準備し、<br>
[CFWまたはLCFW搭載のPSP](https://www.google.com/search?q=PSP+CFW6.61+ME%2FLME)に入れてレッツプレイ<br>

## 注意事項など
### 仕様
 - "動作に必要なもの"が全て用意されていない場合、<br>
 圧縮や変換などの一部機能が利用できなくなります<br>

 - 本ツールを使用した際に出力されるons.iniは、<br>
 [新verのONScripter向けの記述](https://web.archive.org/web/20100709172750fw_/http://blog.livedoor.jp/tormtorm/archives/51520243.html)となっています<br>

 - 対応しているゲームの解像度は4種類のみです<br>
 以下の解像度以外は変換が行えません<br>
    - 800x600
    - 640x480
    - 400x300 ~~←正直怪しい~~
    - 320x240 ~~←これも正直怪しい~~
  
 - 解像度が対応しているゲーム作品であっても、<br>
 そのソフトが正常に動作するとは限りません<br>
 (ONSの仕様上、DLLとかlua依存の作品は無理)<br>

### お約束
 - 本ツールの使用において生じた問題や不利益などについて、<br>
 製作者は一切その責任を負わないものとします<br>
 また、それらの問題を他のツールの製作者様や<br>
 メーカー/サークル様に問い合わせるのは**絶対にやめてください**<br>

### 最後に
~~...今更PSPでノベルゲームやるやついる？~~<br>