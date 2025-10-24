



```sh
# 启动
systemctl start mongod
# 关闭
systemctl stop mongod
```



## MongoDB Python 使用

#### 查找 find()

```python
self.client = MongoClient(connection_string)
self.db = self.client[db_name]
self.users = self.db['users']

# MongoDB 的 find() 方法返回的是一个游标，它是一个可迭代对象，但通常只能迭代一遍；
users_data = self.users.find()

# 一般操作
result = []
for user for users_data:
    user['_id'] = str(user['str'])
    resulr.append(user)
# 或者
users_data = [user for user in users_data]
for user for users_data:
    user['_id'] = str(user['str'])

# users_data将会变为空对象
for user in users_data:
    user['_id'] = str(user['_id'])
```

#### ObjectId 类型

MongoDB 中文档必须有 "_id" 键，默认为ObjectId对象；

ObjectId 是一个12字节 BSON 类型数据，有以下格式：

- 前4个字节表示时间戳
- 接下来的3个字节是机器标识码
- 紧接的两个字节由进程id组成（PID）
- 最后三个字节是随机数。

在查找数据和获取数据时一般需和**`String`进行转换**

```python
# 操作前转换，否则MongoDB无法识别类型
id = "000000000000000000000000"
users_data = self.users.find({'_id': ObjectId(id)})

# 获取数据时转换，部分组件框架不兼容ObjectId
result = []
for user for users_data:
    user['_id'] = str(user['str'])
    resulr.append(user)
    
# 不转换可能的问题
# FastAPI 默认使用 jsonable_encoder 来将 Python 对象转换为 JSON 兼容的格式，但 ObjectId 对象本身不是 JSON 兼容的。
```

