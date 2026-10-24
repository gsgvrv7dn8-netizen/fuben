# GitHub 私有协作与账号核验

已创建并核验个人私有仓库[echo1229/mathorcup-2026-track-a](https://github.com/echo1229/mathorcup-2026-track-a)。Owner为echo1229；总控标准GitHub连接及CLI操作身份均已核验为echo1229。刘源Forever-lyy1012、谢小鱼gsgvrv7dn8-netizen的write权限邀请均已发送。每位队员使用自己的授权账号协作，不共享队长账号。

## 谁能看到

- 普通个人账号的私人仓库：加入公司组织不会自动把该个人仓库权限授予公司组织管理员。访问取决于仓库自身授权。
- 公司组织名下的私有仓库：组织Owner对组织全部仓库有管理权限；普通成员权限取决于基础权限、团队和直接授权等。
- 企业统一创建的Enterprise Managed Users账号：存在企业Owner临时访问用户仓库的例外，不能当普通个人账号处理。
- 三人协作可以用个人Private仓库邀请两名队友；GitHub Free足够。人类协作者可限定为三人，但已授权Apps等也要纳入访问范围，不能承诺绝对只有三人接触。

官方来源：[仓库归属与可见性](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories)、[组织角色](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization)、[企业托管账号访问例外](https://docs.github.com/en/enterprise-cloud%40latest/admin/managing-accounts-and-repositories/managing-repositories-in-your-enterprise/accessing-user-owned-repositories-in-your-enterprise)、[邀请个人仓库协作者](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/repository-access-and-collaboration/inviting-collaborators-to-a-personal-repository)。核查日期2026-10-24。

## 建库前提与步骤

1. 总控建库及上传使用已核验的echo1229身份；队员后续提交使用各自获授权的账号。不得只凭显示名称或本机Git作者信息认定账号。
2. 确认账号为普通个人账号后，仓库Owner选择echo1229、Visibility选择Private。
3. 初始上传先审阅文件清单；代码、规范、证据摘要入库，原始数据、下载材料、密钥和本地运行缓存排除。
4. 获得B/C准确GitHub用户名后邀请，确认接受再开展PR协作。
5. 每人独立工作副本与任务分支，main作为整合分支，重要结果由另一成员审查。

## 省去来回传话

B/C按长期任务维护自己的状态与证据，里程碑开PR。总控读取PR和状态文件即可，不需要复制长聊天。B若只用DeepSeek聊天，可自行编辑Markdown/CSV，通过GitHub网页提交文档；不要求DeepSeek自动访问私有仓库。

交付统一走[GitHub交接流程](GITHUB_HANDOFF.md)：B/C提交`[待验收]`PR，总控在同一PR写验收与下一步。A完成回报唤醒总控时，总控同时处理B/C队列；不用用户传话，也不设置定时任务。GitHub事件当前不能直接唤醒本桌面聊天，因此不是即时通知服务。

## 当前连接限制

标准GitHub连接和CLI身份均已核验echo1229，仓库已通过CLI创建。2026-10-24本次标准连接读取仓库返回404，已改用核验echo1229的CLI并确认仓库仍为Private；不能把连接404误报为仓库不存在。另一个“GitHub写入工具”连接身份与用户不符，已停止使用；未在身份不符账号创建仓库或上传项目。后续如连接变化，写入前重新核对。
