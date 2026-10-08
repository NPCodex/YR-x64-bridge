# 自动源码 Nightly

工作流：`.github/workflows/source-nightly.yml`，每小时第 23 分钟检查，也支持 main 推送和 Actions 手动运行。

- NVIDIA dxvk-remix 跟踪 main；用于编译 32 位 d3d9.dll 和配套 64 位 YRBridge64.exe。
- Digger1955/dxvk-gplall 跟踪 GitHub 的默认分支；使用上游 GCC 构建环境与编译选项，编译 x64 d3d9.dll，打包为 .yrbridge/d3d9vk_x64.dll。默认分支变化会自动跟随，并非只等待 Release。
- 检测阶段锁定两个完整提交 SHA，后续任务只编译这两个提交。标签包含版本、两个源码 SHA 和构建配方指纹；任一改变就构建，完整同名发布已存在则跳过。手动 force_rebuild 可重建。
- PE 位数、文件哈希及 Bridge 诊断通过后，自动发布 GitHub **预发布版**，附 ZIP 与 SHA256。编译失败不会发布新的包；实际地图兼容性仍需测试。
- BACKEND.json 与 dependencies.json 记录 GPLALL 源码提交和 DLL 哈希；UPSTREAM.json 记录 Remix 与本仓库提交。
- 原 nightly.yml 保留正式版本构建入口及固定已验证 GPLALL Release 后端，取消原定时触发。正式版本递增规则不变。

使用：GitHub → Actions → Latest Remix and GPLALL source Nightly → Run workflow。仓库需启用 Actions，发布任务使用内置 GITHUB_TOKEN，无需新增密钥。

安装：解压 ZIP 到游戏根目录，保留 .yrbridge 目录结构。Nightly 为测试版，更新前备份当前已验证补丁。
