# 刑法 ctexbook 重排与数学化研习工程

以 434 页扫描底本为基础，保存可编辑的中文 LaTeX 重排稿、TikZ 图表、数学化研习册，以及继续校订所需的识别数据、脚本、字体和审计记录。

## 直接阅读

| 文件 | 内容 |
| --- | --- |
| [criminal-law-retypeset.pdf](criminal-law-retypeset.pdf) | 365 页全文重排校对稿 |
| [criminal-law-mathematical.pdf](criminal-law-mathematical.pdf) | 39 页数学化研习册 |
| [STATUS.txt](STATUS.txt) | 完成范围、未完成事项与续作断点 |

## 完整工程：六个分卷全部保留

完整工程 ZIP 按原字节顺序拆分为 `criminal-law-project.zip.part01` 至 `criminal-law-project.zip.part06`。**六片合起来才是完整工程**；这些是普通二进制分片，不能分别作为 ZIP 解压。

前五片各 24,000,000 字节，第六片 18,375,242 字节。分卷没有删减工程内容，恢复后共 **4,164 个文件**，包括原扫描底本、两份 PDF、全部 LaTeX/TikZ 源码、OCR 与波浪线数据、字体、依赖及审计记录。

### 下载并恢复

在 GitHub 使用 **Code → Download ZIP**，解压后进入仓库目录；也可以克隆：

```bash
git clone https://github.com/liyiliuxingyu/criminal-law-ctexbook.git
cd criminal-law-ctexbook
```

确保六片、`package-manifest.json` 和 `restore_project.py` 位于同一目录，然后运行：

```bash
python3 restore_project.py
```

恢复脚本只依赖 Python 3 标准库。它流式合并分卷，逐片和整包核验 SHA-256，检查 ZIP 路径及文件类型，再安全解压；随后按原 `SHA256SUMS.json` 核验 4,163 个文件，并检查连同清单本身共 4,164 个文件、没有多余文件。脚本不联网、不下载代码，也不执行解压出的代码。

默认恢复到脚本旁的 `criminal_law_ctexbook/`。**目标已存在时拒绝覆盖，保留原内容。** 需要另一份副本时指定一个尚不存在的目录：

```bash
python3 restore_project.py --destination ../criminal_law_ctexbook_copy
```

只核验六片、完整 ZIP 与全部归档文件，不恢复目录：

```bash
python3 restore_project.py --verify-only
```

### 编译

需要 Python 3 和具备 XeTeX、LaTeX 基础、TikZ、常用扩展宏包的 TeX Live。工程附中文宏包、Fandol 与 Latin Modern 字体，没有打包系统 XeTeX 可执行程序。

```bash
cd criminal_law_ctexbook
python3 scripts/compile.py
```

默认三轮编译以更新目录、页码和引用，输出在 `output/`。也可只编译一册：

```bash
python3 scripts/compile.py retypeset
python3 scripts/compile.py mathematical
```

**普通文字或图表修改后使用 `compile.py`**：它直接编译当前 TeX，不会从 OCR 覆盖编辑结果。

**从保留数据重新生成使用 `rebuild_all.py`**：

```bash
python3 scripts/rebuild_all.py
```

后者会覆盖生成章节和图表引用，再编译两册；不会重新识别 434 页扫描。运行前应保存直接编辑的 TeX，并将需保留的修改同步回数据和修订记录。图表修改应同步维护 `tex/figures/` 与 `data/figures/` 的对应文件。

## 内容与真实完成边界

- `ctexbook` 默认中文标题与正文字号；A4，内侧 18 mm、外侧 16 mm、上 18 mm、下 19 mm。
- 新封面之后直接进入新目录；“使用指南”“法考是不是‘三无考试’？”分别另起一页。原作者介绍、出版前置材料、前言及公众号页脚不进入阅读稿。
- 197 处图表已重绘为可编辑 TikZ：77 幅非表格图和 120 张表格。两份阅读 PDF 均不嵌入扫描图。
- 检出的 713 段保留内容强调线已有文字范围映射；这不等于扫描中所有波浪线都已穷尽发现。
- 数学化册共 10 章，对应原书 25 讲，含 31 张检索卡、39 个教学设例、17 个模型命题，区分规范前提、解释假设、事实输入与逻辑结论。

**重排稿仍是校对稿。** 约 44 万字尚未逐字完成独立人工校对。数学化册覆盖核心模型、推导、反例和记忆方法，尚未逐条形式化原书全部案例、全部罪名细节或所有地方标准。有限模型检查不代表法律前提已获证明，也不代表 Lean 等证明助手已认证整本书。

详细记录见恢复后的 `README.txt`、`STATUS.txt`、`audit/final_report.json` 与 `audit/legal_sources.json`。正文逐字校对的续作起点为原扫描 PDF 第 13 页。

## 恢复后的主要路径

| 路径 | 用途 |
| --- | --- |
| `tex/retypeset.tex`、`tex/mathematical.tex` | 两册编译入口 |
| `tex/chapters/` | 原书 25 讲正文与参考文献 |
| `tex/figures/` | 全部 197 处 TikZ 图表 |
| `tex/math_content.tex`、`tex/math_derivations.tex` | 数学化正文与严格推导补篇 |
| `data/ocr/`、`data/figures/` | 识别、波浪线、人工修订及图表重建数据 |
| `source/original.pdf` | 434 页扫描底本，供核对 |
| `texmf/`、`licenses/` | 随附字体、宏包及原有许可证 |
| `audit/`、`SHA256SUMS.json` | 审计记录、工具链和文件指纹 |

原始教材及其内容的权利属于相应权利人。本仓库没有为原书另行授予开放许可；随附字体、宏包等仍按各自原有许可证使用，详见完整工程的 `licenses/` 等许可文件。

## 校验依据

原完整包名称：`刑法_ctexbook完整续作工程_20261120.zip`。

原完整包大小：**138,375,242 字节**；SHA-256：

```text
c1258632bc3fc340b5bc0af063a00e97704f3932c232a91d2536f26abf658401
```

每片的名称、字节数和 SHA-256 见 [package-manifest.json](package-manifest.json)。恢复后的完整工程还提供以下检查命令：

```bash
python3 scripts/verify_project.py
python3 scripts/verify_math_models.py
python3 scripts/verify_derivation_models.py
python3 scripts/verify_derivations.py
```

普通续作无需重新安装 OCR 引擎。可选 PDF 检查及备用图形重建依赖见工程内 `requirements-rebuild.txt`；实际工具链见 `audit/toolchain.json`。编辑工程后原指纹不匹配属于预期，建立新基线可运行 `python3 scripts/hash_files.py`。
