import re
from typing import List, Tuple

class SQLSafetyChecker:
    """SQL安全检查器"""
    
    # 允许的SQL操作(白名单)
    ALLOWED_OPERATIONS = {'SELECT'}
    
    # 危险关键字(黑名单)
    DANGEROUS_KEYWORDS = {
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
        'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC'
    }
    
    @classmethod
    def check(cls, sql: str) -> Tuple[bool, str]:
        """
        检查SQL是否安全
        返回: (是否安全, 错误信息)
        """
        sql_upper = sql.upper().strip()
        
        # 1. 检查是否以允许的操作开头
        operation = sql_upper.split()[0]
        if operation not in cls.ALLOWED_OPERATIONS:
            return False, f"不允许的操作:{operation}"
        
        # 2. 检查危险关键字
        for keyword in cls.DANGEROUS_KEYWORDS:
            if re.search(rf'\b{keyword}\b', sql_upper):
                return False, f"包含危险关键字:{keyword}"
        
        # 3. 检查注释注入(--或#)
        if '--' in sql or '#' in sql:
            return False, "不允许使用SQL注释"
        
        # 4. 检查多语句(;)
        if sql.count(';') > 1:
            return False, "不允许执行多条SQL语句"
        
        return True, "安全检查通过"

# 使用示例
safe_sql = "SELECT * FROM orders WHERE status = 'completed'"
is_safe, msg = SQLSafetyChecker.check(safe_sql)
print(f"✅ {msg}")  # 安全检查通过

unsafe_sql = "SELECT * FROM users; DROP TABLE users;"
is_safe, msg = SQLSafetyChecker.check(unsafe_sql)
print(f"❌ {msg}")  # 不允许执行多条SQL语句