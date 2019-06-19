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
<br>
So the way of collecting the users of github is to do the traversal of graph. It is easy. Howerver, there are some problems need to be solved.
<br>1. If the program terminates unexpectedly, how can we restore to the state before termination?
<br>2. How to deal with anti-crawler mechanism?
<br>3. After a period of time, the program will fail to connect.
<br>
### 1. If the program terminates unexpectedly, how can we restore to the state before termination?
The inforamtion crawling is a stateless work. So if the program terminates unexpectedly, we have to restart. However, the number of users is huge. So it is unwise to restart it. In this program, I design two function to deal with this problem. They are the `backup()` and the `recovery()`. The `backup()` is to record the `queue`. And the `recovery()` is to recover the `queue` from database.
### 2. How to deal with anti-crawler mechanism?
The answer to let the program sleep 3s.
### 3. After a period of time, the program will fail to connect.
I use the function `tryagain()` to deal with this problem. It is shown as follows. In this function, the program will try to connect the linkstr 3 times. If the connection is successful, the `trycount` will be set to 10 (10 only is a state). Then this function will return (response,trycount).
```
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
 ```
### 4. Describe
This program starts at the function `start()`. Firstly, it will call the `recovery()` to decide whether the `back_queue` is null. If the `back_queue` is null, it will start at project `sqlmap`. Otherwise it will recover the `queue`. In the function `BSF()`, each iteration will do :
<br>
(1) connect one user link to collect the information of this user.
<br>
(2) add the user links from the `Followers` and the `Following` to the `queue`.
<br>
(3) connect this user' s `Repositories` to collect the project information.
<br> 
(4)collect user links from the `Star` and `Watch` of each project of the `repositories` of this user.
