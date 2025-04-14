from src.database.base import BaseDatabase

class GroupManager(BaseDatabase):
    """群组管理器类"""
    def __init__(self, db_name='xhs.db'):
        super().__init__(db_name)

    def create_table(self):
        """创建群组表"""
        self.execute('''
            CREATE TABLE IF NOT EXISTS group_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                group_name TEXT NOT NULL,
                create_time INTEGER NOT NULL
            )
        ''')
        self.commit()

    def insert_group(self, group_id, group_name, create_time):
        """插入群组信息"""
        self.execute('INSERT INTO group_info (group_id, group_name, create_time) VALUES (?, ?, ?)', 
                    (group_id, group_name, create_time))
        self.commit()

    def get_group_by_id(self, group_id):
        """根据群组ID获取群组信息"""
        return self.fetch_one('SELECT * FROM group_info WHERE group_id = ?', (group_id,))

    def get_all_groups(self):
        """获取所有群组信息"""
        return self.fetch_all('SELECT * FROM group_info')

    def update_group_name(self, group_id, new_name):
        """更新群组名称"""
        self.execute('UPDATE group_info SET group_name = ? WHERE group_id = ?', 
                    (new_name, group_id))
        self.commit()

    def delete_group(self, group_id):
        """删除群组"""
        self.execute('DELETE FROM group_info WHERE group_id = ?', (group_id,))
        self.commit()

