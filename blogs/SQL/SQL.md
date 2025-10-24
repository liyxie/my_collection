### 修改属性的部分内容

```sql
表 b_article ，把内容包括 liy1900.xyz 替换 liy1900.top，更新字段包括：article、content、content_md
SELECT 
    REPLACE(article, 'liy1900.xyz', 'liy1900.top') AS new_article,
    REPLACE(content, 'liy1900.xyz', 'liy1900.top') AS new_content,
    REPLACE(content_md, 'liy1900.xyz', 'liy1900.top') AS new_content_md
FROM b_article
WHERE article LIKE '%liy1900.xyz%' 
   OR content LIKE '%liy1900.xyz%' 
   OR content_md LIKE '%liy1900.xyz%';

```

