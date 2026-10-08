# 构建与打包

## GitHub Actions

- `.github/workflows/nightly.yml`：main 推送或手动运行；使用 Remix main 或指定完整 SHA，后端固定为 `config/backend.json`，发布正式版本。
- `.github/workflows/source-nightly.yml`：main 推送、每小时第 23 分钟或手动运行；锁定 Remix 与 GPLALL 两个源码提交，发布预发布版。
- `.github/workflows/package.yml`：手动生成固定后端的包，Remix 使用构建脚本默认提交，只保存 Actions artifact。

入口复用 `build-bridge.yml` 的 Windows 编译、诊断和打包步骤，两个发布渠道复用 `publish-release.yml`。版本仍按提交计算，规则见 [README](../README.md)。

## 本地构建

需要 Windows、Python 3.11、Git、MSVC x86/x64 工具链和 Windows SDK。确保 `python` 指向实际解释器。

```powershell
python -m pip install meson==1.3.2 ninja==1.11.1.1
pwsh -File scripts/build-from-source.ps1 -UpstreamCommit <完整40位SHA> -VcVarsVer 14.29
```

`-VcVarsVer` 同时用于编译与诊断。默认后端由 `config/backend.json` 指定；自定义后端可传 `-DxvkDll <x64-d3d9.dll路径>`。源码 Nightly 显式同时传入 `-BackendMetadata <source-backend.json路径>`，元数据必须与本次 DLL 的 SHA256 一致，并在旁边提供 `DXVK-GPLALL-LICENSE.txt`。未指定元数据时，不使用之前 Nightly 留下的源码元数据。

最终包从本次中间包读取 `BACKEND.json` 和 `UPSTREAM.json`，不依赖环境变量或其他构建的缓存。最终 `dependencies.json` 与实际 `BACKEND.json` 一致。

打包先在独立暂存目录完成校验，再生成正式输出；失败清理本次暂存内容，保留已有发布文件。已有同名中间包、发布目录、ZIP 或校验文件时，需要先将旧产物归档再重新打包，不会静默覆盖。

输出在 `dist/`；解压后 `d3d9.dll`、根目录 `bridge.conf` 和 `.yrbridge/` 直接放入游戏根目录，不包含 `ddraw.dll`。源码 checkout 若已有其他提交或本地更改，准备脚本会停止，保留现场供检查。

## 验证

```powershell
python -m unittest discover -s tests
python -m unittest discover -s third_party/l4d2-bridge/tests
```

源码构建还会执行 C++ 诊断，包含队列开关关闭、开启、两端设置不同，以及 x86 与 x64 双向传输。游戏回归见 [PERFORMANCE-REGRESSION.md](PERFORMANCE-REGRESSION.md)。
