刑法 ctexbook 重排与数学化研习工程
2026-11-20

一、从哪里开始

直接阅读：output/retypeset.pdf 是原文重排校对稿；output/mathematical.pdf 是数学化研习册。
直接编辑：tex/retypeset.tex 与 tex/mathematical.tex 是两个入口。
正文：tex/chapters/ 按原书二十五讲拆分。
人工重绘的图表：tex/figures/，每幅都是可以编辑文字、节点、连线和表格单元格的 TikZ 源码。
数学化正文：tex/math_content.tex；严格推导补篇：tex/math_derivations.tex。
最终范围、页数和检查结果：STATUS.txt、audit/final_report.json。

二、重排采用的规则

文档类为 ctexbook，采用默认中文标题与正文字号；A4，内侧18mm、外侧16mm、上18mm、下19mm。
有新封面，封面之后直接进入重新生成的目录。
原作者介绍、出版信息、前言等前置材料不进入阅读稿；原目录由新目录替代。
“使用指南”“法考是不是‘三无考试’？”各自另起一页；“知识体系”保留并用 TikZ 重绘。
原页脚“关注公众号【法考180】免费分享”从阅读稿删除。
大型图表移到下一页时，允许前页保留页底空白，避免把段落间距强制拉大。
所有已经识别的树状图、流程图、关系图和表格均有人工核对的 TikZ 替换，不嵌入扫描图。
波浪线依字符范围恢复；原扫描跨行的同一强调语段可以在新行宽下自然换行。
原脚注的圈号和文字保留，以小字号放在相应原页内容之后；没有把圈号改成另一套自动编号。
原书的观点与案例在重排稿中保留。对观点的逻辑分析与法律版本说明放在独立研习册中。
由于采用新的纸张和默认排版，新页码不与底本页码相同。追溯原页可查源码注释和覆盖审计。

三、通常的编辑和编译

需要 Python 3 与一个具备 XeTeX、LaTeX 基础、TikZ、常用扩展宏包的 TeX Live 安装。
已附中文宏包、Fandol 中文字体、Latin Modern 字体和相应许可证。
未将系统 XeTeX 可执行程序打包。首次编译在本工程 build/ 内生成格式缓存，不修改系统 TeX 配置。

在工程目录运行：

    python3 scripts/compile.py

仅编译一册：

    python3 scripts/compile.py retypeset
    python3 scripts/compile.py mathematical

默认进行三轮编译以更新目录、页码和引用。输出在 output/；日志在同目录，摘要在 audit/。
普通文字或图表修改后使用 compile.py，它不会从 OCR 重新覆盖您编辑的 TeX。
工程本次实际使用的 Python、XeTeX 和中文宏包信息见 audit/toolchain.json。

四、从已经保存的识别数据重新生成

    python3 scripts/rebuild_all.py

该命令会重新生成 tex/chapters/ 和图表引用，再编译两册。
生成依据为 data/ocr/clean/、data/ocr/underlines/ 和 data/figures/。
这是“从保存的数据复建”，不重新运行全书文字识别。
如果已经直接修改生成后的章节，请先备份修改，或者把改动同步回 clean 数据和修订记录。
图表的权威编辑本在 tex/figures/；运行复建前应把图表改动同步回 data/figures/ 中的同名文件。
全部图表已有人工替换时，复建无需 OpenCV 或 OCR 神经网络。自动图形重建脚本仅作为备用路径保留。

五、检查

    python3 scripts/verify_project.py
    python3 scripts/verify_math_models.py
    python3 scripts/verify_derivation_models.py
    python3 scripts/verify_derivations.py

verify_project.py 检查交付文件哈希、输入文件、全文页覆盖、图表替换、目录节数与 PDF 结构。
安装 PyMuPDF 后，它还检查 PDF 是否能读、是否含扫描位图、是否残留已识别的公众号页脚。
如需 PDF 检查及备用图形重建依赖，可安装 requirements-rebuild.txt。
模型检查脚本只检查声明的有限赋值、关系连接、数值边界与源码结构。
它们不证明法律前提正确，不认定事实，也不代表 Lean 等证明助手已经验证整本刑法。

SHA256SUMS.json 记录交付时文件指纹。您编辑文件后出现哈希不同属于预期；如需建立自己的一版基线，运行：

    python3 scripts/hash_files.py

六、原始材料、识别与校订留痕

source/original.pdf 是您上传的434页扫描底本，仅供核对，不是去除宣传后的阅读交付稿。
data/ocr/raw/ 保留原始识别，clean/ 保留清理和已核实局部修正后的识别。
data/ocr/verified_corrections.json 与其他 correction/audit 文件记录已核实改字及原因。
data/ocr/underlines/ 记录波浪线、对应文字范围和排除的伪线条；边界仍应随全文校对复核。
data/figures/manual_figures.json 登记每个手绘图表、原页、精确范围和替换关系。
图表修复过程释放的表外正文保留在原文中，没有把题目、选项或章节标题吞入表内。
审计里的“covered”表示每条保留的 OCR 行已有去向，不表示每个字都已经人工校对。

高级 OCR 脚本在 scripts/ocr/，要求 requirements-ocr.txt 所列依赖。
已有 OCR 数据可直接续作；正常修改不需要重新安装 OCR 引擎或重新识别434页。
重新识别可能改变行ID、文字和波浪线对齐，应在副本中进行并重新核对，不能直接覆盖现有人工修订。

七、内容边界

重排稿完整覆盖保留的原书内容，但全书约44万字没有逐字完成独立人工校对；阅读稿明确标为校对稿。
图表是逐图逐表对照重绘的；这项核查与正文逐字校对的完成范围不同。
数学化研习册覆盖二十五讲的核心模型、推导、反例与记忆方法，并补充严格语义和完整演算。
它不是原书全部罪名、所有案例和所有历史真题已经逐条形式化完毕的替代本。
数学证明只在明确的法律前提、解释方案和事实输入下成立；规范、证据与逻辑证明分别记载。
法律来源和核验范围在研习册末章及 audit/legal_sources.json。

后续逐条校订应按 STATUS.txt 的断点记录推进，不要以编译成功替代文字或法律校对。
