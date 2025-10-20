# ONScripter_Multi_Converter
## 关于此工具
 用于制作一些特定设备的ONScripter游戏的~~现在才~~制作的综合转换工具。<br>
 目前，目标是成为[C&D; Tools Win GUI](https://web.archive.org/web/20170419120050fw_/http://www.geocities.jp/stm_torm/ons/tool.html)的继承作<br>


## 准备环境
 目前没有进行非常多的系统兼容性验证<br>
 我认为Windows10及以后的版本不会有多少兼容性问题<br>
 <br>
 [作者制作和验证的PC设备环境]<br>
 规格: <br>
 [![CPU-Z](https://valid.x86.fr/cache/banner/eidarj-2.png)](https://valid.x86.fr/eidarj)<br>
 FFmpeg-version: version 7.1-full_build<br>


## 准备工具
### 必要工具
 - "ONScripter_Multi_Converter" exe本体 [[DL (Assets)]](https://github.com/Prince-of-sea/ONScripter_Multi_Converter/releases/latest)
 - GARbro.Console [[DL (Google drive)]](https://drive.usercontent.google.com/u/0/uc?id=1gH9nNRxaz8GexN0B1hWyUc3o692bkWXX&export=download)
 - FFmpeg / FFprobe [[DL (gyan.dev)]](https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z)
 - smjpeg_encode [[DL (archive.org)]](http://web.archive.org/web/20130203074100/http://www.geocities.jp/stm_torm/ons/smjpeg4.zip)
 - nsaed [[DL (archive.org)]](https://web.archive.org/web/20130328141650/http://www.geocities.jp/stm_torm/nsaed2.zip)
 - 准备转换的NSCripter或ONScripter游戏作品的文件<br>

### 可选
 - gscScriptCompAndDecompiler-cli [[DL (Assets)]](https://github.com/PC-CNT/gscScriptCompAndDecompiler-cli/releases/tag/pr12)
 - DirectorCastRipper_D10 [[DL (Assets)]](https://github.com/n0samu/DirectorCastRipper/releases/tag/v2.5)
 - mjdisasm [[DL (View raw)]](https://github.com/Inori/FuckGalEngine/blob/master/Majiro/mjdev/mjdisasm.exe)
 - igscriptD [[DL (Assets的igtools.zip里)]](https://github.com/lennylxx/IG_tools/releases/tag/v1.0.0)
 - Kikiriki [[DL (archive.org)]](https://web.archive.org/web/20140714111942/http://tlwiki.org/images/7/7d/Kikiriki.rar)

※"可选"再转换特定的非ONScripter作品时才需要使用<br>
一般来说常规作品转换时是不需要的<br>


## 使用方法
### 转换前准备
 将下载的文件部署/移动到每个位置，<br>
 最后按如下方式排列文件<br>
，即可完成
 (总目录的位置无关紧要)

#### 基本所需文件排列示例
```
[工具目录同级目录（其实可以和ONScripter_Multi_Converter.exe在同一目录）]
   ffmpeg.exe
   ffprobe.exe


[工具目录（自己命名）]
│  ONScripter_Multi_Converter.exe
│  
└─tools
    │  nsaed.exe
    │  smjpeg_encode.exe
    │                  
    └─Garbro_console
       │  GARbro.Console.exe
       │  {其他的大量文件都要包含}
       │  
       └─{其他的大量文件都要包含}
```

#### 使用所有工具的文件排列示例
```
[工具目录同级目录（其实可以和ONScripter_Multi_Converter.exe在同一目录）]
   ffmpeg.exe
   ffprobe.exe


[工具目录（自己命名）]
│  ONScripter_Multi_Converter.exe
│  
└─tools
    │  gscScriptCompAndDecompiler.exe
    │  igscriptD.exe
    │  mjdisasm.exe
    │  nsaed.exe
    │  smjpeg_encode.exe
    │  
    ├─DirectorCastRipper_D10
    │  │  DirectorCastRipper.exe
    │  │  {其他的大量文件都要包含}
    │  │  
    │  └─{其他的大量文件都要包含}
    │                  
    ├─Garbro_console
    │  │  GARbro.Console.exe
    │  │  {其他的大量文件都要包含}
    │  │  
    │  └─{其他的大量文件都要包含}
    │          
    └─Kikiriki
            kikiriki.exe
            madCHook.dll
```

 ※ffmpeg、ffprobe可以在tools目录下(nsaed和smjpeg_encodeと的同级目录)被识别<br>
 此外，工具目录同级目录与tools目录下都存在的话tools目录下的回优先被使用<br>


### 使用设置(GUI)
 [详细内容在这里有写](./README_setting.md)<br>
~~如果你不确定，我认为你可以直接更换成合适的硬件，只指定input/output，然后按Convert~~
启动GBK支持，需要在命令行启动应用，命令为
```
   ONScripter_Multi_Converter.exe -lang en -chrs gbk
```

### 使用设置(CLI)
 [详细内容在这里有写](./README_setting2.md)<br>
 可能会出现未知错误，所以如果您不确定，请不要使用它


## 注意事项
### 规范
 - 此工具旨在与以下版本的 ONScripter 配合使用
    - PSP: onscripter-20110111_psp ※实测转换中文时封魔夜君的2009040X版本可以运行，图片正常显示，其他均有部分异常
    - PSVITA: ONScripter-jh-PSVita (yuri) v0.5.1.3 ※日本語で確認
    - Brain: onscripter-20100510-424x318 / onscripter-20100510-qvga
    - Android: ONScripter v20240906

 - 在不支持自由分辨率规范的硬件(PSP/Brain)，仅支持 4 种类型的游戏分辨率<br>
   除了以下分辨率外，无法执行转换<br>
 ※目前，v2.0.0 之后（仅适用于 PSP ）如果水平分辨率为 640 或 800 的 +-10（例：793x446）可以强制转换为<br>
    - 800x600
    - 640x480
    - 400x300 ~~←真的很可疑~~
    - 320x240 ~~←这个也很可疑~~

 - 即使是支持的分辨率<br>
   软件也可能无法正常工作<br>
 (由于是ONS，无法进行依赖于 DLL 或 lua 的工作)<br>

 - 由于使用了 PyInstaller 和~~不必要的~~一些复杂的内部处理<br>
 似乎是会被报毒<br>
建议在转换前将此工具设置为白名单<br>

 - 请在 C 盘上有足够的可用空间的情况下使用它<br>
 特别的，由于转换方法的不同，某些作品转换时可能会暂时消耗高达15GB的空间<br>

### 关于使用 CD-DA 的软件
为了在ONScripter使用[CD audio 的音频替换功能](https://web.archive.org/web/20231102082402if_/https://onscripter.osdn.jp/onscripter.html#cd-audio-mapping)<br>
请事先将提取出的音源文件（wav格式）准备好作为输入文件<br>
本工具将自动完成转换为ogg等格式，无需提前进行转换<br>

### 已知问题
 - 若原本使用defsub覆盖了avi、mpegplay、rnd2等部分函数，则会与本工具的功能发生冲突。
 - 位于nsa/sar/ns2之外的nbz文件无法处理
 - 个别设置栏中的若干字符显示为“?”(但是可以用)
 - 部分包含日语的sar文件无法以正常名称解压(也许是GARbro的问题?)

### 规定
 - 关于使用本工具时产生的问题或不利影响，<br>
 制作者概不承担任何责任。<br>
 请不要就此类问题联系其他工具的制作者/社团方。<br>
