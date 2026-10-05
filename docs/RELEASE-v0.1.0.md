# v0.1.0 — YR / MO DXVK x64 Bridge

首个简单手动安装的集成版本。将 ZIP 内容解压到游戏根目录，保留现有支持 D3D9 的 ddraw.dll，将渲染器设为 direct3d9，以管理员身份启动游戏或 MentalOmegaClient.exe。

包含：x86 D3D9 Bridge 客户端、x64 Host、官方 DXVK 2.6.1 x64 后端、YR/MO 保守配置、文档、文件校验和原作者许可。游戏引擎仍为32位；不修改游戏、Ares、Phobos 或网络代码。

验证：原版 YR 的菜单和进入地图正常，日志显示64位后端初始化成功；用户报告 MO 简化安装可用。长时间稳定性、性能及联机同步未完成标准化验证。

安装前备份 d3d9.dll、bridge.conf、.l4d2bridge 和 ddraw.ini。详细安装/还原见 ZIP 内 README.md。请下载二进制 Release ZIP；GitHub 自动生成的 Source code ZIP 用于开发，不能直接当游戏补丁安装。
