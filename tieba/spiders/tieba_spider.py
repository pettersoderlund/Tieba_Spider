# -*- coding: utf-8 -*-

import scrapy
import json
from tieba.items import ThreadItem, PostItem, CommentItem, UserItem, ImageItem
from . import helper
import time

#Used for debug
#import logging
#from scrapy.utils.log import configure_logging

class TiebaSpider(scrapy.Spider):
    name = "tieba"
    cur_page = 1    #modified by pipelines (open_spider)
    end_page = 9999
    filter = None
    see_lz = False
    
    # Used for debug
    """configure_logging(install_root_handler=False)
    logging.basicConfig(
        filename='log.txt',
        format='%(levelname)s: %(message)s',
        level=logging.INFO
    )"""    
    
    def parse(self, response): #forum parser
        for sel in response.xpath('//li[contains(@class, "j_thread_list")]'):
            data = json.loads(sel.xpath('@data-field').extract_first())
            item = ThreadItem()
            item['thread_id'] = data['id']
            item['forum_name'] = self._parse_forum_name(response)
            item['author'] = data['author_name']
            item['reply_num'] = data['reply_num']
            item['good'] = data['is_good']
            if not item['good']:
                item['good'] = False
            item['title'] = sel.xpath('.//div[contains(@class, "threadlist_title")]/a/text()').extract_first()
            if self.filter and not self.filter(item["id"], item["title"], item['author'], item['reply_num'], item['good']):
                continue
            #filter过滤掉的帖子及其回复均不存入数据库
               
            yield item
            meta = {'thread_id': data['id'], 'page': 1}
            url = 'http://tieba.baidu.com/p/%d' % data['id']
            if self.see_lz:
                url += '?see_lz=1'
            yield scrapy.Request(url, callback = self.parse_post,  meta = meta)
        next_page = response.xpath('//a[@class="next pagination-item "]/@href')
        self.cur_page += 1
        if next_page:
            if self.cur_page <= self.end_page:
                yield self.make_requests_from_url('http:'+next_page.extract_first())
            
    def parse_post(self, response): 
        meta = response.meta
        has_comment = False
        for floor in response.xpath("//div[contains(@class, 'l_post')]"):
            if not helper.is_ad(floor):
                data = json.loads(floor.xpath("@data-field").extract_first())
                item = PostItem()
                item['post_id'] = data['content']['post_id']
                item['author'] = data['author']['user_name']
                item['comment_num'] = data['content']['comment_num']
                if item['comment_num'] > 0:
                    has_comment = True
                content = floor.xpath(".//div[contains(@class,'j_d_post_content')]").extract_first()
                #以前的帖子, data-field里面没有content
                item['content'] = helper.parse_content(content, True)
                
                images = helper.get_images(content, True)
                if len(images) > 0:
                    for image in images:
                        yield self.parse_image(image_url=image, post_id=item['post_id'],image_index=images.index(image))

                #以前的帖子, data-field里面没有thread_id
                item['thread_id'] = meta['thread_id']
                item['floor'] = data['content']['post_no'] 
                if 'user_id' in data['author'].keys():
                    item['user_id'] = data['author']['user_id']
                else:
                    item['user_id'] = None
                #只有以前的帖子, data-field里面才有date
                if 'date' in data['content'].keys():
                    item['time'] = data['content']['date']
                    #只有以前的帖子, data-field里面才有date
                else:
                    item['time'] = floor.xpath(".//span[@class='tail-info']")\
                    .re_first(r'[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}')
                user_uri = floor.xpath(".//a[@class='p_author_name j_user_card']/@href").extract_first() 
                if user_uri:
                    url = 'http://tieba.baidu.com%s' % user_uri
                    yield scrapy.Request(url, callback = self.parse_user)
                yield item
        if has_comment:
            url = "http://tieba.baidu.com/p/totalComment?tid=%d&fid=1&pn=%d" % (meta['thread_id'], meta['page'])
            if self.see_lz:
                url += '&see_lz=1'
            yield scrapy.Request(url, callback = self.parse_comment, meta = meta)
        next_page = response.xpath(u".//ul[@class='l_posts_num']//a[text()='下一页']/@href")
        if next_page:
            meta['page'] += 1
            url = response.urljoin(next_page.extract_first())
            yield scrapy.Request(url, callback = self.parse_post, meta = meta)

    def parse_comment(self, response):
        comment_list = json.loads(response.body_as_unicode())['data']['comment_list']
        for value in comment_list.values():
            comments = value['comment_info']
            for comment in comments:
                item = CommentItem()
                item['comment_id'] = comment['comment_id']
                item['author'] = comment['username']
                item['post_id'] = comment['post_id']
                item['content'] = helper.parse_content(comment['content'], False)
                item['time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(comment['now_time']))
                item['user_id'] = comment['user_id']
                yield item
                url = 'http://tieba.baidu.com/home/main?un=%s' % comment['username']
                yield scrapy.Request(url, callback = self.parse_user)

    def parse_user(self, response):
        if 'error.html' not in response.url:
            item = UserItem()
            item['username'] = response.xpath("//span[@class='userinfo_username ']/text()").extract_first()
            item['sex'] = response.xpath("//div[@class='userinfo_userdata']/span[1]/@class").extract_first()[26:]
            item['years_registered'] = self._parse_user_age(response)
            item['posts_num'] = self._parse_user_posts_num(response)
            item['user_id'] = response.xpath("//a[contains(@class, 'btn_sendmsg')]/@href").extract_first()[15:]
            yield item

    def parse_image(self, image_url, post_id, image_index):
        item = ImageItem()
        item['url'] = image_url
        item['post_id'] = post_id
        item['image_id'] = str(post_id) + 'i' + str(image_index)
        return item

    def _parse_user_age(self, response):
        """Helper function tp get user age on tieba
        :returns: user age decimal / float
        """
        return scrapy.Selector(response).css('.user_name span:nth-child(2)::text').extract_first()[3:-1] or 0# 吧龄:(X)X.X年

    def _parse_user_posts_num(self, response):
        """ Helper function to get number of posts in a user profile. 
        character 万indicates 10000 posts. 
        :returns: numberofposts int
        """
        num = scrapy.Selector(response).css('.userinfo_userdata span:nth-child(4)::text').extract_first() # 发贴:(X)X.X万
        num = num[num.find(":")+1:]
        
        if num:
            return num if self._is_number(num) is True else float(num[:-1]) * 10000
        else:
            return 0
    
    def _is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def _parse_forum_name(self, response):
        tieba_name = response.xpath("//div[@class='card_title']/a[contains(@class, 'card_title_fname')]/text()").extract_first().strip()#xx吧
        return tieba_name[:-1]#xx

