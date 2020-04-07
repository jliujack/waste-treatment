import requests        #导入requests包
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import xlwt
import re

kw = ['垃圾分类', '垃圾处理']
city = {
    '北京市': '11',
    '上海市': '31',
    '深圳': '4403',
    '广东': '44 not 4403'
}

# 获取Url地址列表
def getUrlList(params, area):
    url = 'http://search.ccgp.gov.cn/bxsearch?searchtype=1&bidSort=0&buyerName=&projectId=&pinMu=0&bidType=7&dbselect=bidx&start_time=2019%3A04%3A07&end_time=2020%3A04%3A07&timeType=6&displayZone=%E5%8C%97%E4%BA%AC%E5%B8%82&pppStatus=0&agentName='
    query = urlencode(params)
    res = requests.get(url+'&'+query)
    soup = BeautifulSoup(res.text, 'lxml')
    data = soup.select('.vT-srch-result-list-bid>li> a')
    total = soup.select('body > div:nth-child(9) > div:nth-child(1) > div > p:nth-child(1) > span:nth-child(2)')[0].get_text()
    total = int(total)
    while params['page_index'] * 20 < total:
        params['page_index'] += 1
        query = urlencode(params)
        res = requests.get(url + '&' + query)
        soup = BeautifulSoup(res.text, 'lxml')
        data.extend(soup.select('.vT-srch-result-list-bid>li> a'))
    ret = []
    for item in data:
        result = {
            'title': item.get_text().strip(),
            'link': item.get('href'),
            'bid-area': area,
            'bid-kw': params['kw'],
            'bid-name': '',
            'purchaser': '',
            'bid-winner': '',
            'bid-date': '',
            'bid-amount': ''
        }
        ret.append(result)
    return ret

#爬取中标详细信息 采购单位、中标人、中标日期、中标金额
def detail(obj):
    try:
        headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER'}
        res = requests.get(obj['link'], headers=headers)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'lxml')
        purchase_node = soup.find(class_="title", string="采购单位")
        obj['purchaser'] = purchase_node.next_sibling.string

        purchase_node = soup.find_all(string=re.compile("供应商名称："))
        if not purchase_node:
            purchase_node = soup.find_all(string=re.compile("中标单位："))
            if not purchase_node:
                purchase_node = soup.find_all(string=re.compile("中标人："))
        if purchase_node:
            bid_list = [i.split('：')[1] for i in purchase_node]
            obj['bid-winner'] = ','.join(bid_list)
        else:
            purchase_node = soup.find("td", string=re.compile("中标供应商名称"))
            if purchase_node:
                purchase_node = purchase_node.parent
                purchase_node = purchase_node.parent.find_all('tr')[1].find_all('td')[1]
                obj['bid-winner'] = purchase_node.string
            else:
                purchase_node = soup.find("p", string=re.compile("中标供应商名称"))
                if purchase_node:
                    purchase_node = purchase_node.next_sibling
                    purchase_node = purchase_node.next_sibling
                    purchase_node = purchase_node.strings
                    for string in purchase_node:
                        obj['bid-winner'] = string.split('、')[0]
                        break
        purchase_node = soup.find(class_="title", string="中标日期")
        if purchase_node:
            obj['bid-date'] = purchase_node.next_sibling.string

        purchase_node = soup.find(string=re.compile("中标金额："))
        if purchase_node:
            obj['bid-amount'] = purchase_node.split('：')[1]
        else:
            purchase_node = soup.find(class_="title", string="总中标金额")
            if purchase_node:
                obj['bid-amount'] = purchase_node.next_sibling.string[1:]

        purchase_node = soup.find(string=re.compile("项目名称："))
        if purchase_node:
            obj['bid-name'] = purchase_node.split('：')[1]
        else:
            purchase_node = soup.find(class_="title", string="项目名称")
            if purchase_node:
                obj['bid-name'] = purchase_node.next_sibling.string[1:]

        print('采购单位：' + obj['purchaser'] + '\t中标成交供应商名称：' + obj['bid-winner'] +'\t中标日期：' + obj['bid-date'] +'\t中标金额：' + obj['bid-amount'] +'\t项目名称：' + obj['bid-name'])
    except:
        preint('error happened!!!!!!')
#中标信息写入excel文件
def writeExcel(excelPath,objs):
    workbook = xlwt.Workbook()
    #获取第一个sheet页
    sheet = workbook.add_sheet('git')
    row0=['地区','项目名称','采购单位','中标成交供应商名称','中标日期','中标金额','标题','链接', '搜索关键字']
    for i in range(0,len(row0)):
        sheet.write(0,i,row0[i])
    for i in range(0,len(objs)):
        obj = objs[i]
        sheet.write(i + 1, 0, obj['bid-area'])
        sheet.write(i + 1, 1, obj['bid-name'])
        sheet.write(i + 1, 2, obj['purchaser'])
        sheet.write(i + 1, 3, obj['bid-winner'])
        sheet.write(i + 1, 4, obj['bid-date'])
        sheet.write(i + 1, 5, obj['bid-amount'])
        sheet.write(i + 1, 6, obj['title'])
        sheet.write(i + 1, 7, obj['link'])
        sheet.write(i + 1, 8, obj['bid-kw'])
    workbook.save(excelPath)

# 主函数
def main():
    data = []
    for key in city:
        for search_text in kw:
            print('-----分隔符', key, ' ', search_text, '-------')
            params = {
                'page_index': 1,
                'kw': search_text,
                'zoneId': city[key],
            }
            newdata = getUrlList(params, key)
            for obj in newdata:
                link = obj['link']
                if (not link or not link.startswith('http')):
                    continue
                detail(obj)
            data.extend((newdata))
    writeExcel('d:/waste-treatment.xlsx', data)

# def test(url):
#     detail({'link': url})
#
# test('http://www.ccgp.gov.cn/cggg/dfgg/zbgg/201912/t20191231_13683100.htm')

main()
