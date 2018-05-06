# -*- coding: utf-8 -*-

import json
import os
import sys
import pymysql
import warnings
import time
import csv

class config:
    config_path = 'config.json'
    config = None

    def __init__(self):
        with open(self.config_path, 'r') as f:
            self.config = json.loads(f.read())
            # loads后若有中文 为unicode
    def save(self):
        with open(self.config_path, 'wb') as f:
            s = json.dumps(self.config, indent=4, ensure_ascii=False)
            if isinstance(s, str):
                s = s.encode('utf8')
            f.write(s)

class log:
    log_path = 'spider.log'
    
    def __init__(self, tbname, dbname, begin_page, good_only, see_lz):
        if not os.path.isfile(self.log_path):
            with open(self.log_path, 'w') as f:
                csvwriter = csv.writer(f, delimiter='\t')
                csvwriter.writerow(['start_time','end_time','elapsed_time','tieba_name','database_name', 'pages', 'etc'])
        self.tbname = tbname
        self.dbname = dbname
        self.begin_page = begin_page
        etc = []
        if good_only:
            etc.append('good_only')
        if see_lz:
            etc.append('see_lz')
        self.etc = '&'.join(etc)
        if not self.etc:
            self.etc = "None"
        self.start_time = time.time()
        
    def log(self, end_page):
        end_time = time.time()
        elapsed_time = '%.4g' % (end_time - self.start_time)
        start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time))
        end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))
        tbname = self.tbname

        pages = '%d~%d'%(self.begin_page, end_page) if end_page >= self.begin_page else 'None'
        with open(self.log_path, 'a') as f:
            csvwriter = csv.writer(f, delimiter='\t')
            csvwriter.writerow([start_time, end_time, elapsed_time, tbname, self.dbname, pages, self.etc])
        
        
def init_database(host, user, passwd, dbname, use_ssl = False, ssl_check_hostname = False, ssl_ca = None):
    warnings.filterwarnings('ignore', message = "Table.*already exists") 
    warnings.filterwarnings('ignore', message = "Can't create.*database exists") 
    #都说了if not exists还报警告 = =
    ssl = None
    if use_ssl:
        ssl = {'ca' : ssl_ca, 'check_hostname' : ssl_check_hostname }

    db = pymysql.connect(host, user, passwd, ssl=ssl)
    tx = db.cursor()
    tx.execute('set names utf8mb4')
    tx.execute('create database if not exists `%s`default charset utf8mb4\
    default collate utf8mb4_general_ci;' % pymysql.escape_string(dbname))
    #要用斜引号不然报错
    #万恶的MySQLdb会自动加上单引号 结果导致错误
    db.select_db(dbname)
    tx.execute("create table if not exists user(user_id BIGINT,\
        username VARCHAR(30),\
        sex VARCHAR(6), years_registered FLOAT, posts_num INT(11),\
        PRIMARY KEY (user_id)) CHARSET=utf8mb4;")
    tx.execute("create table if not exists thread(\
        thread_id BIGINT(12), forum_name VARCHAR(125), title VARCHAR(100),\
        author VARCHAR(30), reply_num INT(4),\
        good BOOL, PRIMARY KEY (thread_id)) CHARSET=utf8mb4;")
    tx.execute("create table if not exists post(\
        post_id BIGINT(12), floor INT(4), author VARCHAR(30), content TEXT,\
        time DATETIME, comment_num INT(4), thread_id BIGINT(12),\
        user_id BIGINT, PRIMARY KEY (post_id),\
        FOREIGN KEY (thread_id) REFERENCES thread(thread_id),\
        FOREIGN KEY (user_id) REFERENCES user(user_id)\
        ) CHARSET=utf8mb4;")
    tx.execute("create table if not exists comment(comment_id BIGINT(12),\
        author VARCHAR(30), content TEXT, time DATETIME, post_id BIGINT(12),\
        user_id BIGINT,\
        PRIMARY KEY (comment_id), FOREIGN KEY (post_id) REFERENCES post(post_id),\
        FOREIGN KEY (user_id) REFERENCES user(user_id)\
        ) CHARSET=utf8mb4;")
    tx.execute("create table if not exists image(image_id varchar(30),\
        post_id BIGINT, url TEXT,\
        PRIMARY KEY (image_id), FOREIGN KEY (post_id) REFERENCES post(post_id)\
        ) CHARSET=utf8mb4;")
    db.commit()
    db.close()
    warnings.resetwarnings()

    warnings.filterwarnings('ignore', message = ".*looks like a ") 
    # bs.get_text传入纯url内容的时候会被误解
