# YR / MO DXVK 64 位渲染桥接

给《尤里的复仇》和心灵终结（Mental Omega）使用的 D3D9 → x64 DXVK 桥接集成包。游戏和游戏逻辑仍是 32 位，渲染后端运行在独立的 64 位进程中。

本项目参考 L4D2 Nightly 的补丁和构建方法，保留完整适配补丁，编译 NVIDIA dxvk-remix 的 Bridge。正式版搭配固定的 DXVK-GPLALL 2.6.8-2 x64 后端；源码 Nightly 同时跟踪 Remix 和 GPLALL 的最新源码。它不是重新编译的 64 位游戏引擎，也不包含游戏文件。

## 安装

1. 退出游戏和 Host，备份现有桥接文件及配置。
2. 将 Release ZIP 中的 `d3d9.dll`、根目录 `bridge.conf` 和整个 `.yrbridge` 文件夹解压到游戏根目录，与 `gamemd.exe` 同级，保留现有的 `ddraw.dll`。
3. 使用支持 D3D9 的 `cnc-ddraw`，确认 `ddraw.ini` 中生效的 `renderer=direct3d9`；MO 客户端保存设置后再核对一次。
4. 按原来的方式启动游戏；本机此前需要管理员权限才能正常启动。

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
    ├── YRBridge64.exe          # 本项目的 x64 Host
    └── d3d9vk_x64.dll           # GPLALL x64 DXVK 后端
```

不要把普通 DXVK 的 `d3d9.dll` 覆盖到本包的桥接客户端上，也不要单独双击 Host。Host 由游戏侧桥接自动启动。若可执行文件改名，需同步修改两份 `bridge.conf` 的 `client.targetProcess` 为实际游戏进程名。

## 确认生效

应同时出现 `gamemd.exe` 和 `YRBridge64.exe`。`bridge32.log` 显示握手完成，`bridge64.log` 显示 `d3d9vk_x64.dll` 加载及设备创建成功；`YRBridge64_d3d9.log` 显示 DXVK 信息。日志可能在游戏根目录或 `.yrbridge`。

原版 YR 已验证菜单和进入地图；此前的 MO 测试版已获用户确认：地图加载、存读档、连续切图和内存增长检查正常，YR 命名迁移后也能进入地图。各结果只适用于当时测试的版本，不能直接套用于后续 Nightly。标准化性能对比、长时间稳定性和多机联机仍需验证。详见 [验证记录](docs/VALIDATION.md)。

## 还原

退出游戏和 Host，恢复安装前备份的 `d3d9.dll`、两份配置、桥接目录及 `ddraw.ini`。若文件原先不存在，移走本包对应文件即可。切换普通渲染器前先移走桥接 `d3d9.dll`，避免继续进入这条链路。

## 自动构建和发布

仓库启用 Actions 后有以下入口：

| 入口 | 触发方式 | 后端与产物 |
| --- | --- | --- |
| **Build YR MO Nightly**（历史名称） | main 推送、手动运行 | 固定 GPLALL 2.6.8-2，按提交版本发布正式包 |
| **Latest Remix and GPLALL source Nightly** | main 推送、每小时第 23 分钟、手动运行 | 跟踪 Remix main 和 GPLALL 默认分支，发布预发布包 |
| **Build YR package manually** | 手动运行 | 使用构建脚本默认的固定 Remix 提交和固定后端，只上传 Actions 构建产物 |

正式版入口的 `upstream_commit` 留空跟随 Remix main，或填写完整 40 位 SHA；两个发布入口的 `force_rebuild` 可重建已有版本。定时调度仅属于源码 Nightly，GitHub 调度可能延迟。

各入口共用编译、诊断和打包流程，两个发布渠道共用发布流程，使用仓库自带的 `GITHUB_TOKEN`。替换已发布附件前先将 Release 置为草稿，回下载核验 ZIP 与 SHA256 一致后才公开；中断保留为未完成状态，下次可重试。检测已发布包时比较校验文件与 GitHub 资产摘要，缺摘要的旧资产会重新构建一次。

包内 `BACKEND.json` 与 `dependencies.json` 标明实际后端，`UPSTREAM.json` 记录构建来源。补丁冲突、编译、诊断或校验失败时不发布。详细步骤见 [构建说明](docs/BUILD.md) 和 [源码 Nightly](docs/SOURCE-NIGHTLY.md)。

本地源码构建需要 Windows、Python 3.11、Git、VS C++ x86/x64 工具链及 Windows SDK。默认使用 MSVC `14.29`，可用 `-VcVarsVer` 指定已安装的兼容版本，编译和诊断使用相同参数：

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
