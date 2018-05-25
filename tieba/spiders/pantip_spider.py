# This Python file uses the following encoding: utf-8
import scrapy
from scrapy.spiders import CrawlSpider
from tieba.items import PantipThreadItem, PantipPostItem, PantipCommentItem, UserItem, ImageItem
import json
from . import helper
from datetime import datetime

class PantipSpider(scrapy.Spider):

    name = 'pantip'

    def parse(self, response):
        last_thread_id = 0
        forum_name = response.xpath('//ul[contains(@class, "breadcrumb")]/li[contains(@class, "last")]/text()').extract_first()
        for sel in response.xpath('//div[contains(@class, "post-list-wrapper")]/div[contains(@class, "post-item")]'):
            url = sel.xpath('./div[contains(@class, "post-item-title")]/a/@href').extract_first()
            last_thread_id = url.split("/")[-1]

            item = PantipThreadItem()
            item['forum_name'] = forum_name #'forum_name : tag'
            title = sel.xpath('./div[contains(@class, "post-item-title")]/a/text()').extract_first()
            item['title'] = helper.parse_content(title, False)
            item['author'] = sel.xpath('./div[contains(@class, "post-item-by")]/span/text()').extract_first()
            item['good'] = 0
            tags = sel.xpath('.//div[contains(@class, "post-item-taglist")]/div[contains(@class, "tag-item")]/a/span/@data-tag').extract()
            item['tags'] = ' | '.join(tags)

            replies = sel.xpath('.//div[contains(@class, "post-item-status-i")]/text()').extract()
            if(replies):
                item['reply_num'] = replies[1].strip()
            else:
                item['reply_num'] = 0

            item['thread_id'] = last_thread_id
            yield item

            yield response.follow(url, callback=self.parse_thread)

        url = response.url.split('?')[0]

        # Last thread id not needed with this method... 
        next_url = response.xpath('//div[contains(@class, "loadmore-bar")]/a[@rel="next"]/@href')
        #if(next_url):
        if(last_thread_id != 0):
            yield self.make_requests_from_url(url+'?tid='+str(last_thread_id))
        #    next_url = next_url.extract_first()
        #    if(response.url[response.url.find("tid=")+4:] != next_url[next_url.find("tid=")+4:]):
        #        yield self.make_requests_from_url(next_url)

        #yield self.make_requests_from_url(url+'?tid='+str(last_thread_id))

    def parse_thread(self, response):
        thread_id = response.url.split("/")[-1]
        item = PantipPostItem()
        item['thread_id']  = thread_id
        item['author'] = response.css(".display-post-name.owner::text")[0].extract()
        item['user_id']    = response.xpath('//div[contains(@class, "main-post-inner")]//a[contains(@class, "display-post-name")]/@id').extract_first()
        content = response.xpath('//div[contains(@class, "main-post-inner")]//div[@class="display-post-story"]').extract_first()
        item['content']    = helper.parse_content(content, True)
        item['post_id']    = '-' + str(thread_id) # Since the original post does not have a post id...
        posted = response.xpath('//div[contains(@class, "main-post-inner")]//span[@class="display-post-timestamp"]/abbr/@data-utime').extract_first()
        item['time']       = datetime.strptime(posted, '%m/%d/%Y %H:%M:%S')
        #item['emotions']   = comment['emotion']
        item['floor']      = 0
        item['comment_num'] = None
        item['ipv4'] = None
        item['ipv6'] = None
        ip = response.xpath('//div[contains(@class, "main-post-inner")]//span[contains(@class, "display-post-ip")]/text()')
        if(ip):
            s = ip.extract_first()
            ip = s[s.find("[IP: ")+5:s.find("]")]
            if(':' in ip):
                item['ipv6'] = ip
            else:
                item['ipv4'] = ip

        item['likecount'] = response.xpath('//div[contains(@class, "main-post-inner")]//span[contains(@class, "like-score")]/text()').extract_first()
        item['emotioncount'] = response.xpath('//div[contains(@class, "main-post-inner")]//span[contains(@class, "emotion-score")]/text()').extract_first()

        user_item = UserItem()
        user_item['user_id'] = item['user_id']
        user_item['username'] = item['author']
        user_item['sex'] = None
        user_item['years_registered'] = None
        user_item['posts_num'] = None
        yield user_item

        images = helper.get_images(content, True)
        if(images): 
            if len(images) > 0:
                for image in images:
                    yield self.parse_image(image_url = image, post_id = \
                        item['post_id'],image_index = images.index(image))

        yield item

        yield scrapy.Request("http://pantip.com/forum/topic/render_comments?tid="\
             + thread_id, callback=self.parse_comment,\
             headers={"X-Requested-With": "XMLHttpRequest"})

    def parse_comment(self, response):
        res = json.loads(response.body_as_unicode())

        if "count" in res:
            thread_id = res['paging']['topic_id']
            for comment in res["comments"]:
                item = PantipPostItem()
                #item['subcomment_count'] += comment["reply_count"]
                item['thread_id']  = thread_id
                item['author']     = comment['user']['name']
                item['user_id']    = comment['user']['mid']
                item['content']    = helper.parse_content(comment["message"], False)
                item['post_id']    = comment['_id']
                item['time']       = datetime.strptime(comment['data_utime'], '%m/%d/%Y %H:%M:%S')
                #item['emotions']   = comment['emotion']
                item['floor']      = comment['comment_no']
                item['comment_num'] = len(comment['replies'])
                item['ipv4'] = None
                item['ipv6'] = None

                if('data_ip_email' in comment):
                    if(':' in comment['data_ip_email']):
                        item['ipv6'] = comment['data_ip_email']
                    else:
                        item['ipv4'] = comment['data_ip_email']

                if('ipv6' in comment):
                    item['ipv6'] = comment['ipv6']

                item['likecount'] = 0
                item['emotioncount'] = comment['emo_score']

                user_item = UserItem()
                user_item['user_id'] = item['user_id']
                user_item['username'] = item['author']
                user_item['sex'] = None
                user_item['years_registered'] = None
                user_item['posts_num'] = None
                yield user_item

                images = helper.get_images(comment['message'], False)
                if(images): 
                    if len(images) > 0:
                        for image in images:
                            yield self.parse_image(image_url = image, post_id = \
                                item['post_id'],image_index = images.index(image))

                yield item

                #if self.is_anon(username):
                    #item['anon_comment_count'] += 1
                    # set anon flag user
                for subcomment in comment["replies"]:
                    item = PantipCommentItem()
                    item['content'] = helper.parse_content(subcomment['message'], False)
                    item['comment_id'] = subcomment['reply_id']
                    item['post_id'] = comment['_id']
                    item['user_id'] = subcomment['user']['mid']
                    item['time'] = datetime.strptime(subcomment['data_utime'], '%m/%d/%Y %H:%M:%S')
                    item['author'] = subcomment['user']['name']
                    item['ipv4'] = None

                    if('data_ip_email' in subcomment):
                        # Check if ipv6
                        if(':' not in subcomment['data_ip_email']):
                            item['ipv4'] = subcomment['data_ip_email']

                    if('ipv6' in subcomment):
                        item['ipv6'] = subcomment['ipv6']
                    else:
                        item['ipv6'] = None

                    item['likecount'] = 0
                    item['emotioncount'] = subcomment['emo_score']

                    user_item = UserItem()
                    user_item['user_id'] = item['user_id']
                    user_item['username'] = item['author']
                    user_item['sex'] = None
                    user_item['years_registered'] = None
                    user_item['posts_num'] = None
                    yield user_item

                    images = helper.get_images(subcomment['message'], False)

                    if(images): 
                        if len(images) > 0:
                            for image in images:
                                yield self.parse_image(image_url = image, post_id = \
                                    item['post_id'],image_index = images.index(image), comment = True)

                    yield item

                    
                    #if self.is_anon(subcomment["user"]["name"]):
                        #item['anon_subcomment_count'] += 1
            #return item

    def is_anon(self, username):
        if username.find(u'สมาชิกหมายเลข') != -1:
            return True
        else:
            return False

    def parse_image(self, image_url, post_id, image_index, comment = False):
        item = ImageItem()
        item['url'] = image_url
        item['post_id'] = post_id
        if(comment is True): 
            #image from comment
            separator = 'cm'
        else:
            #image from post
            separator = 'ps'

        item['image_id'] = str(post_id) + separator + str(image_index)
        return item

