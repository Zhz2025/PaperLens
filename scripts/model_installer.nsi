Unicode true

Name "PaperLens 2B 模型包"
OutFile "..\dist\PaperLens_Qwen3.5-2B-Q4_K_M_installer.exe"
InstallDir "E:\PaperLens\data\models"

RequestExecutionLevel user

; GGUF 不可压缩（LZMA 仅省 ~17MB），且 NSIS /SOLID lzma 对单文件 >1GiB 的解压会挂起（实测 0 字节卡死）
; 故用不压缩存储，简单可靠
SetCompress off

!include MUI2.nsh

!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_TEXT "2B 模型已安装到 PaperLens 数据目录（E:\PaperLens\data\models）。重新打开 PaperLens 后即可在设置页切换到 Qwen3.5-2B。"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "SimpChinese"

Function .onInit
  ; 本机定制版：无 D 盘且禁用 C 盘，数据目录固定为 E:\PaperLens\data，
  ; 模型写入其 models/ 子目录。刻意不提供目录选择页：模型必须落在应用
  ; 实际扫描的目录，避免装错位置。
  StrCpy $INSTDIR "E:\PaperLens\data\models"
  DetailPrint "Customized INSTDIR=$INSTDIR"
FunctionEnd

Section "Install"
  SetOutPath "$INSTDIR"
  File "..\assets\models\Qwen3.5-2B-Q4_K_M.gguf"
  WriteRegStr HKCU "Software\PaperLens\model-2b" "InstallDir" "$INSTDIR"
SectionEnd
