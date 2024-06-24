from lxml import etree
import re
from GetCookies import keep_seesion


def download_t3(i):
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 " \
                "Safari/537.36 "
    headers = {'User-Agent': userAgent}

    getVIEWSTATEurl = 'http://10.122.66.105/t3/Default.aspx?vp=viewlist'

    session = keep_seesion('T3')
    VIEWSTATE = etree.HTML(session.get(getVIEWSTATEurl, headers=headers).text).xpath(
        '//*[@id="__VIEWSTATE"]/@value')

    # get newest T3 url
    T3NameData = {
        'VP$ScriptManager1': 'VP$UpList|VP$TxtChassis',
        'VP$DdlChassis': '-1',
        'VP$TxtChassis': i,
        '__EVENTTARGET': 'VP$TxtChassis',
        '__VIEWSTATEGENERATOR': '42A6D4D6',
        '__VIEWSTATEENCRYPTED': '',
        '__ASYNCPOST': 'true',
        '__VIEWSTATE': VIEWSTATE[0]
    }
    response = session.post(getVIEWSTATEurl, headers=headers, data=T3NameData)
    try:
        getT3url = 'http://10.122.66.105' + etree.HTML(response.text).xpath('//*[@id="VP_GvList_ctl02"]/td[3]/a/@href')[0]

        # download
        response = session.get(url=getT3url, headers=headers)
        downloadLink = 'http://10.122.66.105/T3/' + etree.HTML(response.text).xpath('//*[@id="VP_HlExport"]/@href')[0]
        response = session.get(url=downloadLink, headers=headers)
        content_disposition = response.headers.get('Content-Disposition')
        pattern = r'filename=(.+)'
        filename = re.search(pattern, content_disposition).group(1).replace('%20', ' ')

        downloadpath = './T3sqlite/SourceT3list'
        with open(downloadpath + '/' + filename, 'wb') as file:
            file.write(response.content)

        print(f'T3文件已成功下载到 {downloadpath}\{filename}')
    except IndexError:
        pass