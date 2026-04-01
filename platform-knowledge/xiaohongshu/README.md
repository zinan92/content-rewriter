# 小红书平台知识库

本目录包含小红书内容创作的平台规则、设计模式和调性指南。
这些知识直接被 content-rewriter 的 XHS adapter prompt 和 videocut cover 模板使用。

## 文件索引

| 文件 | 内容 | 用途 |
|------|------|------|
| [algorithm.md](algorithm.md) | CES 评分、推荐机制、限流规则、发布时间 | rewriter prompt 的算法意识 |
| [content-formats.md](content-formats.md) | 4 种封面类型 + 适用场景 + 设计规格 | cover 模板选择逻辑 |
| [banned-words.md](banned-words.md) | 触发限流的禁词分类表 | rewriter prompt 的禁词过滤 |

## 数据来源

- 小红书星云 5.0 算法官方文档（2025）
- 知乎/运营派/青瓜传媒的 CES 评分拆解
- 实际 feed 截图分析（2026-04-01，Wendy 的发现页）
- dontbesilent、早起虫子、千狐商业增长、就叫陈金水 等高互动账号的封面拆解

## 更新日志

- 2026-04-01: 初始版本，基于 CES 5.0 研究 + feed 截图归类分析
