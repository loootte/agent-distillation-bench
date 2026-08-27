# RFC-0001：从 Agent 轨迹编译可验证的确定性程序

- Status: Accepted (v0)
- Issue: [#1](https://github.com/loootte/agent-distillation-bench/issues/1)
- Date: 2026-08-27

## 1. 定位

传统硬编码软件把边界收在设计期：输入规则固定、场景可枚举，稳定性和效率来自不再推理。
Agent 的优势是探索和归纳，不是把同一条路径推理第一千遍。

本仓库不把 Agent 当作生产路径的默认执行器，而当作：

1. **探索器**：在尚未硬化的任务上试错，收集成功 / 失败轨迹。
2. **编译器**：把高重复、已验证的过程沉淀为可执行程序。
3. **守卫失败时的回退**：编译产物与现实不一致时，把控制权交回 Agent，并触发再编译。

一句话：**Agent 出现在编译期与偏移期；执行面尽量是普通软件。**

## 2. 问题形式化

给定任务族 \(\mathcal{T}\) 与轨迹集 \(\{\tau_i\}\)（含成功 / 失败、工具调用、环境观测）：

| 阶段 | 定义 |
|---|---|
| **编译** | 产出确定性工件 \(P\)。v0 入库形态是带参数的 Python 函数；可选附带显式状态机 IR（状态 = 观测谓词，迁移 = 动作）。不是只写 SKILL.md。 |
| **验证** | 在干净环境重放 \(P\)，由**独立 checker** 判定任务是否完成。覆盖率（步骤走完）≠ 完成。 |
| **复用** | 后续同类任务优先执行 \(P\)，逐步零（或接近零）LLM。 |
| **交回** | 守卫失败（观测与 \(P\) 预期不符）时交回 Agent，并记录一次再编译候选。 |

评测至少包含，不只报一次成功率：

| 指标 | 含义 |
|---|---|
| 冷启动成本 | 第一次探索 + 编译 + 验证 |
| 热启动延迟 / 费用 | 命中 \(P\) 后的执行 |
| 编译保真率 | 能重放 **且** 任务真正完成的比例 |
| 守卫触发率 | 复用时交回 Agent 的比例 |
| 微扰衰减 | UI / API / 数据轻微变化后 \(P\) 是否仍成立 |

## 3. 架构

```
Explore  →  Compile  →  Verify-before-store  →  Replay
                                              ↘ guard miss → Fallback → Explore
```

- **Explore**：产生 JSONL 轨迹。v0 用录制轨迹 / 人工记录，不接真实 LLM。
- **Compile**：输入 ≥N 条同任务族成功轨迹，输出 `Program`。
- **Verify-before-store**：干净环境重跑 \(P\)；独立 checker 通过才写入 artifact store。不通过则拒绝入库并保留反例。
- **Replay**：`if store.hit(task) and guards_ok: run(P) else: run(agent_stub)`。
- **Fallback**：v0 的 `agent_stub` 重放已有成功轨迹，或标记人工记录。

## 4. v0 拍板

本 RFC 锁定 issue #1 里待拍板的三项，后续 issue 不得静默扩大范围。

### 4.1 玩具域：进程内工单 API

选择 **带固定 API 的工单状态流转**（in-process mock，无网络、无 GUI）。

理由：状态完全可观测；成功可自动判定（`status == closed` 且存在决议评论）；任务可重复；天然对应「步骤走完但任务失败」的假程序（只评论不关单）。

路径：`examples/toy_domain/`。

### 4.2 编译目标：Python 函数入库，状态机作 IR

- **入库 / 运行时执行体**：参数化 Python 函数（`run(api, **params)`）。
- **可选 IR**：显式状态机 JSON（states / transitions / guards），便于后续对照 PreAct 式谓词守卫。
- v0 **不**发明独立 DSL；不把自然语言 SOP 当作可执行产物。

### 4.3 不接真实 LLM

v0 用录制轨迹打通 Explore → Compile → Verify → Replay → Fallback。
`agent_stub` = 重放已有成功轨迹。真实 LLM 编译器留给后续 issue。

## 5. v0 范围

只做一条竖切：

1. **轨迹格式**：JSONL，见 `schema/trace.schema.json`。必填：`task_id`、`step`、`observation`、`action`、`tool`、`args`、`success`。
2. **编译器 MVP**：接口 + 轨迹线性化参考实现（把成功 episode 的 tool 序列参数化成 Python）。
3. **Verify-before-store**：干净环境重跑；独立 checker 通过才 `store.put`。
4. **运行时调度**：命中且守卫通过则 `run(P)`，否则 `agent_stub`。
5. **一个玩具域**：至少一个任务、若干轨迹、一个期望编译产物、一个应被门拒绝的反例。

## 6. 非目标（v0 明确不做）

- 把 Agent 做成传统软件的通用 `except` 实现
- 只沉淀自然语言 SOP / SKILL.md 而不产出可执行代码
- 开放世界、一次性创意任务
- 多仓库技能市场、跨模型蒸馏、GUI Computer-Use
- 运行时自愈、工作流搜索、多 Agent 编排

## 7. 相关工作

| 工作 | 与本仓库的关系 |
|---|---|
| [PreAct](https://arxiv.org/abs/2606.17929) | 轨迹 → 状态机；replay 前检查观测；**verify-before-store** 拒绝「步骤走完但任务未完成」的假程序。本仓库把该门做成 v0 硬约束。 |
| [Skill-DisCo](https://arxiv.org/abs/2606.26669) | 轨迹 → 可执行、可验证的参数化过程子图，而不是自然语言 skill。 |
| [Compiled AI](https://arxiv.org/abs/2604.05150) / [PlanCompiler](https://arxiv.org/abs/2604.13092) | 编译期用模型，运行期确定性代码；LLM 不在默认执行面。 |
| [Trace2Policy](https://arxiv.org/abs/2606.10457) | 规则编译成零 LLM Python；执行形态本身带来收益。 |

## 8. 工程验收

- [x] `README.md`：问题、架构图、引用
- [x] 本 RFC
- [x] `schema/trace.schema.json`
- [x] `src/compile/`、`src/verify/`、`src/store/`、`src/runtime/` 模块 + 接口
- [x] `examples/toy_domain/`：1 个任务、若干轨迹、1 个期望编译产物
- [x] 测试：验证门拒绝「步骤走完但任务失败」的假程序

## 9. 后续 issue

- `#2` 轨迹 schema 与采集约定（本 RFC 只锁最小字段）
- `#3` 编译器 MVP（跨轨迹对齐、参数绑定，而不仅线性化一条 episode）
- `#4` verify-before-store 的环境重置契约与反例库
- `#5` 运行时守卫与交回
- `#6` 评测脚本与五项指标
