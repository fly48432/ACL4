# ACL4 · 个人代理规则仓库

个人使用的 ACL 规则、代理规则与插件集合，适配 **Loon**、**Clash**、**OpenClash** 等代理客户端。

> **免责声明**
> 本仓库仅供个人学习与研究使用，所有内容均为规则配置文件，不提供任何代理服务器或节点。
> 使用者需自行遵守所在地区的相关法律法规，由此产生的任何法律责任由使用者本人承担，与本仓库作者无关。

---

## 目录结构

```
ACL4/
├── MY/              # 主配置文件（个人完整配置）
├── Rules/
│   ├── Loon/        # Loon 格式规则列表
│   └── Clash/       # Clash YAML 格式规则列表
├── Plugin/
│   └── Loon/        # Loon 插件（去广告 / 功能增强）
└── IconSet/         # 代理策略组图标
```

---

## MY/ · 主配置

| 文件 | 客户端 | 说明 |
|------|--------|------|
| `Loon.conf` | Loon | 完整 Loon 配置，含 DNS、节点订阅、远程规则引用、策略组 |
| `Clash.yaml` | Clash | Clash 配置，含多地区策略组与健康检查 |
| `openclash.yaml` | OpenClash | OpenWrt 路由器上的 Clash 配置，16 个策略组 |
| `dorian_rules.ini` | Subconverter | 订阅转换格式配置，兼容 Clash 前端 |

### 代理策略组结构

```
FINAL
└── 节点选择
    ├── 香港节点
    ├── 台湾节点
    ├── 新加坡节点
    ├── 日本节点
    ├── 韩国节点
    └── 美国节点

服务专项组
├── ChatGPT / AI 套件
├── YouTube / 流媒体
├── Telegram / 社交
├── OneDrive / iCloud
└── 游戏平台（Steam / Epic / Blizzard）
```

---

## Rules/ · 规则列表

同一规则同时提供 Loon（`.list`）和 Clash（`.yaml`）两种格式。

### 规则文件说明

| 文件名 | 用途 |
|--------|------|
| `OpenAI.list / .yaml` | ChatGPT / OpenAI 全域名及 IP 段（含 Perplexity） |
| `AISuite.list / .yaml` | AI 服务合集：Claude、Gemini、Grok、Cursor、Meta AI、Sora |
| `ProxyMedia.list / .yaml` | 代理流媒体：Twitch、Apple TV、Cake |
| `Proxy.list` | 个人代理直连域名（开发社区、Fintech 服务等） |
| `Direct.list / .yaml` | 个人直连域名（国内服务） |
| `IBKR.list` | 盈透证券（Interactive Brokers）专项规则 |
| `LAN / LAN.yaml` | 局域网 CIDR 不走代理（RFC1918 + CGNAT） |
| `CN_REGION` | 中国大陆 GEOIP 直连规则 |

---

## Plugin/Loon/ · Loon 插件

共 **144** 个插件，分为以下几类：

### 去广告

覆盖主流 App 的广告去除，包括：

- **视频**：YouTube、哔哩哔哩、爱奇艺、优酷、腾讯视频、芒果 TV
- **音乐**：Spotify、网易云音乐、QQ 音乐、酷狗音乐、虾米
- **电商**：淘宝、京东、拼多多、什么值得买
- **社交**：微博、微信公众号、微信小程序、QQ
- **工具**：百度地图、高德地图、百度网盘、迅雷
- **阅读**：知乎、豆瓣、喜马拉雅、番茄小说
- 及其他 50+ 应用

### 功能增强

| 插件 | 功能 |
|------|------|
| `TikTok_redirect.plugin` | TikTok 区域解锁（台湾/日/韩/美/欧等 15+ 地区） |
| `YouTube_remove_ads.plugin` | 去广告 + 画中画 + 字幕翻译 |
| `Spotify_lyrics_translation.plugin` | 歌词翻译 |
| `YouTubeSubtitlesTranslation.plugin` | 字幕翻译 |
| `AppleWeatherEnhancer.plugin` | 苹果天气增强 |
| `TestFlightRegionUnlock.plugin` | TestFlight 区域解锁 |
| `Auto_Join_TF.plugin` | TestFlight 自动加入 |
| `VVebo_repair.plugin` | 微博第三方客户端修复 |
| `Weixin_external_links_unlock.plugin` | 微信外链解锁 |
| `JD_Price.plugin` | 京东历史价格查询 |

### 工具 & 管理

| 插件 | 功能 |
|------|------|
| `Sub-Store.plugin` | 订阅管理面板 |
| `BoxJs.plugin` | 脚本配置界面 |
| `Script-Hub.plugin` | 社区脚本中心 |
| `LoonGallery.plugin` | 插件市场 |
| `Node_detection_tool.plugin` | 节点测速工具 |
| `WARP_Node_Query.plugin` | Cloudflare WARP 查询 |
| `Switch_github_mirror.plugin` | GitHub 镜像切换 |
| `1.1.1.1.plugin` | Cloudflare 1.1.1.1 |

### 隐私 & 安全

| 插件 | 功能 |
|------|------|
| `Prevent_DNS_Leaks.plugin` | 防 DNS 泄漏 |
| `Block_HTTPDNS.plugin` | 屏蔽 HTTPDNS |
| `BlockAdvertisers.plugin` | 广告网络拦截 |

---

## IconSet/ · 图标

策略组自定义图标：`Apple.png`、`ChatGPT.png`、`YouTube.png`

---

## DNS 配置

```
国内：223.5.5.5（阿里）、119.29.29.29（腾讯）
国外：8.8.8.8（Google）、1.1.1.1（Cloudflare）
IPv6：已启用
```

---

## 健康检查地址

```
cp.cloudflare.com/generate_204
www.gstatic.com/generate_204
```
