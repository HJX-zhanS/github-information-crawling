github information crawling
===========================

## Operating environment

Python3 + MySQL


## How to run this program?
1.Recovery the database "github_info" to the your computer, then modify pool=PooledDB(pymysql,50,host='localhost',user='root',passwd='123456',db='github_info',port=3306,charset="utf8"). The user is the username of your database, the passwd is the password of your database.
<br>2.Run this program after 1.


## Explain
The information I need to collect is shown in these 2 figures. One is the project information, another is the user information.
<br>
<br>

* `This is the project information.`
![image](https://github.com/HJX-zhanS/github-information-crawling/blob/master/projectinfo.png)
 <br>
 <br>
 
* `This is the user information.`
![image](https://github.com/HJX-zhanS/github-information-crawling/blob/master/userinfo.png)
 
 
Actually,the relationship amount users is a graph. This graph is shown as below.
![image](https://github.com/HJX-zhanS/github-information-crawling/blob/master/userrelationship.jpg)
