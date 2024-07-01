# 用于查询PN物料信息
from lxml import etree
from Data_Prepare.GetCookies import keep_seesion
import pandas as pd

def SearchPN(PN):
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/" \
                "537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"

    headers = {'User-Agent': userAgent}

    session = keep_seesion('NAVL')
    data = {
        'VP$ScriptManager1': 'VP$UpdatePanel1|VP$BtnSearch',
        'VP_FsFilter_hidden': 'block',
        'VP$DdlFolderSearch': '-1',
        'VP$TxtLIPNSearch': PN,
        'VP$DdlEolSearch': '-1',
        'VP$GvList$ctl04$PageList': '0',
        '__VIEWSTATEGENERATOR': '8D19A1CC',
        '__EVENTTARGET': '',
        '__ASYNCPOST': 'true',
        'VP$BtnSearch': 'Filter',
    }

    url = "http://10.122.66.105/NAVL/Default.aspx?vp=searchbb"
    response = session.post(url, headers=headers, data=data).text
    tree = etree.HTML(response)
    xpath_queries = {
        'pn': "//tbody/tr/td[2]/a/text()",
        'fru': "//tbody/tr/td[3]/text()",
        'description': "//tbody/tr/td[7]/text()",
        'supplier': "//tbody/tr/td[8]/text()",
        'note': "//tbody/tr/td[13]/text()",
    }

    results = {}
    for variable, xpath_query in xpath_queries.items():
        try:
            result = tree.xpath(xpath_query)[0]
        except IndexError:
            result = '空'
        results[variable] = result
    data = {
        'PN': [results['pn']],
        'Description': [results['description']],
        'Supplier': [results['supplier']],
        'Fru': [results['fru']],
        'Note': [results['note']]
    }
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(data)
    return df

def SearchProject(PN):
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/" \
                "537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    headers = {'User-Agent': userAgent}

    session = keep_seesion('NAVL')

    url = 'http://10.122.66.105/NAVL/Default.aspx?vp=searchbbpartdetail&p=' + PN
    response = session.get(url, headers=headers).text
    tree = etree.HTML(response)

    projectname = tree.xpath("//*[@id='VP_GvAvlProj']/td[2]/a/text()")
    num = len(projectname)
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame({"projectname": projectname})
    return df, num
