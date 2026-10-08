# 测试与日志

先单机测试菜单、进入地图、选择单位、滚屏、存读档和退出，再对比同地图、同 mod 版本、相同选项的联机结果。保留无桥接基线。

没有 Host：确认 D3D9 后端、根目录桥接 d3d9.dll、.yrbridge 完整、游戏进程名匹配及管理员启动。MO 客户端保存设置后重新检查 renderer。不要独立运行 Host。

黑屏或设备创建失败：检查 bridge32.log、bridge64.log 和 YRBridge64_d3d9.log。正式版使用固定 GPLALL 2.6.8-2，源码 Nightly 使用构建时锁定的 GPLALL 源码；以包内 BACKEND.json 和 dependencies.json 为准，需要与该后端相容的 Vulkan GPU/驱动。

联机报错：记录错误原文、地图、双方游戏/mod版本、是否单机也发生，并保留 SYNC*.TXT（若生成）、except_ih.txt、debug 日志和 Bridge 日志。无需把隐私信息或整套游戏上传为公开 issue。不要通过 disableTimeouts=True 掩盖问题。

包内不附带 ReShade。完整适配补丁保留上游已有能力，常规配置关闭开发实验选项。若你已有其他 d3d9.dll 注入组件，请先备份并分别测试，避免覆盖后误判。

Steam 覆盖层：此前本机的启动闪退在停用 Bridge 后也出现，用户报告重启电脑后覆盖层与 Bridge 均正常。尚未确认具体根因。再次出现时应记录当前版本和日志，分别测试覆盖层开关，不能直接认定是桥接不兼容。

下载校验不匹配：不要混用不同构建的 ZIP 和 SHA256。重新下载同一 Release 的一对附件并校验；强制重建时 Release 会暂时处于草稿状态，核验完整后才公开。
