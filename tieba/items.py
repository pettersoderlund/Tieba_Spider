# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ThreadItem(scrapy.Item):
    name = 'thread'
    thread_id = scrapy.Field()
    forum_name = scrapy.Field()
    title = scrapy.Field()
    author = scrapy.Field()
    reply_num = scrapy.Field()
    good = scrapy.Field()
    
class PostItem(scrapy.Item):
    name = 'post'
    post_id = scrapy.Field()
    floor = scrapy.Field()
    author = scrapy.Field()
    content = scrapy.Field()
    time = scrapy.Field()
    comment_num = scrapy.Field()
    thread_id = scrapy.Field()
    user_id = scrapy.Field()

class CommentItem(scrapy.Item):
    name = 'comment'
    comment_id = scrapy.Field()
    author = scrapy.Field()
    content = scrapy.Field()
    time = scrapy.Field()
    post_id = scrapy.Field()
    user_id = scrapy.Field()

class UserItem(scrapy.Item):
    name = 'user'
    username = scrapy.Field()
    sex = scrapy.Field()
    years_registered = scrapy.Field()
    posts_num = scrapy.Field()
    user_id = scrapy.Field()

class ImageItem(scrapy.Item):
    name = 'image'
    image_id = scrapy.Field()
    post_id = scrapy.Field()
    url = scrapy.Field()

