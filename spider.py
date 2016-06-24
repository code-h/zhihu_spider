#!/usr/bin/env python
#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

import requests
import redis
from lxml import html
from multiprocessing.dummy import Pool
from mongodbs import Zhihu_User_Profile

#from requests.packages.urllib3.exceptions import InsecureRequestWarning

'''
爬虫核心逻辑
'''

class Spider():

    def __init__(self,url,option="print_data_out"):
        self.url=url
        self.option=option
        self.header={}

        #cookie要自己从浏览器获取
        self.header["User-Agent"]="Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:35.0) Gecko/20100101 Firefox/35.0"
        self.cookies={"q_c1":"0ccc0032c7de427b9a60b372811a9def|1465797740000|1465797740000",
                      "l_cap_id":'"Mzk2YWE5YjVhMjVhNDU0MThmYjYyYzM1N2VmNjgxNDQ=|1465797740|85024d9a22de44df66e6d09d3dde66c8eda33f87"',
                      "cap_id":'"YjBmODNmMjcyM2MzNDk1MTkxYTk0ZDZmMzcyMjdkMTU=|1465797740|de1d96022ab5299ffb18788f2d8f0dc46da31296"',
                      "d_c0":'"AACANE4qEgqPTi0DK6P2CPRHcV9ebgYC2Z8=|1465797741"',
                      "_za":"e762b9d7-c8d3-4d07-afdf-90aab4184ba9",
                      "login":'"OWIyMWY5OGVjOWIxNGI4ZGFhNjc0ODkxMGUzNWQ1MGI=|1465797750|08bd76ed073ec1d81694558bf0336cb645356e72"',
                      "__utma":"51854390.101148435.1466736718.1466736718.1466738576.2",
                      "__utmz":"51854390.1466738576.2.2.utmcsr=zhihu.com|utmccn=(referral)|utmcmd=referral|utmcct=/",
                      "_xsrf":"6613cd948f1e44365dfb31dde644e389",
                      "_zap":"a769d54e-78bf-44af-8f24-f9786a00e322",
                      "__utmb":"51854390.3.9.1466738838982",
                      "__utmc":"51854390",
                      "l_n_c":"1",
                      "z_c0":"Mi4wQUFDQVBvUkNBQUFBQUlBMFRpb1NDaGNBQUFCaEFsVk5kdG1GVndDVU9RR1NJRElLRU1uZ3hiV2NyTmdzdEpYczB3|1465797750|bf5ba241e9db5f544d70599d90aa5df24ae3e86c",
                      "s-q":"%E4%BA%91%E8%88%92",
                      "s-i":"2",
                      "sid":"1jsjlbsg",
                      "s-t":"autocomplete",
                      "__utmv":"51854390.100-1|2=registration_date=20141130=1^3=entry_date=20141130=1",
                      "__utmt":"1"}

    def get_user_data(self):
        followee_url=self.url+"/followees"
        try:
            get_html=requests.get(followee_url,cookies=self.cookies,
                                headers=self.header,verify=False)
        except:
            print "requests get error!"
            return
        content=get_html.text
        if get_html.status_code==200:
            self.analy_profile(content)
            return

    def get_xpath_source(self,source):
        if source:
            return source[0]
        else:
            return ''

    #使用xpath解析html
    def analy_profile(self,html_text):
        tree=html.fromstring(html_text)
        self.user_name=self.get_xpath_source(tree.xpath("//a[@class='name']/text()"))
        self.user_avatar=self.get_xpath_source(tree.xpath("//img[@class='Avatar Avatar--l']/@src"))
        self.user_location=self.get_xpath_source(tree.xpath("//span[@class='location item']/@title"))
        self.user_gender=self.get_xpath_source(tree.xpath("//span[@class='item gender']/i/@class"))
        if "female" in self.user_gender and self.user_gender:
            self.user_gender="female"
        else:
            self.user_gender="male"
        self.user_employment=self.get_xpath_source(tree.xpath("//span[@class='employment item']/@title"))
        self.user_employment_extra=self.get_xpath_source(tree.xpath("//span[@class='position item']/@title"))
        self.user_education_school=self.get_xpath_source(tree.xpath("//span[@class='education item']/@title"))
        self.user_education_subject=self.get_xpath_source(tree.xpath("//span[@class='education-extra item']/@title"))
        try:
            self.user_followees=tree.xpath("//div[@class='zu-main-sidebar']//strong")[0].text
            self.user_followers=tree.xpath("//div[@class='zu-main-sidebar']//strong")[1].text
        except:
            return
        self.user_be_agreed=self.get_xpath_source(tree.xpath("//span[@class='zm-profile-header-user-agree']/strong/text()"))
        self.user_be_thanked=self.get_xpath_source(tree.xpath("//span[@class='zm-profile-header-user-thanks']/strong/text()"))
        self.user_info=self.get_xpath_source(tree.xpath("//span[@class='bio']/@title"))
        self.user_intro=self.get_xpath_source(tree.xpath("//span[@class='content']/text()"))

        if self.option == "print_data_out":
            self.print_data_out()
        else:
            self.store_data_to_mongo()
        global red
        #提取出被关注者的url
        url_list=tree.xpath("//h2[@class='zm-list-content-title']/a/@href")
        for target_url in url_list:
            target_url=target_url.replace("https","http")
            if red.sadd('red_had_spider',target_url):
                red.lpush('red_to_spider',target_url)


    def print_data_out(self):
        print "*" * 60
        print '用户名:%s\n' % self.user_name
        print '用户头像:%s\n' % self.user_avatar
        print "用户性别:%s\n" % self.user_gender
        print '用户地址:%s\n' % self.user_location
        print "被同意:%s\n" % self.user_be_agreed
        print "被感谢:%s\n" % self.user_be_thanked
        print "被关注:%s\n" % self.user_followers
        print "关注了:%s\n" % self.user_followees
        print "工作:%s/%s" % (self.user_employment, self.user_employment_extra)
        print "教育:%s/%s" % (self.user_education_school, self.user_education_subject)
        print "用户信息:%s" % self.user_info
        print "*" * 60


    def store_data_to_mongo(self):
        new_profile = Zhihu_User_Profile(
        user_name=self.user_name,
        user_avatar=self.user_avatar,
        user_be_agreed=self.user_be_agreed,
        user_be_thanked=self.user_be_thanked,
        user_followees=self.user_followees,
        user_followers=self.user_followers,
        user_education_school=self.user_education_school,
        user_education_subject=self.user_education_subject,
        user_employment=self.user_employment,
        user_employment_extra=self.user_employment_extra,
        user_location=self.user_location,
        user_gender=self.user_gender,
        user_info=self.user_info,
        user_intro=self.user_intro,
        user_url=self.url
        )
        new_profile.save()
        print "saved: %s \n" %self.user_name

#　核心模块,bfs宽度优先搜索
def BFS_Search(option):
    global red
    while True:
        temp=red.rpop('red_to_spider')
        if type(temp)==None:
            print 'empty'
            break
        result=Spider(temp,option)
        result.get_user_data()

    return "ok"


if __name__=='__main__':

    try:
        option=sys.argv[1]
    except:
        print 'argv is not accepted'
        sys.exit()
    red=redis.Redis(host='localhost',port=6379,db=1)
    red.lpush('red_to_spider',"https://www.zhihu.com/people/liu-shi-tao-30")

    BFS_Search(option)

    #使用多进程，注意，实际测试出来，并没有明显速度的提升,瓶颈在IO写;如果直接输出的话,速度会明显加快
    '''
    res=[]
    process_Pool=Pool(4)
    for i in range(4):
        res.append(process_Pool.apply_async(BFS_Search,(option, )))

    process_Pool.close()
    process_Pool.join()

    for num in res:
        print ":::",num.get()
    print 'Work had done!'
    '''







