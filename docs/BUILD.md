# 构建与复现

## 源码组成

- scripts/：本项目的依赖校验、源码构建入口和 Release 打包源码。
- config/bridge.conf：YR/MO 适配配置。
- third_party/l4d2-bridge/：固定提交的完整上游适配仓库快照，不包含 .git。含全部 C++ 补丁、测试、构建脚本和许可。
- dependencies.json：上游发布包、Bridge 基础提交和官方 DXVK 固定版本。

基础 Bridge 和 Detours 源码由上游 prepare_bridge.py 获取到 third_party/l4d2-bridge/.deps；本源码包不假装已经包含或重新编写它们。源码编译使用上游 MIT C++ 修改，先由 build_bridge.ps1 调用准备流程，再以 x86/x64 MSVC 构建。DXVK 后端取官方二进制；要自行编译 DXVK，请查阅 https://github.com/doitsujin/dxvk/tree/v2.6.1 的官方说明。

本项目没有新增修改游戏或网络逻辑的 C++ 补丁。区别是目标进程设置为 gamemd.exe、保守 keep 资源策略、禁用额外异常处理器以减少与 mod 处理器冲突，并将桥接客户端作为根目录 d3d9.dll 提供。配置同步放在根目录和 .l4d2bridge。

## 发布步骤

1. 修改 VERSION、文档、配置；更新依赖时同时核验 dependencies.json 中的来源和 SHA256。
2. 运行 scripts/package.ps1。默认使用固定、经过校验的上游发布二进制。
3. 检查 dist 中 ZIP 和 SHA256。脚本拒绝覆盖旧输出，先移动旧输出再重新打包。
4. 上传仓库源文件；不要上传 .cache、dist、游戏文件、个人日志或存档。
5. GitHub 创建对应版本 Release，上传 ZIP 和 .sha256。源码由 GitHub 提供下载，也可上传独立 Source ZIP。

若用 scripts/build-from-source.ps1，则需要安装 README 中的编译依赖。编译后的包由同一个 package.ps1 处理，位数、文件和 ZIP 完整性检查一致。不同编译器、时间戳和环境会导致二进制哈希变化，不承诺字节完全一致。
