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