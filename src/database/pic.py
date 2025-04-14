from src.database.base import BaseDatabase

class PicManager(BaseDatabase):
    """图片管理器类"""
    def __init__(self, db_name='xhs.db'):
        super().__init__(db_name)

    def create_table(self):
        """创建图片表"""
        self.execute('''
            CREATE TABLE IF NOT EXISTS pic_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                content TEXT NOT NULL,
                group_id INTEGER NOT NULL,
                create_time INTEGER NOT NULL
            )
        ''')
        self.commit()

    def insert_pic(self, path, content, group_id, create_time):
        """插入图片信息"""
        self.execute('INSERT INTO pic_info (path, content, group_id, create_time) VALUES (?, ?, ?, ?)', 
                    (path, content, group_id, create_time))
        self.commit()

    def get_pic_by_id(self, pic_id):
        """根据图片ID获取图片信息"""
        return self.fetch_one('SELECT * FROM pic_info WHERE id = ?', (pic_id,))

    def get_pics_by_group_id(self, group_id):
        """根据群组ID获取该群组的所有图片"""
        return self.fetch_all('SELECT * FROM pic_info WHERE group_id = ?', (group_id,))

    def get_all_pics(self):
        """获取所有图片信息"""
        return self.fetch_all('SELECT * FROM pic_info')

    def update_pic_path(self, pic_id, new_path):
        """更新图片路径"""
        self.execute('UPDATE pic_info SET path = ? WHERE id = ?', 
                    (new_path, pic_id))
        self.commit()

    def delete_pic(self, pic_id):
        """删除图片记录"""
        self.execute('DELETE FROM pic_info WHERE id = ?', (pic_id,))
        self.commit()
        