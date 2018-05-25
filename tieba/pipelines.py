# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from twisted.enterprise import adbapi
import pymysql
import pymysql.cursors
from urllib.parse import quote
from tieba.items import ThreadItem, PostItem, CommentItem, UserItem, ImageItem

class TiebaPipeline(object):
    @classmethod
    def from_settings(cls, settings):
        return cls(settings)

    def __init__(self, settings):
        dbname = settings['MYSQL_DBNAME']
        tbname = settings['TIEBA_NAME']
        if not dbname.strip():
            raise ValueError("No database name!")
        if not tbname.strip():
            raise ValueError("No tieba name!")          
        if isinstance(tbname, str):
            settings['TIEBA_NAME'] = tbname.encode('utf8')

        ssl = None
        if settings['MYSQL_USE_SSL']:
            ssl_check_hostname = True
            if settings['MYSQL_SSL_CHECK_HOSTNAME'] == 'False': 
                ssl_check_hostname = False
            ssl = {'ca' : settings['MYSQL_SSL_CA_PATH'],\
                   'check_hostname' : ssl_check_hostname }

        self.settings = settings
        
        self.dbpool = adbapi.ConnectionPool('pymysql',
            host=settings['MYSQL_HOST'],
            db=settings['MYSQL_DBNAME'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            ssl = ssl,
            charset='utf8mb4',
            cursorclass = pymysql.cursors.DictCursor,
            init_command = 'set foreign_key_checks=0' #异步容易冲突
        )
        
    def open_spider(self, spider):
        spider.cur_page = begin_page = self.settings['BEGIN_PAGE']
        spider.end_page = self.settings['END_PAGE']
        spider.filter = self.settings['FILTER']
        spider.see_lz = self.settings['SEE_LZ']
        if(spider.name == 'pantip'):
            start_url = 'http://pantip.com/tag/%s'%(quote(self.settings['TIEBA_NAME']))
        else: 
            start_url = "http://tieba.baidu.com/f?kw=%s&pn=%d" \
                %(quote(self.settings['TIEBA_NAME']), 50 * (begin_page - 1))
        if self.settings['GOOD_ONLY']:
            start_url += '&tab=good'
        
        spider.start_urls = [start_url]
        
    def close_spider(self, spider):
        self.settings['SIMPLE_LOG'].log(spider.cur_page - 1)
    
    def process_item(self, item, spider):
        _conditional_insert = {
            'thread': self.insert_thread, 
            'post': self.insert_post, 
            'comment': self.insert_comment,
            'user': self.insert_user,
            'image': self.insert_image,
            'pantipthread': self.insert_pantipthread,
            'pantippost': self.insert_pantippost, 
            'pantipcomment': self.insert_pantipcomment
        }
        query = self.dbpool.runInteraction(_conditional_insert[item.name], item)
        query.addErrback(self._handle_error, item, spider)
        return item
        
    def insert_thread(self, tx, item):
        sql = "insert into thread values(%s, %s, %s, %s, %s, %s) on duplicate key\
        update reply_num=values(reply_num), good=values(good)"
        # 回复数量和是否精品有可能变化，其余一般不变
        params = (item["thread_id"], item["forum_name"], item["title"], item['author'], item['reply_num'], item['good'])
        tx.execute(sql, params)     
        
    def insert_post(self, tx, item):
        sql = "insert into post values(%s, %s, %s, %s, %s, %s, %s, %s) on duplicate key\
        update content=values(content), comment_num=values(comment_num)"
        # 楼中楼数量和content(解析方式)可能变化，其余一般不变
        params = (item["post_id"], item["floor"], item['author'], item['content'], 
            item['time'], item['comment_num'], item['thread_id'], item['user_id'])
        tx.execute(sql, params)
        
    def insert_comment(self, tx, item):
        tx.execute('set names utf8mb4')
        sql = "insert into comment values(%s, %s, %s, %s, %s, %s) on duplicate key update content=values(content)"
        params = (item["comment_id"], item['author'], item['content'], item['time'], item['post_id'], item['user_id'])
        tx.execute(sql, params)
        
    def insert_user(self, tx, item):
        tx.execute('set names utf8mb4')
        sql = "insert into user values(%s, %s, %s, %s, %s) on duplicate key update posts_num=values(posts_num)"
        params = (item["user_id"], item["username"], item['sex'], item['years_registered'], item['posts_num'])
        tx.execute(sql, params)

    def insert_image(self, tx, item):
        tx.execute('set names utf8mb4')
        sql = "insert into image values(%s, %s, %s) on duplicate key update url=values(url), post_id = values(post_id)"
        params = (item["image_id"], item["post_id"], item["url"])
        tx.execute(sql, params)

    def insert_pantipthread(self, tx, item):
        sql = "insert into thread values(%s, %s, %s, %s, %s, %s, %s) on duplicate key\
        update reply_num=values(reply_num), good=values(good)"
        params = (item["thread_id"], item["forum_name"], item["title"], item['author'], item['reply_num'], item['good'], item['tags'])
        tx.execute(sql, params)     

    def insert_pantippost(self, tx, item):
        sql = "insert into post values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) on duplicate key\
        update content=values(content), comment_num=values(comment_num)"
        params = (item["post_id"], item["floor"], item['author'], item['content'], 
            item['time'], item['comment_num'], item['thread_id'], item['user_id'],
            item['ipv4'], item['ipv6'], item['likecount'], item['emotioncount'])
        tx.execute(sql, params)
        
    def insert_pantipcomment(self, tx, item):
        tx.execute('set names utf8mb4')
        sql = "insert into comment values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)\
                on duplicate key update content=values(content)"
        params = (item["comment_id"], item['author'], item['content'],\
                item['time'], item['post_id'], item['user_id'],
                item['ipv4'], item['ipv6'], item['likecount'], item['emotioncount'])            
        tx.execute(sql, params)

    #错误处理方法
    def _handle_error(self, fail, item, spider):
        spider.logger.error('Insert to database error: %s \
        when dealing with item: %s' %(fail, item))
