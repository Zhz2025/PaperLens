# AGENT-REPORT：发布阻断修复与打包（2026-08-17）

## 背景
将 PaperLens 打包为可分发的 NSIS 安装包（Windows）：
- 不含用户账号数据
- LLM 模型随包分发：0.8B 内置主包，2B 独立可选自解压包
- 默认安装到 `D:\PaperLens\PaperLens`（无 D 盘回退 `%LOCALAPPDATA%\PaperLens`）

## 一、代码修复（13 项，全部通过验证）
| 类别 | 文件 | 关键修复 |
|------|------|----------|
| 前端 | `client.ts:8` `sse.ts:30` | `BASE = 'http://127.0.0.1:8737/api'` 绝对地址，SSE 复用 |
| 后端 | `main.py:11-15` | CORS 增加 `http://tauri.localhost`（生产源，无 `tauri://localhost`） |
| 后端 | `config.py` | 数据目录 env 优先 + `bundled_models_dir`/`bundled_ecdict_path` 只读目录注入 |
| 后端 | `llm_service.py` | 合并扫描数据目录 + bundled 目录，size_bytes 修正 532,517,120 |
| 后端 | `ecdict_service.py` | fallback 重构（`_tried` 延迟置位，数据目录优先 → bundled 兜底） |
| 后端 | `backup_service.py:93` | 硬编码 `data_dir/files` → `get_settings().files_dir` |
| Rust | `lib.rs` | `SIDECAR_BIN="paperlens-server"`（纯名，tauri-plugin-shell 扁平解析）、D 盘 fallback、`PAPERLENS_PORT/MODELS/ECDICT/OCR_EXE` 环境注入 |
| Rust | `capabilities/default.json` | name 对齐 `paperlens-server` |

## 二、本轮新增修复（2 项发布阻断，本报告重点）
1. **2B 模型安装器 `/SOLID lzma` 解压挂起**（`scripts/model_installer.nsi`）
   - 现象：单文件 ~1.19GB 的 GGUF 在 LZMA 压缩包内解压时**卡死且文件停留在 0 字节**（实测挂起 >10 分钟）；此前还出现过快速 exit code 2。
   - 根因：NSIS `/SOLID lzma` 对 >1GiB 单文件解压的已知缺陷。
   - 修复：改用 `SetCompress off`（GGUF 不可压缩，LZMA 仅省 ~17MB，纯属自找麻烦）；安装包 1.28GB，仍在 NSIS 2GiB 上限内。
2. **D 盘检测 `${FileExists} "D:\"` 不可靠**（`model_installer.nsi` + 主安装器 `installer.nsi`）
   - 现象：D 盘存在时仍返回 false，安装落到 `%LOCALAPPDATA%`（用户实际踩中："装错位置"）。
   - 根因：NSIS `IfFileExists` 对盘根目录判定不可靠。
   - 修复：改用 `System::Call 'kernel32::GetDriveType(t "D:\") i .R0'`（返回 1=DRIVE_NO_ROOT_DIR 表示盘不存在），与后端 `config.py` 的 `os.path.isdir("D:\\")` 语义一致。

## 三、打包配置
| 产物 | 路径 | 关键点 |
|------|------|--------|
| server onefile spec | `scripts/package_server_onefile.spec` | `console=True`（console=False 导致 parent 3s 退出 code 3），无 COLLECT |
| tauri.conf.json | `apps/desktop/src-tauri/tauri.conf.json` | resources Map 形式、`nsis.template="installer.nsi"`、`installMode=currentUser` |
| NSIS 模板 | `apps/desktop/src-tauri/installer.nsi` | 默认 `D:\PaperLens\PaperLens`、GetDriveType 盘符检测、卸载清理 |
| 2B 安装器 | `scripts/model_installer.nsi` | 无目录选择页、SetCompress off、GetDriveType、自动落 `{数据目录}/models/` |

## 四、资产生成
| 资产 | 大小 | 来源/生成 |
|------|------|-----------|
| 0.8B 模型 | 508 MB | `assets/models/...0.8B...gguf` → `bundle-resources/models/` |
| ecdict.db | 296 MB | `scripts/ecdict_import.py` 裁剪 → `bundle-resources/ecdict.db` |
| OCR worker | 269 MB | `ocr-dist/paperlens-ocr` onedir |

## 五、验证结果（全绿）
| 测试 | 结果 |
|------|------|
| pytest | 116 passed |
| npm run build（tsc + vite） | ✅ |
| cargo check | ✅ |
| 2B 安装器静默安装 | EXIT=0，模型落 `D:\PaperLens\models`，注册表 InstallDir 正确 |
| 主安装器静默安装 | EXIT=0，应用落 `D:\PaperLens\PaperLens`，InstallLocation 注册表正确 |
| 端到端启动 | health ok；模型扫描 0.8B+2B 均 downloaded=true；退出级联清理 ✅ |
| CORS 三源 | tauri.localhost / localhost:5173 通过；恶意源拦截 ✅ |
| 无用户数据 | bundle-resources 仅 ecdict.db + 0.8B 模型；无 .token/db/backups ✅ |

## 六、待办
- [x] 2B 安装器验证
- [x] 全链路验证
- [ ] 发布说明 / sha256 校验（可选）
