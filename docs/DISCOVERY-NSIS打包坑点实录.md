# DISCOVERY：NSIS 打包坑点实录（2026-08-17）

## 1. `/SOLID lzma` + 单文件 >1GiB 解压挂起
- **现象**：1.19GB GGUF 解压卡死，文件停在 0 字节（>10min 无进展，超时被杀）；个别构建快速 exit code 2。
- **证据**：同脚本 `SetCompress off` → 解压成功、文件完整（GGUF magic 校验通过）。对比实验：`/SOLID lzma` 挂起 vs `SetCompress off` 正常，其余代码完全一致。
- **结论**：模型类不可压缩大文件一律 `SetCompress off`（或拆文件），别用 solid LZMA。

## 2. `${FileExists} "D:\"` 对盘根判定不可靠
- **现象**：D 盘存在仍返回 false → 装到 `%LOCALAPPDATA%`。
- **证据**：安装器日志反复输出 "No D -> INSTDIR=LOCALAPPDATA"，而 `ls /d/` 正常。
- **结论**：盘符存在性判定用 `System::Call 'kernel32::GetDriveType(t "D:\") i .R0'`（1=DRIVE_NO_ROOT_DIR），或 `${DriveExists}`（tauri 版 NSIS 的 WordFunc 太旧没有此宏）。

## 3. NSIS 脚本必须 UTF-8 **带 BOM**
- **现象**：脚本含中文时 `makensis` 报 "Bad text encoding: xxx.nsi:3" 直接中止编译。
- **结论**：写文件工具不带 BOM，需额外补 `\xEF\xBB\xBF` 前缀。

## 4. MSYS `tasklist`/`reg` 不可靠
- **现象**：`tasklist | grep makensis` 漏报实际运行中的进程（误判构建死亡，重跑导致两个 makensis 抢同一输出文件）；`reg query` 漏报实际存在的注册表键。
- **结论**：监控进程用 PowerShell `Get-Process`；读注册表用 PowerShell `Get-ItemProperty`。

## 5. tauri 模板 `RestorePreviousInstallLocation` 会恢复旧安装路径
- **现象**：残留 `HKCU\Software\PaperLens\PaperLens` 让新静默安装装回已删除的旧目录。
- **结论**：验收"默认装 D 盘"前必须清掉旧注册表残留；对用户而言首次安装无此问题。

## 6. 编译中断会留孤儿 makensis + 损坏 exe
- **现象**：超时杀掉编译后，遗留孤儿 `makensis` 进程占用输出文件，后续运行报"文件被占用"，且产生**坏 exe 假象**（曾被误判为安装器 bug）。
- **结论**：重编前先杀残留进程；用干净重编排除坏 exe 干扰（本次靠这个纠正了 2 次误判）。

## 7. PyInstaller onefile + `console=False` 致命（继承自交接）
- parent 3s 异常退出 code 3、Job Object 失效；`console=True` 解决（Tauri GUI 父进程拉起无黑窗）。

## 8. tauri-bundler NSIS 缓存脆弱（继承自交接）
- 缺 `Plugins/x86-unicode/additional/nsis_tauri_utils.dll` 会删目录重下（GitHub 超时）；缺文件手动补全，勿动缓存逻辑。

## 9. CORS 生产源只有 `http://tauri.localhost`（继承自交接）
- Tauri 源码无 `tauri://localhost`；`"tauri.localhost"` 无 scheme 永不匹配。
