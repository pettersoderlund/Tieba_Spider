# Tieba_Spider
Tieba Crawler. 

## Updates
20180928 - Started to translate readme from chinese to english with help from Google translate. Posts are sometimes marked as "floor" where the 1st floor is the thread initiator. 2nd floor is the first answer and so on. 

## System and dependency reference
Ubuntu 16.04.4 LTS (GNU/Linux 4.4.0-133-generic x86_64)
Python 3.5.2
mysql  Ver 14.14 Distrib 5.7.23
lxml==4.2.1
beautifulsoup4==4.6.0
Twisted==17.9.0
Scrapy==1.5.0
PyMySQL==0.8.0

See full list in requirements.txt

## Installation
### Prerequisites
Python3
A mysql database

# Installing python packages
Run the following command in a terminal to install related packages. Make sure pip is pointing to your python3 installation. 
$pip install -r requirements.txt

## Instructions
First open the config.json file, configure the domain name, username and password of the database. Then run the command directly:
```
Scrapy run <tieba forum name> <database name> [option]
```
The tieba forum name does not include the word "吧" at the end, and the database name is the name of the database to be stored. The database will be created before crawling. E.g
```
scrapy run 仙五前修改 Pal5Q_Diy
```
If you have configured the name of the paste and the corresponding database name in config.json, you can ignore the database name. If you ignore the name of the post, then crawl the database of DEFAULT in config.json.

**Special Reminder** Once the mission is disconnected, you cannot proceed. Therefore, when SSH opens a task, please ensure that you do not disconnect, or consider using background tasks or screen commands.

## Options Description

|Short form|Long form     |Number of arguments|Function                              |Example                           |
|------|-----------|--------|----------------------------------|-------------------------------|
|-p    |--pages    |2       |Set the start and end pages of the crawled post     |scrapy run ... -p 2 5          |
|-g    |--good_only|0       |Only climb the boutique posts (??? translators edit) |scrapy run ... -g              |
|-s    |--see_lz   |0       |Look at the landlord, that is, not climbing the floor of the non-landlord (??? translators edit |scrapy run ... -s              |
|-f    |--filter   |1       |Set post filter function name (see `filter.py`)|scrapy run ... -f thread_filter| 

Example：
```
scrapy run 仙剑五外传 -gs -p 5 12 -f thread_filter
```
Use only look at the landlord mode to climb the fairy sword five outside the best posts in the fifth page to the 12th post, which can pass the `filter_py` function in the `filter_py` function and its contents will be stored in the database.

## Data processing
The data that is crawled is not stored in the same way, and some processing will be performed.

1.  The ad posts will be removed (the posts with the word "advertising" in the lower right corner).
2. The bold and red characters are lost to plain text (the get_text function of the beautifulsoup).
3. Common expressions will be converted to text expressions (emotion.json, welcome to add).
4. The picture and video will become the corresponding link (to get a video link you need to get a 302 response).

## Data saving structure
 - thread
 
Some basic information for each post.

|Column      |Types        |Remarks                                                     |
|---------|------------|--------------------------------------------------------|
|thread_id       |BIGINT(12)  |"http://tieba.baidu.com/p/4778655068"  has the ID of 4778655068|
|title    |VARCHAR(100)|                                                        |
|author   |VARCHAR(30) |                                                        |
|reply_num|INT(4)      |Reply quantity               |
|good     |BOOL        |Whether it is a boutique post                                           |
|last_seen|datetime|For continuous scraping this is a date when the element was last scraped|
|times_seen|datetime|For continuous scraping this is a counter for the number of times the element has been scraped|

 - post

Some basic information for each post/floor, including the first floor.

|Column | Types |Remarks |
|-----------|-----------|----------------------|
|post_id |BIGINT(12) |The floor also has a corresponding ID |
|floor |INT(4)|floor number |
|author |VARCHAR(30)| |
|content |TEXT | Floor Content |
|time |DATETIME |Published time |
|comment_num|INT(4) |Reward number of buildings in the building |
|thread_id |BIGINT(12) |The main post ID of the floor, foreign key|
|user_id|bigint(20)||
|last_seen|datetime|For continuous scraping this is a date when the element was last scraped|
|times_seen|datetime|For continuous scraping this is a counter for the number of times the element has been scraped|



 - comment
 
Some information about the building in the middle of the building.

|Column | Types |Remarks |
|-------|-----------|--------------------------|
|comment_id |BIGINT(12) |The building has an ID and is shared with the floor|
|author |VARCHAR(30)| |
|content|TEXT |Floor Building Content |
|time |DATETIME |Published time |
|post_id|BIGINT(12) | Main floor ID of the building, foreign key |
|user_id|bigint(20)||
|last_seen|datetime|For continuous scraping this is a date when the element was last scraped|
|times_seen|datetime|For continuous scraping this is a counter for the number of times the element has been scraped|


The crawling method determines that the comment may be crawled before the corresponding post, and the foreign key is wrong. Therefore, the foreign key detection of the database at the beginning of the task will be closed.

- image
Links to images in posts 

|Column | Types |Remarks |
|-------|-----------|--------------------------|
|image_id|varchar(30)||
|post_id|bigint(20)||
|url|text||


- user
Information about users

|Column | Types |Remarks |
|-------|-----------|--------------------------|
|user_id|bigint(20)||
|username|varchar(125)||
|sex|varchar(6)||
|years_registered|float|Year count on tieba|
|posts_num|int(11)|Number of posts on tieba|


## Time-consuming reference
Time-consuming is related to server bandwidth and crawl time. Below is the time when my Alibaba Cloud server crawls several stickers. It is for reference only.

| Post bar name | Posts number | Reply number | Floor number of buildings | Time (seconds) |
|----------|------|-------|--------|--------|
|pandakill |3638  |41221  |50206   |222.2   |
|lyingman  |11290 |122662 |126670  |718.9   |
|仙剑五外传|67356 |1262705|807435  |7188    |

The following are the crawls at the same time:

| Post bar name | Posts number|Reply number|Floor number of buildings|Time (seconds)|
|-----------|------|------|--------|--------|
|仙五前修改 |530   |3518  |7045    |79.02   |
|仙剑3高难度|2080  |21293 |16185   |274.6   |
|古剑高难度 |1703  |26086 |32941   |254.0   |

**Special Reminder** Please pay attention to the space occupied by crawling data, do not fill the disk.


# Pantip spider
There is a crawler for the www.pantip.com forum as well in this project, built in the same fashion as the Tieba spider. It uses the same database configuration. 
It is run by the command:
```
scrapy run_pantip <pantip keyword> <database>
```
