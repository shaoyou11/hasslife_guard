# HassLife 白名单守卫实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建可独立安装、可单独禁用的 HassLife 白名单守卫，并通过 HACS 自定义仓库安装。

**Architecture:** 使用标准 Home Assistant Config Entry 自定义集成。纯 Python 校验模块负责读取 HassLife 源文件、验证三处白名单拦截并生成基线摘要；HA 层用 DataUpdateCoordinator 在启动和 12 小时周期执行校验，并暴露状态实体和两个操作按钮。守卫的目录独立于 HassLife，HACS 更新 HassLife 不会覆盖它。

**Tech Stack:** Python 3、Home Assistant Config Flow、DataUpdateCoordinator、pytest、GitHub CLI、HACS custom repository。

**Spec:** `docs/superpowers/specs/2026-08-30-hasslife-guard-design.md`

## Global Constraints

- 默认检查周期为 12 小时。
- 不直接编辑 `.storage`。
- 不在仓库、日志或回复中保存或显示账号密码、令牌及其他秘密。
- 未通过三处保护校验时不自动接受当前代码为新基线。

---

### Task 1: 白名单源代码校验核心

**Files:**
- Create: `tests/test_guard_core.py`
- Create: `custom_components/hasslife_guard/guard_core.py`

**Interfaces:**
- Produces `SourceCheckResult` and `check_hasslife_source(root, expected_digest=None)`。

- [ ] **Step 1: Write the failing test**

测试有效源文件、缺失拦截标记、基线摘要变化和无效 manifest 四种行为。

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q tests/test_guard_core.py`

Expected: FAIL because `custom_components.hasslife_guard.guard_core` does not exist。

- [ ] **Step 3: Write minimal implementation**

实现限定文件读取、UTF-8 解析、必需标记校验、manifest 版本读取和 SHA-256 摘要生成。

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest -q tests/test_guard_core.py`

Expected: PASS。

### Task 2: Home Assistant 集成、实体和配置流

**Files:**
- Create: `custom_components/hasslife_guard/__init__.py`
- Create: `custom_components/hasslife_guard/const.py`
- Create: `custom_components/hasslife_guard/coordinator.py`
- Create: `custom_components/hasslife_guard/binary_sensor.py`
- Create: `custom_components/hasslife_guard/button.py`
- Create: `custom_components/hasslife_guard/config_flow.py`
- Create: `custom_components/hasslife_guard/manifest.json`
- Create: `custom_components/hasslife_guard/strings.json`
- Create: `custom_components/hasslife_guard/translations/en.json`
- Create: `custom_components/hasslife_guard/translations/zh-Hans.json`

**Interfaces:**
- Exposes a binary sensor, immediate-check button, baseline-accept button, and Config Entry options flow。
- Uses `hass.config_entries.async_set_disabled_by(..., ConfigEntryDisabler.USER)` to stop HassLife after a failed check。

- [ ] **Step 1: Write the failing test**

补充纯函数设置合并和默认周期测试，要求默认周期为 12 小时、自动停用默认开启。

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest -q tests`

Expected: FAIL because integration constants and settings helpers do not exist。

- [ ] **Step 3: Write minimal implementation**

实现配置流、协调器、状态属性、持久通知、异常时停用 HassLife、手动基线确认和卸载清理。

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest -q tests`

Expected: PASS。

### Task 3: HACS 仓库元数据和交付文档

**Files:**
- Create: `hacs.json`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.github/workflows/validate.yml`

- [ ] **Step 1: Run repository validation**

Run: `pytest -q` and `python -m compileall -q custom_components tests`。

- [ ] **Step 2: Review secret scan**

Run: `rg -n -i '(password|token|api[_-]?key|secret)\s*[:=]\s*[^<\[({"'"'']' . --glob '!tests/test_guard_core.py'`。

Expected: no real credential values。

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "新增HassLife白名单守卫集成"
```

### Task 4: GitHub 与 Home Assistant 安装验证

**Files:**
- No source changes。

- [ ] **Step 1: Create or update the `shaoyou11/hasslife_guard` GitHub repository**

只推送已通过本地测试的代码，不推送 HA 配置、备份、账号或令牌。

- [ ] **Step 2: Add the repository to HACS as an integration**

使用 HACS 自定义仓库入口添加 `shaoyou11/hasslife_guard`，再下载安装。

- [ ] **Step 3: Restart and validate**

重启前先通过 HA 配置检查；重启后读取 `hasslife_guard` 配置条目、守卫状态实体、按钮和 HassLife 条目状态，确认 HomeKit Bridge 未被改动。
