# 测试与日志

先单机测试菜单、进入地图、选择单位、滚屏、存读档和退出，再对比同地图、同 mod 版本、相同选项的联机结果。保留无桥接基线。

没有 Host：确认 D3D9 后端、根目录桥接 d3d9.dll、.l4d2bridge 完整、游戏进程名匹配及管理员启动。MO 客户端保存设置后重新检查 renderer。不要独立运行 Host。

黑屏或设备创建失败：检查 bridge32.log、bridge64.log 和 L4D2Bridge64_d3d9.log。该版本基于官方 DXVK 2.6.1，需要相容的 Vulkan GPU/驱动。

联机报错：记录错误原文、地图、双方游戏/mod版本、是否单机也发生，并保留 SYNC*.TXT（若生成）、except_ih.txt、debug 日志和 Bridge 日志。无需把隐私信息或整套游戏上传为公开 issue。不要通过 disableTimeouts=True 掩盖问题。

本版不附带 ReShade、输入覆盖层或内存读取恢复实验。若你已有其他 d3d9.dll 注入组件，请先备份并分别测试，避免覆盖后误判。
