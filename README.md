# 柏浪涛《刑法》重排与法考数学化研习工程

## 阅读与查找考点

| 文件 | 用法 |
| --- | --- |
| [原文重排校对稿](criminal-law-retypeset.pdf) | 355 页。阅读原文、表格、波浪线、脚注和可编辑 TikZ 导图 |
| [数学化速查册](criminal-law-mathematical.pdf) | 39 页。复习主要模型、反例和闭卷检索卡 |
| [数学化详解册](study-detailed/guide.pdf) | 208 页。按原书讲节学习规则前提、推导、反例和记忆方法 |
| [25 讲、106 个具名节的对照索引](study-detailed/concordance.md) | 从教材章节找两册对应内容和 PDF 页码 |

例如，复习第二十二讲时，先定位速查册第 6.3 节，再按索引进入详解册的具体罪名。合上书，列出题目已知事实、规则前提、推理步骤和还需查证的条件。只改一个事实，重新推导结论，最后对照解析。详解册另收 307 条规则、5 个跨讲案例及闭卷记忆总表。各项规则的法源版本和适用域见册内说明。

## 修改与编译

[教材章节](tex/chapters/)、[TikZ 图表](tex/figures/)、[勘校依据](data/editorial/)、[生成与验证脚本](scripts/)及[详解册源码](study-detailed/src/)可以直接在 GitHub 上查看差异。根目录六个分卷保存 2026 年 11 月 20 日原始工程，提供扫描底本、OCR、中文宏包、字体和许可证。下载或克隆整个仓库后，在根目录使用 Python 3.10 或以上、XeTeX 和包含 TikZ 及常用 LaTeX 扩展的 TeX Live 编译。

```bash
python3 project.py compile
python3 study-detailed/build.py
```

首条命令输出 `build/output/retypeset.pdf` 和 `build/output/mathematical.pdf`，只编教材时用 `python3 project.py compile retypeset`。详册输出 `study-detailed/build/guide.pdf`。详册的 TeX 依赖和字体配置见[详细编译说明](study-detailed/README.md)。

编辑生成章节时，将相应勘校同步到生成规则或数据，以便复建后保留修改。`python3 project.py rebuild` 在独立工作目录中根据保存的 OCR、图表和勘校记录生成正文；仓库内直接编辑的章节文件不会被覆盖。

```bash
python3 project.py verify
python3 study-detailed/index_guides.py --check
```

核验需安装 PyMuPDF。首条命令校验六个分卷，重建两册，比较生成的 TeX 与仓库中的可编辑稿，检查 PDF 和编译日志，运行模型测试。第二条命令核对两册研习材料的页码索引。更新发布的研习册后，用 `python3 study-detailed/index_guides.py` 重建索引。

## 本次勘校

- 恢复 25 个章首提示框，按底本保留各框内的文字、树图和表格。修整“知识体系·总论”左侧主干的末端。
- 逐条定位 360 条原注，其中 342 条编为页脚注、16 条随表列示、2 条含整幅比较表的长注采用双向链接。另加一条编校注，说明第十四讲“犯罪所得”例 2 中 50 万元减 10 万元等于 40 万元，原书两处写作 30 万元。
- 14 处“续表”统一与下一段表头同页。修正第二讲“排除犯罪事由 I”的序号。已对照底本改正 48 处“谴责”及同批逐行核实的邻近错字，定位见 data/editorial/terms.json。

[核验记录](docs/edition-checks.json) · [接续状态](STATUS.txt) · [历史分卷清单](package-manifest.json)

约 44 万字的重排稿仍待逐字独立校订。详解册覆盖主要考点，尚待逐例核对原书的全部案例。数学模型的核验范围为给定前提下的推导和有限赋值测试。原教材及字体、宏包按各自权利说明使用。分卷恢复、历史文件指纹和依赖记录可通过 `python3 restore_project.py --verify-only` 核验，`python3 restore_project.py` 只还原 11 月 20 日存档。
