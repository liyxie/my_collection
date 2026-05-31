

## mysql索引



### 最左匹配原则

联合索引是由多个字段组成的索引，最左匹配原则要求查询条件必须从索引的最左字段开始连续匹配，才能命中索引。



```sql
-- 创建索引
CREATE INDEX index_col ON accounts (col_a, col_b, col_c);
```

在索引字段上使用函数（如 *LEFT()*，**发生了隐式类型转换**）会导致索引失效。

范围条件（如 *>*、*<*）会中断索引匹配，后续字段无法使用索引。

```sql
-- ✅ 情况1：使用索引 (col_a)
EXPLAIN SELECT * FROM test_leftmost WHERE col_a = 'A';
-- ✅ 情况2：使用索引 (col_a, col_b)
EXPLAIN SELECT * FROM test_leftmost WHERE col_a = 'A' AND col_b = '1';
-- ✅ 情况3：使用索引 (col_a, col_b, col_c)
EXPLAIN SELECT * FROM test_leftmost WHERE col_a = 'A' AND col_b = '1' AND col_c = 'X';
-- ❌ 情况4：不使用索引 (跳过 col_a)
EXPLAIN SELECT * FROM test_leftmost WHERE col_b = '1';
-- ❌ 情况5：不使用索引 (跳过 col_a)
EXPLAIN SELECT * FROM test_leftmost WHERE col_b = '1' AND col_c = 'X';
-- ❌ 情况6：不使用索引 (跳过 col_a)
EXPLAIN SELECT * FROM test_leftmost WHERE col_c = 'X';
-- ✅ 情况7：使用索引 (范围查询仍可使用 col_a)
EXPLAIN SELECT * FROM test_leftmost WHERE col_a > 'A';
-- ⚠️ 情况8：使用索引 (col_a, col_b)，col_c 范围查询后断链
EXPLAIN SELECT * FROM test_leftmost WHERE col_a = 'A' AND col_b > '1' AND col_c = 'X';
```

###  不走索引原因

#### **发生了隐式类型转换（最常见的原因）**

sql语句条件为数字，数据库里存的是字符串，MySQL 会将字段隐式转换为数字再进行比较。**对索引字段做任何函数操作或类型转换，都会导致索引失效**，从而变成全表扫描（ALL）

#### **优化器认为“全表扫描”比“走索引+回表”更快**

使用是 `SELECT *`，这意味着 MySQL 即使命中了辅助索引（联合索引），还需要拿着主键 ID 回到聚簇索引去查其他的列（**回表**）。 如果条件在数据库中匹配了大量的数据（例如占了全表的 20% 以上），MySQL 的基于成本的优化器（CBO）会计算得出：走索引产生大量随机 I/O 回表，还不如直接全表扫描（顺序 I/O）来得快。

### 注意

```
联合索引遇到范围查询（>、<）时，停止匹配，范围查询可以用索引，但后面的查询字段无法用索引。但是对于 >=、<=、BETWEEN、like 前缀匹配，并不会停止匹配
```

1. **`>` 和 `<` （开区间）：** 连边界都无法精确确定，所以后面的字段连在“确定边界”这一步都帮不上忙，直接停止匹配。`key_len` 很短。
2. **`>=`、`<=`、`BETWEEN` （闭区间）：** 因为包含了等于（`=`）的语义，在**等于那个边界值**的局部范围内，后面的字段是有序的。优化器可以利用后面的字段把“扫描起点”或“扫描终点”卡得更准，从而减少扫描范围。所以在 `EXPLAIN` 中，后面的字段被算进了 `key_len`。
3. **`LIKE 'prefix%'`：** 本质上会被优化器转化为 `>= 'prefix' AND < 'prefiy'`，它同样包含了 `>=` 的明确左边界，所以行为与 `>=` 类似。

```sql
CREATE INDEX index_id on daily (account_id, NYID, remaining)

explain
SELECT d.account_id from daily d  where d.account_id > 10 and d.NYID = '2566813'
-- 1	SIMPLE	d		range	index_id	index_id	4		1231	10.0	Using where; Using index
-- 在确定“扫描起始点”时，只用到了 account_id，所以 key_len = 4
explain
SELECT d.account_id from daily d  where d.account_id >= 10 and d.NYID = '2566813'
-- 1	SIMPLE	d		range	index_id	index_id	406		1234	10.0	Using where; Using index
-- 尽管在后续扫描 11、12 时 NYID 无法用于索引查找，但在决定“从哪里开始扫描（确定下边界）”时，account_id 和 NYID 都参与了 B+ 树的快速路由。因此，key_len = 4 + 402 = 406。
```



### 索引下推

#### 现在的 MySQL 为什么看起来“都用到了索引”？

在 MySQL 5.6 引入了**索引下推（Index Condition Pushdown, ICP）**之后，对于 `a = 1 AND b > 2 AND c = 3`：

- 虽然 `c = 3` 无法用于 B+ 树的查找路由（也就是通常说的无法走索引）；
- 但是 MySQL **不会**把 `c=3` 丢给 Server 层去过滤。存储引擎在遍历联合索引时，会顺便把 `c = 3` 的条件在索引树上直接判断掉，不符合的就不回表了。
- 这时候在 `EXPLAIN` 里看，`Extra` 字段会显示 `Using index condition`。很多人据此认为“后面的字段也走了索引”，其实它只是做了索引层的过滤，并没有用到 B+ 树的快速查找特性。

### 核心逻辑

联合索引的本质是**多字段排序**。只要前面的字段确定是一个**确定的值**（`=` 或 `IN`），后面的字段在局部就是有序的，就能走 B+ 树查找；一旦前面的字段是一个**范围**，后面的字段就失去了全局或局部的有序性，就只能用来做遍历时的过滤（索引下推），而不能用于快速树搜索。