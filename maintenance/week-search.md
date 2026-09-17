# 首发周检索与维护

## 日期口径

`firstPublished` 保存已核对的论文首发日期，详情中的 `dateNote` 说明来源。新增关键文献主要使用 arXiv v1 提交日，不把修订日、会议举办日或收录日替代它。存在更早的官方首发来源时，应核对后明确更新口径，而不是只凭年份推算。

`collectionMonth` 继续表示进入文献库的批次；因此一篇 2022 年的论文可以在 2026-09 批次收录。原有 `?month=2026-08` 分享链接仍按收录批次解释。

## ISO 周历

- `2026-W35` 表示 2026-08-24（周一）至 2026-08-30（周日）。
- ISO 第 1 周包含该年的 1 月 4 日。ISO 周历年可能与公历年不同，例如 2021-01-01 属于 2020-W53，2024-12-30 属于 2025-W01。
- 使用 UTC 计算，不受查看者时区或夏令时影响。
- 日期只有 `YYYY-MM` 或缺失时，不设置虚构的日期或周数，放入“日期未精确到日”；只有月份的记录仍可按已知年份查找。
- 周次从日期动态派生，不在 JSON 中重复维护周字段。选择年份时可以选择该年的全部 52 / 53 周；计数为零的周显示空结果，不表示该周全网没有论文。

参考：Python 官方 `datetime.date.isocalendar()`：https://docs.python.org/3/library/datetime.html#datetime.date.isocalendar

## 功能与链接

- 筛选示例：`?year=2026&week=2026-W35`。
- 关键文献检索：`?q=关键文献`。标签表示编辑精选，不是引用量排名。
- 未知周：`?week=undated`；可以进一步限定已知年份。
- 时间线默认按周，也可以切到月份：`?view=timeline&timeline=month`。
- 点击卡片、表格或时间线中的周标签，进入该周所有收录论文。
- CSV 增加首发周、起止日期和日期依据；不导出私人收藏或阅读进度。

## 检查与发布

```bash
python validate.py
python scripts/check_catalog.py
node --check app.js
node --check dates.js
node scripts/test_dates.cjs
node scripts/test_urls.cjs
```

`dates.js` 是新页面依赖，`.github/workflows/site.yml` 必须将它一并放入发布制品。

日期测试逐日对照 1990—2040 年 Python ISO 日历，另覆盖非法日期、跨年、闰日和无精确日期等情况。URL 测试是隔离状态的单元测试，不替代真实线上跳转检查。

浏览器阅读存储键仍为 `vla-radar.reading.v1`，不重编号已有论文。正常文献维护仅更新 `papers.json` 与已有日志，不需要手动计算周次。本次关键文献补充不推进每周全面检索检查点。
