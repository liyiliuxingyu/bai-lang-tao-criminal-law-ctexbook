# 刑法法考数学化详册

详册沿用 2026 年 11 月 7 日研习稿，按教材二十五讲和 106 个具名节展开，共 208 页。简册以 39 页串起主要模型。查某个考点，可先由对照索引找到简册入口，再到详册复核前提、推导和反例。

- [详册 PDF](guide.pdf)
- [二十五讲与一百零六节对照索引](concordance.md)
- [简册 PDF](../criminal-law-mathematical.pdf)

## 怎样使用

1. 从[通用推导方法](guide.pdf#page=9)开始。把已知事实、尚待证明的事实、规范版本、教材采用的解释分别写下。每一步推论注明使用的前提。
2. 在各讲中先独立判断改动一个条件后还可推出什么，再核对反例和解析。[跨讲训练](guide.pdf#page=117)含五组综合案例。
3. 遮住正文，用[闭卷提取总表](guide.pdf#page=121)回忆前提、分支和例外。再翻到[逐讲扩展规则](guide.pdf#page=123)复核，附录收录 307 条编号规则。页内链接可返回对应讲次。
4. [法源与核对范围](guide.pdf#page=207)列出本版使用的规范来源。把结论用于新题时，应核对行为时间、规范版本、证据与解释前提。不同讲次的符号在相应上下文中定义。

## 源码和复编

TeX 主文件为 [src/main.tex](src/main.tex)，讲次顺序见 [src/lecture_inputs.tex](src/lecture_inputs.tex)。单讲源码在 [src/chapters](src/chapters)，闭卷表与扩展规则分别在 [src/memory_index.tex](src/memory_index.tex) 和 [src/rule_reference.tex](src/rule_reference.tex)。

安装 Python 3 和包含 XeLaTeX、CTeX、Fandol、Latin Modern、TikZ 及主文件所列宏包的 TeX Live。在本目录执行：

```sh
python3 build.py
```

输出为 `build/guide.pdf`。需要更新发布文件时使用 `python3 build.py --output guide.pdf`。每次编译运行三轮 XeLaTeX 以更新目录和交叉引用，最后用 xdvipdfmx 载入 Latin Modern 字体映射。

修改任一研习册并更新 PDF 后，在安装 PyMuPDF 的环境下执行 `python3 index_guides.py` 重建页码对照；`python3 index_guides.py --check` 将索引与两册实际书签比对。

本次从源码复编后，与存档版逐页比对了 208 页的文字、页面尺寸和 96 dpi 渲染图，三项一致。两版的 174 条目录书签及其页码也一致。法律内容沿用研习稿各处列明的核对日期。
