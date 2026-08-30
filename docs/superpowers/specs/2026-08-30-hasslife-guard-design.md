# HassLife 白名单守卫设计

## 目标

为 HassLife 增加一个独立于 `custom_components/hasslife` 的 Home Assistant 自定义集成，检测 HACS 更新是否覆盖本地白名单定制代码，并在风险状态下停止 HassLife 同步，避免恢复全量设备控制。

## 约束

- 守卫代码不放在 HassLife 目录内，HACS 更新 HassLife 时不得覆盖守卫。
- 不直接编辑 Home Assistant `.storage`；配置和基线通过 Config Entry 选项保存。
- 默认在 HA 启动时检查一次，之后每 12 小时检查一次。
- 检查只读取本地 HassLife 源文件，不访问设备、不发起网络请求、不重载 HomeKit。
- 初次安装只在当前代码通过三处白名单拦截校验后建立基线。
- 发现源文件发生变化时，不自动接受新代码；默认停用 HassLife 配置条目并发送持久通知。
- 用户可以分别禁用 `hasslife` 和 `hasslife_guard`，禁用守卫不得影响 HomeKit Bridge 或其他设备集成。

## 三处保护校验

1. 状态同步必须调用本地 `is_entity_allowed`。
2. 设备发现列表必须过滤本地白名单。
3. 远程控制请求必须拒绝缺少 `entity_id` 或包含白名单外实体的请求。

## 用户操作

- `binary_sensor.hasslife_guard_whitelist_protection`：显示当前守卫状态和检查结果。
- `button.hasslife_guard_check_now`：立即检查，不自动接受发生变化的代码。
- `button.hasslife_guard_accept_current_baseline`：仅在三处保护校验通过时，将当前代码设为新基线。
- 配置选项可设置检查周期和发现异常时是否自动停用 HassLife，默认周期为 12 小时且启用停用保护。
