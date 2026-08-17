# DECISION：2B 模型安装器方案与 NSIS 打包（2026-08-17）

## 决策 1：2B 模型分发载体 = NSIS 自解压安装器（非 7-Zip SFX）
- **背景**：原计划 7-Zip SFX；但 7z 安装器被系统 MOTW/策略拦截（下载的 exe 执行报"已被用户取消"，Unblock-File 无效）。
- **决定**：用已有 NSIS（tauri-bundler 缓存 `%LOCALAPPDATA%\tauri\NSIS\makensis.exe`）制作独立安装器。
- **结果**：`dist/PaperLens_Qwen3.5-2B-Q4_K_M_installer.exe`（1.28GB）。

## 决策 2：2B 安装器不做目录选择页，强制落应用扫描目录
- **背景**：用户安装时被"选目录"困惑，且模型必须落在后端实际扫描的 `{数据目录}/models/`。
- **决定**：去掉 `MUI_PAGE_DIRECTORY`，`.onInit` 按 `config.py` 同款逻辑计算：D 盘存在 → `D:\PaperLens\models`，否则 `%LOCALAPPDATA%\PaperLens\models`。
- **结果**：双击即装、绝不装错；用户不再需要选位置。

## 决策 3：`SetCompress off`（不用 `/SOLID lzma`）
- **证据**：`/SOLID lzma` + 单文件 1.19GB → 解压挂起（0 字节卡死 >10min）；`SetCompress off` 同脚本 → 解压成功。
- **理由**：GGUF 不可压缩（LZMA 压缩率 98.6%，仅省 ~17MB），体积收益可忽略，换取确定性。
- **结果**：安装器 1.281GB < NSIS 2GiB 硬上限。

## 决策 4：D 盘检测用 `GetDriveType`（弃用 `${FileExists} "D:\"`）
- **证据**：`${FileExists} "D:\"` 在 D 盘存在时返回 false（实测多次复现）；`GetDriveType` 返回 1=DRIVE_NO_ROOT_DIR 判定准确。
- **影响面**：`model_installer.nsi` + 主安装器 `installer.nsi` 两处同步修改。

## 决策 5：主安装器保留 tauri 模板的"恢复上次安装位置"行为
- **注意**：`RestorePreviousInstallLocation` 会读 `HKCU\Software\PaperLens\PaperLens` 恢复旧路径——首次安装不受影响；若用户手动改过安装目录，升级会沿用旧目录（tauri 设计如此，保留）。

## 决策 6：`bundle-resources/` 不入库
- 由 `assets/` 经脚本生成（0.8B 拷贝 + `ecdict_import.py`），与 `assets/models/` 同策略加入 `.gitignore`，避免 800MB 二进制入库。

## 决策 7：发布物清单
| 产物 | 路径 | 体积 | 说明 |
|------|------|------|------|
| 主安装包 | `target/release/bundle/nsis/PaperLens_0.1.0_x64-setup.exe` | 740MB | 含 0.8B 模型、ecdict、OCR、server onefile |
| 2B 离线包 | `dist/PaperLens_Qwen3.5-2B-Q4_K_M_installer.exe` | 1.28GB | 可选，无网用户用；联网用户可直接应用内下载 |
