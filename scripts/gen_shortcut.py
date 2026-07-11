#!/usr/bin/env python3
"""ACL4 加规则 v2 — full explicit wiring (every consumer references producer UUID).

Every serialization shape verified against real shortcuts harvested from iCloud
(ShortcutsBench link corpus) or probe runs on this Mac:
- setvariable/getvalueforkey/base64encode: WFInput = bare token attachment  (Q3/Q4 + samples)
- text.match: input param "text" as WFTextTokenString                       (sample)
- text.match.getgroup: input param "matches" as bare attachment             (sample)
- conditional: WFInput = {Type:Variable, Variable: <attachment>}, numeric
  WFCondition (4 is / 99 contains / 100 has any value / 101 has no value)   (samples)
- choosefrommenu: WFMenuItems plain string array                            (samples)
- WFHTTPHeaders / WFJSONValues: WFDictionaryFieldValue items with
  WFItemType 0 + WFTextTokenString key/value                                (sample)
"""
import plistlib
import sys
import uuid


def U():
    return str(uuid.uuid4()).upper()


def var(name):
    return {"Type": "Variable", "VariableName": name}


def ao(u, name):
    return {"Type": "ActionOutput", "OutputUUID": u, "OutputName": name}


EXT = {"Type": "ExtensionInput"}


def ts(*parts):
    s, att = "", {}
    for p in parts:
        if isinstance(p, str):
            s += p
        else:
            att["{%d, 1}" % len(s)] = p
            s += "￼"
    v = {"string": s}
    if att:
        v["attachmentsByRange"] = att
    return {"Value": v, "WFSerializationType": "WFTextTokenString"}


def ta(att):
    return {"Value": att, "WFSerializationType": "WFTextTokenAttachment"}


def A(ident, params=None):
    return {"WFWorkflowActionIdentifier": "is.workflow.actions." + ident,
            "WFWorkflowActionParameters": params or {}}


def text(content, u=None):
    p = {"WFTextActionText": content}
    if u:
        p["UUID"] = u
    return A("gettext", p)


def setvar(name, src_att):
    return A("setvariable", {"WFVariableName": name, "WFInput": ta(src_att)})


def notify(*parts):
    return A("notification", {"WFNotificationActionBody": ts(*parts), "WFNotificationActionSound": True})


def alert(title, *parts):
    return A("alert", {"WFAlertActionTitle": title, "WFAlertActionMessage": ts(*parts),
                       "WFAlertActionCancelButtonShown": False})


def if_start(g, att, cond, comp=None):
    p = {"GroupingIdentifier": g, "WFControlFlowMode": 0,
         "WFInput": {"Type": "Variable", "Variable": ta(att)},
         "WFCondition": cond}
    if comp is not None:
        p["WFConditionalActionString"] = comp
    return A("conditional", p)


def if_else(g):
    return A("conditional", {"GroupingIdentifier": g, "WFControlFlowMode": 1})


def if_end(g):
    return A("conditional", {"GroupingIdentifier": g, "WFControlFlowMode": 2})


def menu_start(g, prompt, items):
    return A("choosefrommenu", {"GroupingIdentifier": g, "WFControlFlowMode": 0,
                                "WFMenuPrompt": prompt, "WFMenuItems": items})


def menu_case(g, title):
    return A("choosefrommenu", {"GroupingIdentifier": g, "WFControlFlowMode": 1, "WFMenuItemTitle": title})


def menu_end(g):
    return A("choosefrommenu", {"GroupingIdentifier": g, "WFControlFlowMode": 2})


def dictfield(pairs):
    return {"Value": {"WFDictionaryFieldValueItems": [
        {"WFItemType": 0, "WFKey": k, "WFValue": v} for k, v in pairs
    ]}, "WFSerializationType": "WFDictionaryFieldValue"}


def headers():
    return dictfield([
        (ts("Authorization"), ts("Bearer ", var("Token"))),
        (ts("Accept"), ts("application/vnd.github+json")),
    ])


HAS_NO_VALUE, CONTAINS = 101, 99
HOST_RE = r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*://)?(?:[^/@\s]+@)?([^/:?#\s]+)"

acts = []

acts.append(A("comment", {"WFCommentActionText":
    "ACL4 加规则 · 使用前必读\n"
    "1) 把下面『Token』文本动作（github_pat_ 开头的占位文本）替换为你的 GitHub Fine-grained PAT（仅 fly48432/ACL4 仓库、Contents 读写）。\n"
    "2) 可从分享表单调用（网页/文本），也可直接运行后手动输入域名。\n"
    "3) 详细原理与验证清单见仓库 docs/shortcut-add-rule.md"}))

# ── 1. 输入获取 ──
g = U()
uAsk, uCoerce = U(), U()
acts += [
    if_start(g, EXT, HAS_NO_VALUE),
    A("ask", {"WFAskActionPrompt": "输入域名 / 关键词或粘贴网址", "WFInputType": "Text", "UUID": uAsk}),
    setvar("原始输入", ao(uAsk, "Provided Input")),
    if_else(g),
    text(ts(EXT), uCoerce),
    setvar("原始输入", ao(uCoerce, "Text")),
    if_end(g),
]

# ── 2. 提取域名 + 空值守卫 ──
uMatch, uGrp = U(), U()
acts += [
    A("text.match", {"WFMatchTextPattern": HOST_RE, "WFMatchTextCaseSensitive": False,
                     "text": ts(var("原始输入")), "UUID": uMatch}),
    A("text.match.getgroup", {"matches": ta(ao(uMatch, "Matches")),
                              "WFGetGroupType": "Group At Index", "WFGroupIndex": 1, "UUID": uGrp}),
    setvar("域名", ao(uGrp, "Match Group")),
]
g = U()
acts += [
    if_start(g, ao(uGrp, "Match Group"), HAS_NO_VALUE),
    notify("输入无效，未提取到域名"),
    A("exit"),
    if_end(g),
]

# ── 3. 规则类型菜单 ──
g = U()
acts.append(menu_start(g, "规则类型", ["DOMAIN-SUFFIX", "DOMAIN", "DOMAIN-KEYWORD"]))

acts.append(menu_case(g, "DOMAIN-SUFFIX"))
uM2, uM3, uList, uPick, uT = U(), U(), U(), U(), U()
acts += [
    A("text.match", {"WFMatchTextPattern": r"[^.]+\.[^.]+$", "WFMatchTextCaseSensitive": False,
                     "text": ts(var("域名")), "UUID": uM2}),
    setvar("候选2", ao(uM2, "Matches")),
    A("text.match", {"WFMatchTextPattern": r"[^.]+\.[^.]+\.[^.]+$", "WFMatchTextCaseSensitive": False,
                     "text": ts(var("域名")), "UUID": uM3}),
    setvar("候选3", ao(uM3, "Matches")),
    A("list", {"WFItems": [
        {"WFItemType": 0, "WFValue": ts(var("候选2"))},
        {"WFItemType": 0, "WFValue": ts(var("候选3"))},
        {"WFItemType": 0, "WFValue": ts(var("域名"))},
    ], "UUID": uList}),
    A("choosefromlist", {"WFInput": ta(ao(uList, "List")),
                         "WFChooseFromListActionPrompt": "选择规则值", "UUID": uPick}),
    setvar("规则值", ao(uPick, "Chosen Item")),
    text("DOMAIN-SUFFIX", uT),
    setvar("规则类型", ao(uT, "Text")),
]

acts.append(menu_case(g, "DOMAIN"))
uT1, uT2 = U(), U()
acts += [
    text(ts(var("域名")), uT1),
    setvar("规则值", ao(uT1, "Text")),
    text("DOMAIN", uT2),
    setvar("规则类型", ao(uT2, "Text")),
]

acts.append(menu_case(g, "DOMAIN-KEYWORD"))
uAsk2, uT3 = U(), U()
acts += [
    A("ask", {"WFAskActionPrompt": "输入关键词", "WFInputType": "Text",
              "WFAskActionDefaultAnswer": ts(var("域名")), "UUID": uAsk2}),
    setvar("规则值", ao(uAsk2, "Provided Input")),
    text("DOMAIN-KEYWORD", uT3),
    setvar("规则类型", ao(uT3, "Text")),
]
acts.append(menu_end(g))

# ── 4. 分类菜单 ──
g = U()
acts.append(menu_start(g, "分流到", ["直连", "代理"]))
acts.append(menu_case(g, "直连"))
u = U()
acts += [text("Direct.list", u), setvar("目标文件", ao(u, "Text"))]
acts.append(menu_case(g, "代理"))
g2 = U()
acts.append(menu_start(g2, "代理策略", ["默认代理", "美国", "日本", "香港", "新加坡", "AI"]))
for label, fname in [("默认代理", "Proxy.list"), ("美国", "US.list"), ("日本", "JP.list"),
                     ("香港", "HK.list"), ("新加坡", "SG.list"), ("AI", "AISuite.list")]:
    acts.append(menu_case(g2, label))
    u = U()
    acts += [text(fname, u), setvar("目标文件", ao(u, "Text"))]
acts.append(menu_end(g2))
acts.append(menu_end(g))

# ── 5. 规则行 / Token / API 地址 ──
uRule, uTok, uAPI = U(), U(), U()
acts += [
    text(ts(var("规则类型"), ",", var("规则值")), uRule),
    setvar("规则行", ao(uRule, "Text")),
    text("github_pat_请替换为你的Token", uTok),
    setvar("Token", ao(uTok, "Text")),
    text(ts("https://api.github.com/repos/fly48432/ACL4/contents/Rules/Loon/", var("目标文件")), uAPI),
    setvar("API地址", ao(uAPI, "Text")),
]

# ── 6. GET 现有文件 ──
uGET, uSHA, uCont, uOld = U(), U(), U(), U()
acts += [
    A("downloadurl", {"WFURL": ts(var("API地址")), "WFHTTPMethod": "GET",
                      "WFHTTPHeaders": headers(), "ShowHeaders": True, "Advanced": True, "UUID": uGET}),
    A("getvalueforkey", {"WFDictionaryKey": "sha",
                         "WFInput": ta(ao(uGET, "Contents of URL")), "UUID": uSHA}),
    setvar("文件SHA", ao(uSHA, "Dictionary Value")),
    A("getvalueforkey", {"WFDictionaryKey": "content",
                         "WFInput": ta(ao(uGET, "Contents of URL")), "UUID": uCont}),
    A("base64encode", {"WFEncodeMode": "Decode",
                       "WFInput": ta(ao(uCont, "Dictionary Value")), "UUID": uOld}),
    setvar("旧内容", ao(uOld, "Base64 Encoded")),
]

# ── 7. 守卫：解码失败（防整文件覆写）/ 查重 ──
g = U()
acts += [
    if_start(g, ao(uOld, "Base64 Encoded"), HAS_NO_VALUE),
    alert("读取文件失败", "读取文件失败，已中止（避免覆写整个文件）"),
    A("exit"),
    if_end(g),
]
g = U()
acts += [
    if_start(g, ao(uOld, "Base64 Encoded"), CONTAINS, ts(",", var("规则值"))),
    notify("规则已存在：", var("规则值")),
    A("exit"),
    if_end(g),
]

# ── 8. 追加 + PUT ──
uNew, uB64, uPUT, uCommit, uCSHA = U(), U(), U(), U(), U()
acts += [
    text(ts(var("旧内容"), "\n", var("规则行")), uNew),
    A("base64encode", {"WFEncodeMode": "Encode",
                       "WFInput": ta(ao(uNew, "Text")), "UUID": uB64}),
    setvar("新内容B64", ao(uB64, "Base64 Encoded")),
    A("downloadurl", {
        "WFURL": ts(var("API地址")), "WFHTTPMethod": "PUT",
        "WFHTTPHeaders": headers(), "ShowHeaders": True, "Advanced": True,
        "WFHTTPBodyType": "Json",
        "WFJSONValues": dictfield([
            (ts("message"), ts("Add ", var("规则行"), " to ", var("目标文件"), " (Shortcut)")),
            (ts("content"), ts(var("新内容B64"))),
            (ts("sha"), ts(var("文件SHA"))),
            (ts("branch"), ts("main")),
        ]),
        "UUID": uPUT,
    }),
    A("getvalueforkey", {"WFDictionaryKey": "commit",
                         "WFInput": ta(ao(uPUT, "Contents of URL")), "UUID": uCommit}),
    A("getvalueforkey", {"WFDictionaryKey": "sha",
                         "WFInput": ta(ao(uCommit, "Dictionary Value")), "UUID": uCSHA}),
]
g = U()
acts += [
    if_start(g, ao(uCSHA, "Dictionary Value"), HAS_NO_VALUE),
    alert("提交失败", "提交失败，请重试（重跑会重新获取最新 sha）。响应：", ao(uPUT, "Contents of URL")),
    A("exit"),
    if_end(g),
]

# ── 9. purge CDN + 完成通知 ──
uPurge = U()
acts += [
    A("downloadurl", {"WFURL": ts("https://purge.jsdelivr.net/gh/fly48432/ACL4@main/Rules/Loon/", var("目标文件")),
                      "WFHTTPMethod": "GET", "Advanced": True, "UUID": uPurge}),
    notify("已添加 ", var("规则行"), " → ", var("目标文件")),
]

workflow = {
    "WFWorkflowClientVersion": "2605.0.5",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {"WFWorkflowIconStartColor": 946986751, "WFWorkflowIconGlyphNumber": 59511},
    "WFWorkflowImportQuestions": [],
    "WFWorkflowTypes": ["ActionExtension"],
    "WFWorkflowInputContentItemClasses": ["WFURLContentItem", "WFStringContentItem"],
    "WFWorkflowOutputContentItemClasses": [],
    "WFWorkflowHasShortcutInputVariables": True,
    "WFWorkflowActions": acts,
}

out = sys.argv[1] if len(sys.argv) > 1 else "ACL4加规则v2.shortcut"
with open(out, "wb") as f:
    plistlib.dump(workflow, f, fmt=plistlib.FMT_BINARY)
print(f"wrote {out}: {len(acts)} actions")
