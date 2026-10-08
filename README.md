# YR / MO DXVK 64 位渲染桥接

给《尤里的复仇》和心灵终结（Mental Omega）使用的 D3D9 → x64 DXVK 桥接集成包。游戏和游戏逻辑仍是 32 位，渲染后端运行在独立的 64 位进程中。

本项目参考 L4D2 Nightly 的补丁和构建方法，保留已验证的完整 v1.1 适配补丁，自动编译 NVIDIA dxvk-remix main 的最新 Bridge，并搭配固定的 DXVK-GPLALL 2.6.8-2 x64 后端。它不是重新编译的 64 位游戏引擎，也不包含游戏文件。

## 安装

1. 将 Release ZIP 的内容中的 `d3d9.dll` 和 `.yrbridge` 文件夹直接解压到游戏根目录，与 `gamemd.exe` 同级。
2. 启动游戏。
3. 建议把渲染器改为 `cnc-ddraw` 。

需要 cnc-ddraw 时，可从 [官方项目](https://github.com/FunkyFr3sh/cnc-ddraw) 获取；安装其他渲染器前先还原本桥接。

```text
游戏根目录/
├── gamemd.exe
├── MentalOmegaClient.exe       # MO 原有文件
├── ddraw.dll                   # 原有、支持 D3D9 的 DirectDraw 包装器
├── ddraw.ini
├── d3d9.dll                    # 本包的 x86 桥接客户端
├── bridge.conf
└── .yrbridge/
    ├── bridge.conf
    ├── YRBridge64.exe         # x64 Host，名称沿用上游
    └── d3d9vk_x64.dll           # GPLALL x64 DXVK 后端
```

不要把普通 DXVK 的 `d3d9.dll` 覆盖到本包的桥接客户端上，也不要单独双击 Host。Host 由游戏侧桥接自动启动。若可执行文件改名，需同步修改两份 `bridge.conf` 的 `client.targetProcess` 为实际游戏进程名。

## 确认生效

应同时出现 `gamemd.exe` 和 `YRBridge64.exe`。`bridge32.log` 显示握手完成，`bridge64.log` 显示 `d3d9vk_x64.dll` 加载及设备创建成功；`YRBridge64_d3d9.log` 显示 DXVK 信息。日志可能在游戏根目录或 `.yrbridge`。

本机原版 YR 已验证管理员启动、正常菜单和进入地图；用户报告 MO 手动安装链路可用。未进行标准化的长时间、存读档、性能或多机联机测试，不把“能够运行”解释为所有同步问题均已解决。详见 [验证记录](docs/VALIDATION.md)。

## 还原

退出游戏和 Host，恢复安装前备份的 `d3d9.dll`、两份配置、桥接目录及 `ddraw.ini`。若文件原先不存在，移走本包对应文件即可。切换普通渲染器前先移走桥接 `d3d9.dll`，避免继续进入这条链路。

## 自动构建和发布

推送本仓库至默认分支后，在 Actions 中启用 **Build YR MO Nightly**。
每小时第 23 分钟检查 NVIDIA main；GitHub 调度可能延迟。检测新提交后编译 x86 客户端及匹配 x64 Host，运行诊断测试，再自动发布预发布版。
手动执行 Run workflow 时，upstream_commit 留空跟随 main，或填写完整 40 位 SHA。force_rebuild 可重建已有版本。
使用仓库自带 GITHUB_TOKEN，无需个人令牌。发布任务具备 contents:write 权限。

config/backend.json 固定 GPLALL 2.6.8-2 的下载地址和 SHA256。后端不会自动升级；更新该文件后，它与 Bridge 适配补丁的指纹会参与发布标签，即使 Bridge 没变化也能生成新包。
补丁冲突、编译、诊断或校验失败时不发布。游戏兼容性仍需实测。

本地源码构建需要 Windows、Python 3.11、Git、VS C++ x86/x64 工具链及 Windows SDK：

```powershell
python -m pip install meson==1.3.2 ninja==1.11.1.1
pwsh -File scripts/build-from-source.ps1 -UpstreamCommit <完整提交SHA>
```

输出 ZIP 的文件直接解压到游戏根目录，无 bin 层，不包含 ddraw.dll。
手动打包工作流同样从源码构建 YR 命名的运行文件，不再直接重打包旧 L4D2 二进制。

## 归属

原作者版权和许可保留于 `licenses/`、`third_party/l4d2-bridge/` 和 [THIRD_PARTY.md](THIRD_PARTY.md)。新增适配、配置及打包代码采用 MIT。详见 [LICENSE](LICENSE)。项目不隶属于 EA、Valve 或 NVIDIA。

## v1.0 命名和版本规则

运行目录为 `.yrbridge`，Host 为 `YRBridge64.exe`。客户端和Host必须一起更新，仅重命名旧目录不够。备份后安装新包；两份配置中的资源数据库路径改为 `.yrbridge/resource-retention.db`。如需沿用数据库，退出游戏后将旧目录的数据库复制到新目录。旧目录可留作回退。

本次命名提交发布 v1.0，随后 main 的重大功能提交生成 v1.1、v1.2 等，小修复生成 v1.0.1、v1.0.2 或 v1.1.1、v1.1.2 等；多个提交一次推送可能跳过中间发布号。VERSION 是基础版本，发布包 VERSION 按构建提交生成。state/versioning.json 固定版本起点，不要重写起点之后的提交历史。main push 自动构建发布，定时上游构建使用当前版本加 nightly 后缀。

提交末尾可写 `Release-Level: minor` 表示重大更新，`Release-Level: patch` 表示小修复，`Release-Level: major` 表示大版本变化。没有标记时 feat: 提交提升次版本，其余提交提升修复号。升级次版本后修复号归零。提交消息参与版本计算，不需要机器人额外提交。

自动追踪 Remix 与 GPLALL 最新源码并发布预览包：[源码 Nightly 说明](docs/SOURCE-NIGHTLY.md)。
