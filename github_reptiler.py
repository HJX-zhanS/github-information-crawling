import requests
import lxml
from bs4 import BeautifulSoup
import datetime
import queue
import pymysql
from DBUtils.PooledDB import PooledDB
import time
import json

pool=PooledDB(pymysql,50,host='localhost',user='root',passwd='123456',db='github_info',port=3306,charset="utf8")
q=queue.Queue()
login_cookies=''
header={'Connection': 'close'}

def tryAgain(linkstr):
    trycount = 0;
    while trycount < 3:
        try:
            response = requests.get(linkstr, headers=header)
            trycount = 10
            break
        except Exception as e:
            time.sleep(6)
            print(e)
        trycount = trycount + 1
    return (response,trycount)

def login():
    username = 'HJX-zhanS'
    password = 'Gtr19961127'
    r1 = requests.get('https://github.com/login')
    soup = BeautifulSoup(r1.text, features='lxml')
    s1 = soup.find(name='input', attrs={'name': 'authenticity_token'}).get('value')
    r1_cookies = r1.cookies.get_dict()
    r2 = requests.post(
        'https://github.com/session',
        data={
            'commit': 'Sign in',
            'utf8': '✓',
            'authenticity_token': s1,
            'login': username,
            'password': password
        },
        cookies=r1.cookies.get_dict(),
    )
    return r2.cookies.get_dict()

def deleteBackup():
    conn = pool.connection()
    cur = conn.cursor()
    sqlstr = "delete from queue_backup"
    try:
        cur.execute(sqlstr)
        conn.commit()
    except Exception as e:
        print(e)
    cur.close()
    conn.close()

def backup():
    global q
    bq=queue.Queue()
    while not q.empty():
        conn = pool.connection()
        cur = conn.cursor()
        URL=q.get()
        bq.put(URL)
        sqlstr = "insert into queue_backup(URL) values('%s')"%(URL)
        try:
            cur.execute(sqlstr)
            conn.commit()
        except Exception as e:
            print(e)
        cur.close()
        conn.close()
    q=bq

def recovery():
    global q
    conn = pool.connection()
    cur = conn.cursor()
    sqlstr = "select URL from queue_backup"
    try:
        cur.execute(sqlstr)
        results=cur.fetchall()
    except Exception as e:
        print(e)
    cur.close()
    conn.close()
    if len(results)>0:
        for i in results:
            q.put(i[0])
        return 1
    else:
        return 0

def getAbstracts(soup):
    # 获取关键词
    abstract=''
    abstracts = soup.find(name='div', attrs={'class': 'list-topics-container'})
    if abstracts!=None:
        abstracts=abstracts.find_all(name='a')
        for i in abstracts:
            str = i.string.replace('\n', '')
            str = str.replace(' ', '')
            abstract = abstract + '/' + str
    return abstract

def getNo(rawinfo):
    #获取如watch等的数目
    No=-1
    rawinfo = rawinfo[len(rawinfo)-1].string
    if rawinfo!=None:
        rawinfo=rawinfo .replace('\n', '')
        rawinfo = rawinfo.replace(' ', '')
        if rawinfo.find(',')!=-1:
            rawinfo = rawinfo.replace(',', '')
        try:
            No = int(rawinfo)
        except Exception as e:
            print(e)
            No=-1
    return No

def getWSInfo(soup):
    #获取watch、star、fork的数量以及链接
    result=soup.find(name='ul', attrs={'class': 'pagehead-actions'}).find_all(name='li')
    Wat_No = 0
    Star_No = 0
    Fork_No = 0

    Wat_Link = 'https://github.com'
    Star_Link = 'https://github.com'

    str=result[0].find_all(name='a')
    Wat_Link = Wat_Link + str[1]['href']
    Wat_No = getNo(str)

    str = result[1].find_all(name='a')
    Star_Link = Star_Link + str[1]['href']
    Star_No = getNo(str)

    return (Wat_No,Star_No,Fork_No,Wat_Link,Star_Link)

def getCBRC(soup):
    #获取commits、branches、release、contributors的数量
    result=soup.find(name='ul', attrs={'class': 'numbers-summary'})
    Com_No = -1
    Bran_No = -1
    Rel_No = -1
    Con_No = -1
    if result!=None:
        result=result.find_all(name='li')
        str = result[0].find_all(name='span')
        Com_No = getNo(str)

        str = result[1].find_all(name='span')
        Bran_No = getNo(str)

        str = result[2].find_all(name='span')
        Rel_No = getNo(str)

        str = result[3].find_all(name='span')
        Con_No = getNo(str)

    return (Com_No,Bran_No,Rel_No,Con_No)

def getLastCommitTime(soup):
    Last_Com_Time=-1
    result = soup.find(name='span', attrs={'itemprop': 'dateModified'})
    if result!=None:
        result=result.find_all(name='relative-time')
        Last_Com_Time=result[0]['datetime']
        Last_Com_Time=Last_Com_Time.replace('T',' ')
        Last_Com_Time = Last_Com_Time.replace('Z', ' ')
    return Last_Com_Time

def getUserLinkFromProject(Wat_Link,Star_Link):
    global q
    links=(Wat_Link,Star_Link)
    index=0
    for i in links:
        request=i
        while request!=None:
            print(request)
            result=tryAgain(request)
            response=result[0]
            trycount=result[1]
            if trycount==10:
                soup = BeautifulSoup(response.text, features='lxml')
                users = soup.find_all(name='h3', attrs={'class': 'follow-list-name'})
                nextlink = None
                if users != []:
                    if index == 0:
                        nextlink = soup.find(name='a', attrs={'class': 'next_page'})
                    if index == 1:
                        nextlink = soup.find(name='div', attrs={'class': 'BtnGroup'})
                        if nextlink != None:
                            nextlink = nextlink.find_all(name='a')
                            if nextlink[len(nextlink) - 1].string == 'Next':
                                nextlink = nextlink[len(nextlink) - 1]
                            else:
                                nextlink = None
                    if nextlink != None and index == 0:
                        nextlink = 'https://github.com' + nextlink['href']
                    if nextlink != None and index == 1:
                        nextlink = nextlink['href']
                    time.sleep(3)
                    for j in users:
                        Id = int(j.find(name='a')['data-hovercard-url'].replace('/hovercards?user_id=', ''))
                        UName = j.find(name='a').string
                        conn = pool.connection()
                        cur = conn.cursor()
                        sqlstr = 'insert into user_info(Id,UName) values(%d,"%s")' % (Id, UName)
                        try:
                            cur.execute(sqlstr)
                            conn.commit()
                        except Exception as e:
                            print(e)
                        cur.close()
                        conn.close()
                        link = 'https://github.com'
                        link = link + j.find(name='a')['href']
                        q.put(link)
                request = nextlink
        index=index+1

def getProjectInfo(linkstr,UId):
    index=0
    while index<5:
        result=tryAgain(linkstr)
        response=result[0]
        trycount=result[1]
        if trycount==10:
            soup = BeautifulSoup(response.text, features='lxml')
            # author = soup.find(name='span', attrs={'itemprop': 'author'}).find(name='a').string
            info = soup.find(name='strong', attrs={'itemprop': 'name'})
            if info!=None:
                projectname=info.find(name='a').string
                abstract = getAbstracts(soup)
                WSResult = getWSInfo(soup)

                Wat_No = WSResult[0]
                Star_No = WSResult[1]
                Fork_No = WSResult[2]

                Wat_Link = WSResult[3]
                Star_Link = WSResult[4]

                CBRCResult = getCBRC(soup)

                Com_No = CBRCResult[0]
                Bran_No = CBRCResult[1]
                Rel_No = CBRCResult[2]
                Con_No = CBRCResult[3]

                Last_Com_Time = getLastCommitTime(soup)

                conn = pool.connection()
                cur = conn.cursor()
                sqlstr = "insert into project_info(Pro_Name,Abstract,Wat_No,Star_No,Fork_No,Com_No,Bran_No,Rel_No,Con_No,Last_Com_Time) values('%s','%s',%d,%d,%d,%d,%d,%d,%d,'%s')" % (
                    projectname, abstract, Wat_No, Star_No, Fork_No, Com_No, Bran_No, Rel_No, Con_No, Last_Com_Time)
                try:
                    cur.execute(sqlstr)
                    conn.commit()
                except Exception as e:
                    print(e)

                sqlstr = "select Id from project_info where Pro_Name='%s'" % (projectname)
                try:
                    cur.execute(sqlstr)
                    result = cur.fetchall()
                except Exception as e:
                    print(e)

                PId = result[0][0]

                sqlstr = "insert into user_project_info(UId,PId) values(%d,%d)" % (UId, PId)
                try:
                    cur.execute(sqlstr)
                    conn.commit()
                except Exception as e:
                    print(e)

                cur.close()
                conn.close()
                getUserLinkFromProject(Wat_Link, Star_Link)
                index=5
        index=index+1

def getUserLinkFromUserInfo(Followers_Link,Following_Link):
    links=(Followers_Link,Following_Link)
    for i in links:
        request=i
        while request!=None:
            result=tryAgain(request)
            response=result[0]
            trycount=result[1]
            if trycount==10:
                soup = BeautifulSoup(response.text, features='lxml')
                nextlink = soup.find(name='div', attrs={'class': 'BtnGroup'})
                if nextlink != None:
                    nextlink = nextlink.find_all(name='a', attrs={'rel': 'nofollow'})
                    nextlink = nextlink[len(nextlink) - 1]
                    if nextlink != None and nextlink.string == 'Next':
                        nextlink = nextlink['href']
                    else:
                        nextlink = None
                time.sleep(3)
                info = soup.find_all(name='div', attrs={
                    'class': 'd-table table-fixed col-12 width-full py-4 border-bottom border-gray-light'})
                for j in info:
                    info1 = j.find(name='a', attrs={'class': 'd-inline-block no-underline mb-1'})
                    str = info1['data-hovercard-url']
                    Id = str[str.find('=') + 1:len(str)]
                    Id = int(Id)
                    info1 = info1.find_all(name='span')
                    UName = info1[len(info1) - 1].string
                    conn = pool.connection()
                    cur = conn.cursor()
                    sqlstr = 'insert into user_info(Id,UName) values(%d,"%s")' % (Id, UName)
                    try:
                        cur.execute(sqlstr)
                        conn.commit()
                    except Exception as e:
                        print(e)
                    cur.close()
                    conn.close()
                request = nextlink

def getRepoInfo(Repo,UId):
    request=Repo
    while request != None:
        print(request)
        result=tryAgain(request)
        response=result[0]
        trycount=result[1]
        if trycount==10:
            soup = BeautifulSoup(response.text, features='lxml')
            nextlink = soup.find(name='div', attrs={'class': 'BtnGroup'})
            if nextlink!=None:
                nextlink=nextlink.find_all(name='a', attrs={'rel': 'nofollow'})
                nextlink = nextlink[len(nextlink) - 1]
                if nextlink != None and nextlink.string == 'Next':
                    nextlink = nextlink['href']
                else:
                    nextlink=None
            time.sleep(3)
            info = soup.find(name='div', attrs={'id': 'user-repositories-list'})
            if info!=[]:
                info=info.find_all(name='li')
            for i in info:
                projectlink='https://github.com'
                projectlink = projectlink+i.find(name='h3').find(name='a')['href']
                getProjectInfo(projectlink, UId)
            request = nextlink

def BSF():
    global q,login_cookies
    Summarize=''
    Location=''
    Email=''
    URL=''
    Organizations=''
    while not q.empty():
        userlink=q.get()
        trycount=0
        while trycount<3:
            try:
                request=requests.get(
                    userlink,
                    cookies=login_cookies
                )
                trycount=10
                break
            except Exception as e:
                time.sleep(6)
                print(e)
            trycount=trycount+1

        if trycount==10:
            soup = BeautifulSoup(request.text, features='lxml')
            userinfo = soup.find_all(name='div', attrs={'class': 'd-none d-md-block'})
            for i in userinfo:
                result = i.find(name='div', attrs={'class': 'js-profile-editable-area'})
                if result != None:
                    userinfo = i
                    break

            Summarize = userinfo.find(name='div', attrs={'class': 'p-note user-profile-bio js-user-profile-bio'})
            if Summarize!=None:
                Summarize=Summarize.find(name='div')
                if Summarize!=None:
                    Summarize=Summarize.string
                else:
                    Summarize=''
            else:
                Summarize=''

            Location = userinfo.find(name='li', attrs={'itemprop': 'homeLocation'})
            if Location!=None:
                Location=Location.find(name='span')
                if Location!=None:
                    Location=Location.string
                else:
                    Location=''
            else:
                Location=''

            Email = userinfo.find(name='li', attrs={'itemprop': 'email'})
            if Email!=None:
                Email=Email.find(name='a', attrs={'class': 'u-email'})
                if Email!=None:
                    Email=Email.string
                else:
                    Email=''
            else:
                Email=''

            URL = userinfo.find(name='li', attrs={'itemprop': 'url'})
            if URL!=None:
                URL=URL.find(name='a')
                if URL!=None:
                    URL=URL.string
                else:
                    URL=''
            else:
                URL=''

            orginfo = soup.find_all(name='a', attrs={'class': 'avatar-gr oup-item'})
            for i in orginfo:
                Organizations = Organizations + i['aria-label'] + '/'

            user_id = soup.find(name='nav', attrs={'class': 'UnderlineNav-body'}).find(name='a')['data-hydro-click']
            user_id = json.loads(user_id)
            user_id = int(user_id['payload']['profile_user_id'])

            Rep_No=-1
            Pro_No=-1
            Star_No=-1
            Followers_No=-1
            Following_No=-1

            Rep_Link = 'https://github.com'
            Followers_Link = 'https://github.com'
            Following_Link = 'https://github.com'
            infostr = soup.find(name='nav', attrs={'class': 'UnderlineNav-body'}).find_all(name='a')
            for i in infostr:
                tempstr = i.text.replace("\n", '')
                number = i.find(name='span')
                if number != None:
                    number = number.string.replace('\n', '').replace(' ', '')
                if "Repositories" in tempstr:
                    Rep_No = number
                    Rep_Link = Rep_Link + i['href']
                if "Projects" in tempstr:
                    Pro_No = number
                if "Stars" in tempstr:
                    Star_No = number
                if "Followers" in tempstr:
                    Followers_No = number
                    Followers_Link = Followers_Link + i['href']
                if "Following" in tempstr:
                    Following_No = number
                    Following_Link = Following_Link + i['href']
            Contributions = soup.find(name='div', attrs={'class': 'js-yearly-contributions'}).find(name='h2').string
            Contributions = Contributions.replace('\n', '')

            conn = pool.connection()
            cur = conn.cursor()
            sqlstr = "select count(1) from user_info where Id=%d"%(user_id)
            try:
                cur.execute(sqlstr)
                count=cur.fetchall()
            except Exception as e:
                print(e)
            nickname = ''
            locker=0
            nickname = soup.find(name='span', attrs={'itemprop': 'additionalName'})
            if nickname != None:
                nickname = nickname.string

            if count[0][0]==0:
                unmame = soup.find(name='h1', attrs={'class': 'vcard-names'})
                unmame = unmame.find(name='span', attrs={'itemprop': 'name'})
                if unmame != None:
                    unmame = unmame.string
                    if unmame != '':
                        sqlstr = "insert into user_info(Id,UName) values(%d,'%s')"%(user_id,unmame)
                        try:
                            cur.execute(sqlstr)
                            conn.commit()
                        except Exception as e:
                            locker=1
                            print(e)
                    else:
                        locker=1
                else:
                    locker=1

            if locker==0:
                sqlstr = "update user_info set Nickname='%s',Summarize='%s',Location='%s',Email='%s',URL='%s',Organizations='%s',Rep_No='%s',Pro_No='%s',Star_No='%s',Followers_No='%s',Following_No='%s',Contributions='%s' where Id=%d" % (nickname,
                Summarize, Location, Email, URL, Organizations, Rep_No, Pro_No, Star_No, Followers_No, Following_No,
                Contributions, user_id)
                try:
                    cur.execute(sqlstr)
                    conn.commit()
                except Exception as e:
                    print(e)



            cur.close()
            conn.close()

            getRepoInfo(Rep_Link,user_id)
            getUserLinkFromUserInfo(Followers_Link,Following_Link)

            deleteBackup()
            backup()

def start(linkstr):
    result = recovery()
    if result==0:
        #以sqlmap项目作为起点，获取该项目的watch、star的用户
        r1 = requests.get(linkstr)
        soup = BeautifulSoup(r1.text, features='lxml')
        WSResult = getWSInfo(soup)

        Wat_Link = WSResult[3]
        # Star_Link = None
        Star_Link = WSResult[4]
        getUserLinkFromProject(Wat_Link,Star_Link)
    BSF()
    print('it is over')

def main():
    global login_cookies
    login_cookies=login()
    Start_Link='https://github.com/sqlmapproject/sqlmap'
    start(Start_Link)

if __name__ == "__main__":
    main()