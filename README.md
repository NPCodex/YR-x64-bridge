# YR / MO DXVK 64 位渲染桥接

给《尤里的复仇》和心灵终结（Mental Omega）使用的 D3D9 → x64 DXVK 桥接集成包。游戏和游戏逻辑仍是 32 位，渲染后端运行在独立的 64 位进程中。

本项目复用 yeyunyyds 的 L4D2 Bridge v1.1 和官方 DXVK 2.6.1，提供 YR/MO 配置、简单安装说明、固定依赖和发布脚本。它不是重新编译的 64 位游戏引擎，也不包含游戏文件。

## 安装

1. 将 Release ZIP 的内容直接解压到游戏根目录，与 `gamemd.exe` 同级。
2. 建议使用 cnc-ddraw 渲染器。
3. 启动游戏。

需要 cnc-ddraw 时，可从 [官方项目](https://github.com/FunkyFr3sh/cnc-ddraw) 获取；安装其他渲染器前先还原本桥接。

```text
游戏根目录/
├── gamemd.exe
├── MentalOmegaClient.exe       # MO 原有文件
├── ddraw.dll                   # 原有、支持 D3D9 的 DirectDraw 包装器
├── ddraw.ini
├── d3d9.dll                    # 本包的 x86 桥接客户端
├── bridge.conf
└── .l4d2bridge/
    ├── bridge.conf
    ├── L4D2Bridge64.exe         # x64 Host，名称沿用上游
    └── d3d9vk_x64.dll           # 官方 x64 DXVK 后端
```

不要把普通 DXVK 的 `d3d9.dll` 覆盖到本包的桥接客户端上，也不要单独双击 Host。Host 由游戏侧桥接自动启动。若可执行文件改名，需同步修改两份 `bridge.conf` 的 `client.targetProcess` 为实际游戏进程名。

## 确认生效

应同时出现 `gamemd.exe` 和 `L4D2Bridge64.exe`。`bridge32.log` 显示握手完成，`bridge64.log` 显示 `d3d9vk_x64.dll` 加载及设备创建成功；`L4D2Bridge64_d3d9.log` 显示 DXVK 信息。日志可能在游戏根目录或 `.l4d2bridge`。

本机原版 YR 已验证管理员启动、正常菜单和进入地图；用户报告 MO 手动安装链路可用。未进行标准化的长时间、存读档、性能或多机联机测试，不把“能够运行”解释为所有同步问题均已解决。详见 [验证记录](docs/VALIDATION.md)。

## 还原

退出游戏和 Host，恢复安装前备份的 `d3d9.dll`、两份配置、桥接目录及 `ddraw.ini`。若文件原先不存在，移走本包对应文件即可。切换普通渲染器前先移走桥接 `d3d9.dll`，避免继续进入这条链路。

## 源码和发布

仅重新打包已发布二进制，无需编译器：

```powershell
pwsh -File scripts/package.ps1
```

脚本下载固定发布包、校验 SHA256 和 PE 位数，生成 `dist/YR-MO-DXVK64-Bridge-v0.1.0.zip`。本地已有对应完整上游包时，可传 `-BridgeDirectory`。压缩包包含 `.l4d2bridge` 和许可证，不包含游戏或 cnc-ddraw。

从 Bridge 源码编译：

```powershell
python -m pip install meson==1.3.2 ninja==1.11.1.1
pwsh -File scripts/build-from-source.ps1
```

需要 Git、Python 3.11、Windows PowerShell、Visual Studio C++ x86/x64 工具链（上游参考 MSVC 14.29）和 Windows SDK。`-VcVarsVer` 可指定已安装工具链版本；其他版本兼容性需自行验证。脚本使用随附上游源码补丁和固定 RTX Remix Bridge 提交获取实际基础源码，编译客户端与 Host，再执行本项目打包。DXVK 使用校验后的官方二进制；其源码在固定 v2.6.1 标签。详见 [构建说明](docs/BUILD.md)。

将本目录内容上传为 GitHub 仓库即可。创建 `v0.1.0` Release，上传 `dist` 中的 ZIP 和 `.sha256`，正文可使用 [发布说明](docs/RELEASE-v0.1.0.md)。附带的工作流通过固定上游发布包组装附件；它不声称从源码编译，也不自动发布 Release。

## 归属

原作者版权和许可保留于 `licenses/`、`third_party/l4d2-bridge/` 和 [THIRD_PARTY.md](THIRD_PARTY.md)。新增适配、配置及打包代码采用 MIT。详见 [LICENSE](LICENSE)。项目不隶属于 EA、Valve 或 NVIDIA。
