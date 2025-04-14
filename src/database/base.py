import sqlite3
from abc import ABC, abstractmethod

class BaseDatabase(ABC):
    """数据库基类"""
    def __init__(self, db_name='xhs.db'):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    @abstractmethod
    def create_table(self):
        """创建表，子类必须实现"""
        pass

    def execute(self, query, params=None):
        """执行SQL查询"""
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self.cursor

    def commit(self):
        """提交事务"""
        self.connection.commit()

    def close(self):
        """关闭数据库连接"""
        self.connection.close()

    def fetch_one(self, query, params=None):
        """执行查询并返回一条记录"""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query, params=None):
        """执行查询并返回所有记录"""
        cursor = self.execute(query, params)
        return cursor.fetchall()