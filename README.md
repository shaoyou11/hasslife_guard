# HassLife 白名单保护

检查已有 HassLife 白名单基线，保留现有保护策略。

## 安装与更新

在 HACS / Home Assistant Marketplace 的自定义仓库中添加 `shaoyou11/hasslife_guard`，类型选择 Integration。下载后重启 Home Assistant，在“设备与服务”中添加本集成；已有配置项会继续复用，更新不要求删除实体或重新配对。

当前版本：`0.1.1`。发布版本使用 GitHub Releases，更新前请创建 Home Assistant 备份；若行为异常，可通过 Marketplace 重新下载上一个版本并重启回滚。

## 使用边界

这是自建辅助集成，需要已配置的原生或上游集成。不会替代原设备集成，配置项、历史记录和配对不包含在此仓库。图标为本地生成的辅助集成图标，不表示获得硬件厂商认证。

具体依赖以 `custom_components/hasslife_guard/manifest.json` 为准。已有部署可能具有特定设备约束；安装前检查配置流程和兼容性保护。不要同时安装重复的辅助补丁。

## 验证与维护

每个集成独立仓库和版本，Python 文件编译检查后发布；升级不会自动同时更新其他集成。问题请提交到本仓库 Issues，日志和诊断请先移除账号、令牌、地址与位置信息。

首次建立发布基线仅补充品牌资源、文档、更新元数据及持续检查，保留运行逻辑。自建辅助代码尚未宣称达到 Home Assistant 官方质量等级。
