github information crawling
===========================

#中文：

1.将数据库"github_info"恢复到你本机的数据库中，然后修改代码中的pool=PooledDB(pymysql,50,host='localhost',user='root',passwd='123456',db='github_info',port=3306,charset="utf8")，将user和passwd分别改为你自己的数据库的用户名和密码。
2.直接运行程序即可

#English:

1.Recovery the database "github_info" to the your computer, then modify pool=PooledDB(pymysql,50,host='localhost',user='root',passwd='123456',db='github_info',port=3306,charset="utf8"). The user is the username of your database, the passwd is the password of your database.
2.Run this program after 1.


The information I need to collect is shown in these 2 figures. One is the project information, another is the user information.
 ![image](https://github.com/HJX-zhanS/github-information-crawling/blob/master/projectinfo.png)
 ![image](https://github.com/HJX-zhanS/github-information-crawling/blob/master/userinfo.png)
 
 
