c00f2cc70bbf40ab80884de8680a05bf

![image-20250807181259960](E:\MyWenJian\my_collection\temp.assets\image-20250807181259960.png)

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量导入SSE接口简单测试
快速测试批量导入功能
"""

import requests
import json
import pandas as pd
from pathlib import Path

# 配置
BASE_URL = "http://localhost:8000"
DATABASE_ID = "test_user_123"


def create_simple_test_files():
    """创建简单的测试文件"""
    test_dir = Path("test_data_simple")
    test_dir.mkdir(exist_ok=True)
    
    # 创建3个小文件用于快速测试
    
    # 文件1: 用户数据
    users = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['张三', '李四', '王五'],
        'age': [25, 30, 28]
    })
    users.to_csv(test_dir / 'test1_users.csv', index=False, encoding='utf-8-sig')
    
    # 文件2: 产品数据
    products = pd.DataFrame({
        'pid': [101, 102],
        'pname': ['产品A', '产品B'],
        'price': [99.9, 199.9]
    })
    products.to_csv(test_dir / 'test2_products.csv', index=False, encoding='utf-8-sig')
    
    # 文件3: 订单数据
    orders = pd.DataFrame({
        'order_id': [1001, 1002, 1003],
        'user_id': [1, 2, 1],
        'product_id': [101, 102, 101],
        'quantity': [1, 2, 3]
    })
    orders.to_excel(test_dir / 'test3_orders.xlsx', index=False)
    
    print(f"✓ 测试文件已创建在 {test_dir} 目录")
    return test_dir


def test_batch_import_with_requests():
    """使用requests库测试SSE接口（同步版本）"""
    print("\n=== 使用requests测试批量导入 ===\n")
    
    test_dir = create_simple_test_files()
    
    # 准备文件
    files = [
        ('files', ('test1_users.csv', open(test_dir / 'test1_users.csv', 'rb'), 'text/csv')),
        ('files', ('test2_products.csv', open(test_dir / 'test2_products.csv', 'rb'), 'text/csv')),
        ('files', ('test3_orders.xlsx', open(test_dir / 'test3_orders.xlsx', 'rb'), 
                   'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    ]
    
    data = {
        'db_name': 'simple_test.db',
        'force_overwrite': 'true'
    }
    
    headers = {
        'Database-ID': DATABASE_ID
    }
    
    try:
        # 发送请求（使用stream=True来接收SSE）
        response = requests.post(
            f"{BASE_URL}/database/permanent/import/batch",
            files=files,
            data=data,
            headers=headers,
            stream=True
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            return
        
        # 处理SSE流
        print("接收事件流:")
        print("-" * 50)
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                
                # 解析SSE事件
                if line_str.startswith('event:'):
                    event_type = line_str.split(':', 1)[1].strip()
                    print(f"\n[事件] {event_type}")
                
                elif line_str.startswith('data:'):
                    try:
                        data_str = line_str.split(':', 1)[1].strip()
                        data = json.loads(data_str)
                        
                        # 格式化输出
                        if 'progress' in data:
                            print(f"  进度: {data['progress']}%")
                        if 'message' in data:
                            print(f"  消息: {data['message']}")
                        if 'filename' in data:
                            print(f"  文件: {data['filename']}")
                        if 'table_name' in data:
                            print(f"  表名: {data['table_name']}")
                        if 'rows_imported' in data:
                            print(f"  导入行数: {data['rows_imported']}")
                        if 'results' in data:
                            results = data['results']
                            print(f"  === 最终结果 ===")
                            print(f"  成功: {results['successful_imports']}")
                            print(f"  失败: {results['failed_imports']}")
                            print(f"  跳过: {results['skipped_imports']}")
                            print(f"  汇总: {results['summary']}")
                            
                    except json.JSONDecodeError:
                        pass
        
        print("\n" + "=" * 50)
        print("测试完成!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求错误: {e}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        # 关闭文件
        for _, file_tuple in files:
            file_tuple[1].close()


def test_error_scenarios():
    """测试错误场景"""
    print("\n=== 测试错误场景 ===\n")
    
    # 场景1: 不支持的文件类型
    print("1. 测试不支持的文件类型:")
    try:
        # 创建一个txt文件
        test_dir = Path("test_data_simple")
        test_dir.mkdir(exist_ok=True)
        
        txt_file = test_dir / "invalid.txt"
        txt_file.write_text("这是一个文本文件")
        
        files = [
            ('files', ('invalid.txt', open(txt_file, 'rb'), 'text/plain'))
        ]
        
        response = requests.post(
            f"{BASE_URL}/database/permanent/import/batch",
            files=files,
            data={'db_name': 'test.db', 'force_overwrite': 'true'},
            headers={'Database-ID': DATABASE_ID},
            stream=True
        )
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if 'error' in line_str or 'failed' in line_str:
                    print(f"  ✓ 正确拒绝了不支持的文件类型")
                    if line_str.startswith('data:'):
                        data = json.loads(line_str.split(':', 1)[1].strip())
                        if 'message' in data:
                            print(f"    错误信息: {data['message']}")
                    break
        
        files[0][1][1].close()
        
    except Exception as e:
        print(f"  测试出错: {e}")
    
    # 场景2: 表名数量不匹配
    print("\n2. 测试表名数量不匹配:")
    try:
        test_dir = Path("test_data_simple")
        files = [
            ('files', ('test1_users.csv', open(test_dir / 'test1_users.csv', 'rb'), 'text/csv')),
            ('files', ('test2_products.csv', open(test_dir / 'test2_products.csv', 'rb'), 'text/csv'))
        ]
        
        response = requests.post(
            f"{BASE_URL}/database/permanent/import/batch",
            files=files,
            data={
                'db_name': 'test.db',
                'table_names': 'table1',  # 只提供1个表名，但有2个文件
                'force_overwrite': 'true'
            },
            headers={'Database-ID': DATABASE_ID},
            stream=True
        )
        
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if 'error' in line_str:
                    print(f"  ✓ 正确检测到表名数量不匹配")
                    if line_str.startswith('data:'):
                        try:
                            data = json.loads(line_str.split(':', 1)[1].strip())
                            if 'error' in data:
                                print(f"    错误信息: {data['error']}")
                        except:
                            pass
                    break
        
        for _, file_tuple in files:
            file_tuple[1].close()
        
    except Exception as e:
        print(f"  测试出错: {e}")
    
    print("\n错误场景测试完成")


if __name__ == "__main__":
    print("=" * 60)
    print("批量导入SSE接口简单测试")
    print("=" * 60)
    
    # 主测试
    test_batch_import_with_requests()
    
    # 错误场景测试
    test_error_scenarios()
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("=" * 60)
```

