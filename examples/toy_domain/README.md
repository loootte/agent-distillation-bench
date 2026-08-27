# Toy domain: in-process ticket API

RFC-0001 锁定的 v0 竖切。无网络、无 GUI。成功条件可自动判定。

## 任务 `close_ticket`

初始：工单存在，`status=open`，无评论。

成功：`status=closed`，且至少一条评论包含 `resolution`。

## 文件

| 文件 | 作用 |
|---|---|
| `tickets.py` | 固定工单 API |
| `traces.jsonl` | 三条成功轨迹（路径略有不同） |
| `expected/close_ticket.py` | 期望编译产物 |
| `counterexamples/comment_without_close.py` | 步骤走完但任务失败，验证门必须拒绝 |

## 假程序

`comment_without_close.py` 只写评论，不关单。工具调用全部成功（replay 覆盖率 100%），独立 checker 失败。这就是 PreAct 说的 *runs but doesn’t work*。
