# 运行维护、分支清理与性能预算

## 安全清理

`python scripts/maintenance/repo_housekeeping.py`默认只预览；`--apply`执行策略允许的删除。只维护invoidstar/VLA-Radar。仓库最新main必须有已成功Pages deploy，已合并PR的merge commit也必须在该main历史中。当前分支HEAD须等于该PR合并时HEAD；squash合并亦可据此验证，不依赖`git branch --merged`误判。

保留main/master/develop/gh-pages、pre-update-safety、backup/archive/keep前缀、protected分支、open PR引用的head/base和所有未合并工作。其余managedPrefixes内分支只有在合并6小时后才可删除，每次最多10个。仅因为30天未更新不代表代码无价值，未合并旧分支只能报告。每次删除前重新获取PR和branch，用精确SHA lease完成原子条件删除；branch有并发更新则拒绝。这个条件删除不是强制推送新历史的授权。

`housekeeping.yml`每周日09:20（Asia/Singapore，UTC 01:20）检查，在main成功发布后也检查；同一并发组避免重叠。主任务应查看其审计结果，不再写一份不安全的按年龄删分支逻辑。即使本周没有新论文也会清理。报告保存原SHA、PR和保留理由，Actions artifact保留30天。不把读报告等同于实际删除成功。

## main保护

目标：必须PR、必须最新base的validate检查、禁止force-update和删除main、管理员同样遵守；required approving reviews=0以配合已授权助手自检，而不是冒充另一人批准。`maintenance/policies/main-protection.json`为待安装配置。

配置端点需Administration(write)。`python scripts/maintenance/configure_main_protection.py --apply`仅在确认main未保护时安装，遇403停止；已有保护只读、不覆盖。审计/候选配置不等于远端已启用。未取得管理权限时，普通CI与PR流程继续，但不能声称GitHub已强制执行保护。

## 发表状态

API按精确ID、明确Accept访问；406或一般服务异常时用同一官方站点的公开摘要页回退，从Submission history中分别解析v1和最高版本时间。没有明确v1、ID不符、明显标题差异或未来日期则拒绝。403/429不切换端点规避。请求间隔3.1秒、连续3次摘要失败熔断，默认每次最多100篇到期记录、7天轮转。期刊/会议录用仍需一手证据，文章存在不等于已录用。

API失效而回退成功计入明确provider；剩余失败或未到期不混为全库已检查。new version只标needs_review，不升级阅读日期；firstPublished锁不改。来源健康最多100项/180秒，实际剩余明确记录。官方说明：https://info.arxiv.org/help/api/user-manual.html

## 规模与速度

完整源记录不删减。首次打开只下载紧凑library目录；首次检索才读search-index，在Worker中计算，失败用相同算法协作式回退。笔记和榜单结果使用内容哈希路径，分别只读当前论文或赛道。兼容导出仍保留，但不作为默认页面数据。

JSON缓存40项、查询结果32项；失败缓存清理，15秒请求超时。卡片12条/页、榜单20条/页，时间线分批加载。性能CI检查每篇bootstrap预算、内容哈希文件存在、协议隔离，并测临时1000/5000/10000条数据。代码执行测量不是实际移动设备或CDN速度保证。

若将来轻量目录本身超过约2MB gzip或真实设备交互明显变慢，再将首页目录按年份/分页构建并做分片检索；不以固定篇数过早引入服务器。图表只在相应视图加载，保留表格/无动画模式，原图许可不明时提供来源链接而非复制大图。
