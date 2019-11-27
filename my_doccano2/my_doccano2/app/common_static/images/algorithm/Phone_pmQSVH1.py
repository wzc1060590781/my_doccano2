import json
import re
import urllib
from lxml import etree
import requests
from pymongo import MongoClient


class JD_phone():
    def __init__(self):
        self.getcategory_url = "https://list.jd.com/list.html?cat=9987,653,655"
        self.conn = MongoClient("127.0.0.1",27017)
        self.db = self.conn.JD
        self.my_collection = self.db.test_collection

    def get_category(self):
        resp  = requests.get(self.getcategory_url)
        total_str = resp.content.decode()
        html = etree.HTML(total_str)
        li_list = html.xpath('//*[@id="plist"]/ul/li')
        # for li in li_list:
        #     print(li.xpath("./div/div[4]/a/@title"))
        print(total_str)
if __name__ == '__main__':
    jd = JD_phone()
    jd.get_category()
    # print(urllib.parse.unquote(
    #     "https://p.3.cn/prices/mgets?callback=jQuery2088863&ext=11101100&pin=&type=1&area=27_2376_2380_50350&skuIds=J_3133851%2CJ_3133853%2CJ_3133855%2CJ_3133857%2CJ_5089225%2CJ_5089255%2CJ_5089267%2CJ_5089269%2CJ_5089273%2CJ_5089275%2CJ_5544068%2CJ_6946603%2CJ_6946625%2CJ_6946631%2CJ_6946637%2CJ_7321794%2CJ_7421462%2CJ_7425622%2CJ_7425638%2CJ_7437710%2CJ_7437714%2CJ_7596939%2CJ_7635543%2CJ_7635559%2CJ_7651903%2CJ_7651927%2CJ_7652063%2CJ_8441388%2CJ_8654273%2CJ_8735304%2CJ_1202626888%2CJ_100000304401%2CJ_100001270083%2CJ_100000543206%2CJ_100001009384%2CJ_100004069505%2CJ_100004069493%2CJ_100008609748%2CJ_100008348530%2CJ_100008348532%2CJ_100004770263%2CJ_100008348534%2CJ_100008348550%2CJ_100005603522%2CJ_100003395467%2CJ_100003395445%2CJ_100004788067%2CJ_100004788069%2CJ_100004788073%2CJ_100001364160%2CJ_100002881193%2CJ_100002642218%2CJ_100002117901%2CJ_100001467225%2CJ_100002380994%2CJ_100002071812%2CJ_100008348548%2CJ_100008348536%2CJ_100008348546%2CJ_100000287115&pdbp=0&pdtk=&pdpin=&pduid=1548991760&source=list_pc_front&_=1570590053537"))
