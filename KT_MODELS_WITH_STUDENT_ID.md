# pykt-toolkit中使用Student ID/特征的KT模型

## 🔍 搜索结果总结

在pykt-toolkit中，**只有极少数模型**使用与学生相关的特征作为输入。

---

## ✅ 使用学生特征的模型

### 1. **DIMKT** (Difficulty-aware Interaction-aware Multi-dimensional Knowledge Tracing)

**模型文件**: `pykt/models/dimkt.py`

**Forward方法签名**:
```python
def forward(self, q, c, sd, qd, a, qshft, cshft, sdshft, qdshft):
```

**输入参数**:
- `q`: 问题ID (question id)
- `c`: 概念/知识点ID (concept id)
- `sd`: **学生难度水平** (student difficulty level)
- `qd`: 问题难度水平 (question difficulty level)
- `a`: 答题结果 (answer)
- `*shft`: 对应的shift版本（下一个时刻）

**说明**:
- `sd` (sdseqs) 是学生难度等级的序列，表示学生的能力水平
- `qd` (qdseqs) 是问题难度等级的序列
- DIMKT同时考虑学生能力和问题难度的多维度交互

**特点**:
- ✅ **明确使用student difficulty作为输入特征**
- 模型架构中有专门的embedding层: `self.sd_emb = Embedding(self.difficult_levels+2, self.emb_size, padding_idx=0)`
- 在训练时需要提供`sdseqs`和`qdseqs`字段

**训练代码片段** (来自`train_model.py`):
```python
if model_name in ["dimkt"]:
    q, c, r, t, sd, qd = dcur["qseqs"], dcur["cseqs"], dcur["rseqs"], dcur["tseqs"], dcur["sdseqs"], dcur["qdseqs"]
    qshft, cshft, rshft, tshft, sdshft, qdshft = dcur["shft_qseqs"], dcur["shft_cseqs"], dcur["shft_rseqs"], dcur["shft_tseqs"], dcur["shft_sdseqs"], dcur["shft_qdseqs"]
```

---

## ❌ 不使用学生ID的模型（其他所有模型）

以下模型**不使用**student_id或student-specific特征作为输入：

### 核心KT模型
- **DKT** (Deep Knowledge Tracing)
- **DKT+** (DKT Plus)
- **DKT-Forget** (带遗忘机制的DKT)
- **DKVMN** (Dynamic Key-Value Memory Network)
- **SKVMN** (Sequential Key-Value Memory Network)

### IRT相关模型
- **Deep-IRT** (Deep Item Response Theory)
  - 注意：虽然模型内部计算student ability，但这是从答题序列**推断**出来的
  - **不是作为输入提供的**

### 注意力机制模型
- **AKT** (Attentive Knowledge Tracing)
- **SAKT** (Self-Attentive Knowledge Tracing)
- **SAINT** (Separated Self-Attentive Neural Knowledge Tracing)
- **SAINT++**
- **simpleKT**
- **sparseKT**
- **stableKT**

### 图神经网络模型
- **GKT** (Graph-based Knowledge Tracing)
- **HCGKT** (Heterogeneous Cooperative Graph KT)
- **RKT** (Relational Knowledge Tracing)

### Transformer相关模型
- **ATKT** (Adversarially Trained Knowledge Tracing)
- **ATDKT**
- **promptKT**

### 其他模型
- **LPKT** (Learning Process-consistent Knowledge Tracing)
- **KQN** (Knowledge Query Network)
- **UKT** (Uncertainty-aware Knowledge Tracing)
- **ReKT** (Relation-aware Knowledge Tracing)
- **QIKT** (Question-aware Interaction KT)
- **QDKT** (Question Difficulty KT)
- **RobustKT**
- **ExtraKT**
- **FoliBiKT**
- **CSKT**
- **DataKT**
- **IEKT**
- **Hawkes**
- **LEFOKT-AKT**

---

## 🔬 Deep-IRT的特殊情况

**模型**: Deep-IRT

**为什么不算使用student ID?**

查看代码 (`pykt/models/deep_irt.py`):
```python
def forward(self, q, r, qtest=False):
    # ... 处理过程 ...
    
    # 这些是从答题序列计算出来的，不是输入
    stu_ability = self.ability_layer(self.dropout_layer(f))  # equation 12
    que_diff = self.diff_layer(self.dropout_layer(k))        # equation 13
    
    p = torch.sigmoid(3.0*stu_ability - que_diff)             # equation 14
```

**关键区别**:
- ❌ **不是输入**: student ability不是forward的参数
- ✅ **是输出**: 从答题历史序列中动态计算出来的
- 原理类似IRT理论，但是通过神经网络从数据中学习

---

## 📊 模型对比表

| 模型 | 使用Student ID/特征 | 输入类型 | 备注 |
|------|-------------------|---------|------|
| **DIMKT** | ✅ 是 | `sd` (student difficulty level) | 唯一明确使用学生特征的模型 |
| **Deep-IRT** | ❌ 否 | 无student输入 | 内部计算ability，但不作为输入 |
| **LPKT** | ❌ 否 | `q`, `r`, `it` | 学习过程建模，不需要student ID |
| **DKT系列** | ❌ 否 | `q`, `r` | 最基础的KT模型 |
| **AKT系列** | ❌ 否 | `q`, `r`, `pid` | 使用注意力机制 |
| **GKT** | ❌ 否 | `q`, `r` | 使用图结构 |
| **其他所有模型** | ❌ 否 | 问题序列 + 答题结果 | 标准KT范式 |

---

## 💡 为什么大多数KT模型不使用Student ID？

### 1. **知识追踪的核心假设**
知识追踪关注的是"学习过程"而不是"学习者身份"：
```
传统方法: 学生特征 → 预测能力
知识追踪: 答题历史 → 知识状态 → 预测概率
```

### 2. **泛化能力**
- 不依赖学生ID，可以应用到任何新学生
- 冷启动问题：新学生也能获得预测

### 3. **隐私保护**
- 不需要收集学生的个人特征信息
- 只需要答题交互数据

### 4. **动态建模**
- 知识状态随时间变化
- 比静态的"学生能力"更灵活

---

## 🎯 DIMKT为什么特殊？

DIMKT是pykt-toolkit中**唯一**明确使用学生难度特征的模型：

### 设计理念
1. **多维度交互**: 同时考虑学生能力和题目难度
2. **显式建模**: 直接输入学生难度等级，而不是推断
3. **个性化**: 不同能力水平的学生有不同的学习模式

### 数据要求
使用DIMKT需要在数据预处理时提供：
- `sdseqs`: 学生难度等级序列
- `qdseqs`: 问题难度等级序列

这些通常需要额外的标注或计算。

---

## 📝 结论

在pykt-toolkit的**40+个KT模型**中：

| 统计 | 数量 |
|------|------|
| 使用student ID/特征 | **1个** (DIMKT) |
| 不使用student ID/特征 | **39+个** |

**主流KT模型遵循的范式**:
```
输入: 问题序列 + 答题结果 (+ 可选时间信息)
输出: 答对概率

不需要: student_id, student_ability, student_profile
```

这是知识追踪领域的**标准做法**，强调的是**学习轨迹建模**而非**学习者画像**。

---

## 🔍 如何确认其他模型

如果想验证某个模型是否使用student ID，查看其`forward`方法：

```python
# 例如 LPKT
def forward(self, e_data, a_data, it_data=None, at_data=None, qtest=False):
    # 参数中没有student_id或student相关的

# 例如 DKT
def forward(self, c, r):
    # 只有concept和response

# 例如 DIMKT (唯一例外)
def forward(self, q, c, sd, qd, a, qshft, cshft, sdshft, qdshft):
    # 有sd (student difficulty)！
```

---

**更新时间**: 2025-10-19
**统计范围**: pykt-toolkit所有模型

