# HassLife 白名单守卫

这是一个 Home Assistant 自定义集成，用于保护本地 `hasslife` 定制代码中的实体白名单逻辑。

它不会改 HomeKit 配置，也不会替用户自动放行未知代码。默认每 12 小时检查一次；首次检查保存当前代码的哈希基线，之后发现 HassLife 被 HACS 更新、文件缺失或白名单拦截标记缺失时：

1. 创建持久通知，说明失败原因。
2. 默认停用 HassLife 配置条目，避免未审核代码继续同步实体。
3. 保留当前基线，等待人工检查。

## 安装

在 HACS 中选择“自定义存储库”，添加 `shaoyou11/hasslife_guard`，类型选择 `Integration`，下载安装后重启 Home Assistant。

然后在“设置 -> 设备与服务 -> 添加集成”中搜索 `HassLife Whitelist Guard` 并添加。

这里使用的是 HACS 自定义存储库，不代表已经进入 HACS 官方默认目录。

## 设置

- 兜底检查间隔默认 12 小时，可在集成选项中修改，范围为 1 到 168 小时。
- `白名单保护`：开启表示当前 HassLife 源代码通过检查。
- `立即检查白名单`：重新检查，但不会接受代码变化。
- `接受当前版本为基线`：只在检查通过并确认代码无误后使用；它不会自动启用已停用的 HassLife。
- `检查失败时自动停用 HassLife`：默认开启，可在选项中关闭。

## 与现有 HassLife 的关系

守卫只检查和停用 `hasslife` 配置条目，不会修改其实体白名单选项，也不会修改 HomeKit Bridge。停用守卫本身不会停用 HomeKit；停用 HassLife 也不会移除 HomeKit 实体。

本项目只负责发现更新并 fail-closed，不会自动把 HACS 更新回滚或自动修改上游 HassLife 源码。每次更新后应先检查本地白名单补丁，再接受新的基线。

## 开发校验

```text
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests
```
