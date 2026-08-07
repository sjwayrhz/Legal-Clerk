# 执行材料PDF批量拆分工具

>1_split_pdf.py

仅限Windows系统，自动扫描根目录及一级子文件夹内指定合并卷宗PDF，按预设页码批量拆分出申请书、身份证明等7类独立文书。处理完成后，自动生成备用素材目录快捷方式，单文件报错不影响批量运行，简化法院执行卷宗整理工作。

# 批量替换PDF中的字符

>2_replace_pdf_text.py

全平台通用，可递归扫描所有层级子文件夹的PDF，支持批量替换姓名、身份证、手机号等文本。自带智能字体适配功能，无痕覆盖修改内容，保留原文件排版样式，自动清理缓存，仅支持可复制文本PDF，修改后直接覆盖原文件。

# 提取申请书PDF中个人信息

>3_extract_pdf_info.py

全平台可用，扫描一级案件文件夹内的强制执行申请书PDF，精准隔离被执行人信息区块，提取姓名、证件号、住址等信息，修复文本错乱换行。自动生成排版规整的TXT摘要文件，单文件异常不会中断整体批量提取任务。

# 法院文书批量下载重命名工具

>8_court_download.py

全平台通用，批量解析法院执行平台链接参数，调用官方接口批量下载案件PDF文书。可内存读取PDF提取被执行人姓名，自动清理冗余文件名，同名文件自动递增序号，一键规整保存，全程自动化处理，大幅提升法院文书归集效率，单链接报错不中断批量任务。

# 油猴-解除网站禁止密码自动填充

适配浏览器油猴插件，安装导入后可破解各类网站禁止密码自动填充的限制，解除网页原生登录框的填充拦截规则，实现账号密码自动登录，适配多数限制自动填充的网页系统，使用便捷无复杂配置。

```
// ==UserScript==
// @name         解除网站禁止密码自动填充
// @namespace    autofix
// @version      1.0
// @match        *://zxfw.court.gov.cn/*
// @match        *://sdp.hnzycfc.com/*
// @grant        none
// @run-at       document-start
// ==/UserScript==

// 1.移除全部表单autocomplete关闭限制
function fixAutoComplete() {
    document.querySelectorAll("input,form").forEach(el => {
        el.setAttribute("autocomplete", "on");
    })
}
// 2.每秒扫描一次动态表单（适配vue/react动态渲染登录框）
setInterval(fixAutoComplete, 800);

// 3.屏蔽网页禁止粘贴的JS拦截
document.addEventListener('copy', e => e.stopImmediatePropagation())
document.addEventListener('paste', e => e.stopImmediatePropagation())
```