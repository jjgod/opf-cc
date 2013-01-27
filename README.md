opf-cc
======

OPF (Open Packaging Format) 转换工具，支持 epub 和 mobi 格式文件。目前只支持繁体到简体的转换 (欢迎提交 patch 加入其他转换模式)。

使用方法
--------

    $ git clone https://github.com/jjgod/opf-cc.git
    $ cd opf-cc
    $ opf-cc.py <book.epub | book.mobi>

将指定文件转换为简体并在同一目录下生成新的文件，如果转换后的文件名与之前一致则将旧文件改名。

依赖
----

- [OpenCC](https://github.com/BYVoid/OpenCC) (请从 git 编译安装)
- [lxml](http://lxml.de) (`sudo pip install lxml` 或 `sudo easy_install lxml`)
- [Info-zip](http://www.info-zip.org) (OS X 自带)

已知问题
--------

- 文件元数据 (书名、作者和简介等) 暂时不能转换。

致谢
----

这个项目利用了以下库:

- [OpenCC](https://github.com/BYVoid/OpenCC)
- [MobiUnpack](http://www.mobileread.com/forums/showthread.php?t=61986)

