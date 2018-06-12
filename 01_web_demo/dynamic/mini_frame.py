import re
import pymysql
import urllib.parse
import logging


URL_FUNC_DICT = dict()
"""
URL_FUNC_DICT = {
        "/index.py" : index,
        "/center.py" : center,
        }
"""
# func_list = list()

def route(url):
    def set_func(func):
        # func_list.append(func)
        URL_FUNC_DICT[url] = func
        def call_func(*args, **kwargs):
            return func(*args, **kwargs)
        return call_func
    return set_func


@route(r"/index.html")
def index(ret):
    with open("./templates/index.html") as f:
        content = f.read()
    # my_stock_info = "这里是从mysql中查询出来的数据2..."
    # content =  re.sub(r"\{%content%\}",my_stock_info, content)


    conn = pymysql.connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
    cursor = conn.cursor()
    cursor.execute("select * from info;")
    stock_info = cursor.fetchall()
    cursor.close()
    conn.close()
    tr_template = """<tr>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>
    <input type="button" value="添加" id="toAdd" name="toAdd" systemidvaule="%s">
    </td>
    </tr>
    """
    html = ""
    for line_info in stock_info:
        html += tr_template % (line_info[0],line_info[1],line_info[2],line_info[3],line_info[4],line_info[5],line_info[6],line_info[7],line_info[1])
    content =  re.sub(r"\{%content%\}",html, content)
    return content


@route(r"/center.html")
def center(ret):
    with open("./templates/center.html") as f:
        content = f.read()
    # my_stock_info = "这里是从mysql中查询出来的数据..."

    conn = pymysql.connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
    cursor = conn.cursor()
    cursor.execute("select i.code , i.short , i.chg, i.turnover, i.price, i.highs , f.note_info  from info as i inner join focus as f on i.id = f.info_id;")
    stock_info = cursor.fetchall()
    cursor.close()
    conn.close()
    tr_template = """<tr>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>%s</td>
    <td>
        <a type="button" class="btn btn-default btn-xs" href="/update/%s.html"> <span class="glyphicon glyphicon-star" aria-hidden="true"></span> 修改 </a>
    </td>
    <td>
        <input type="button" value="删除" id="toDel" name="toDel" systemidvaule="%s">
    </td>
    </tr>
    """
    html = ""
    for line_info in stock_info:
        html += tr_template % (line_info[0],line_info[1],line_info[2],line_info[3],line_info[4],line_info[5],line_info[6],line_info[0],line_info[0])
    content =  re.sub(r"\{%content%\}",html, content)
    return content 


@route(r"/add/(\d+).html")
def add_focus(ret):
    # print("add_fouces")
    # 1. 获取股票code
    stock_code = ret.group(1)
    # 2.判断是否已经有这只股票
    conn = pymysql.connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
    cursor = conn.cursor()
    cursor.execute("select * from info where code = %s;", (stock_code, ))
    # 如果没有这个股票代码, 那么就任务是非法请求
    if not  cursor.fetchone():
        cursor.close()
        conn.close()
        return "没有这支股票,..大哥, 我们是创业公司, 请手下留情...."

    #3.判断是否已经关注过
    cursor.execute("""select * from info as i inner join focus as f on i.id=f.info_id where i.code=%s;""", (stock_code , ))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return "已经关注过这支股票了....不用再点了"
    
    #4.添加关注
    cursor.execute("insert into focus (info_id) select id from info where code = %s;" , (stock_code , ))
    conn.commit()
    cursor.close()
    conn.close()
    return "添加成功"


@route(r"/del/(\d+).html")
def del_focus(ret):
    # 1. 获取股票code
    stock_code = ret.group(1)

    # 2.判断是否已经有这只股票
    conn = pymysql.connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
    cursor = conn.cursor()
    cursor.execute("select * from info where code = %s;", (stock_code, ))
    # 如果没有这个股票代码, 那么就任务是非法请求
    if not  cursor.fetchone():
        cursor.close()
        conn.close()
        return "没有这支股票,..大哥, 我们是创业公司, 请手下留情...."

    #3.判断是否已经关注过
    cursor.execute("""select * from info as i inner join focus as f on i.id=f.info_id where i.code=%s;""", (stock_code , ))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return "%s之前就没有关注过这支股票了....请勿取消关注" % stock_code
    
    #4.取消关注
    cursor.execute("delete from focus where info_id =(select id from info where code = %s);" , (stock_code , ))
    conn.commit()
    cursor.close()
    conn.close()
    return "取消成功"

@route(r"/update/(\d+)\.html")
def show_update_page(ret):
    """显示修改的那个页面"""
    # 1.获取股票代码
    stock_code = ret.group(1)
    # 2.打开模板
    with open("./templates/update.html") as f:
        content = f.read()
    # 3. 根据股票信息查询相关信息
    conn = pymysql.connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
    cursor = conn.cursor()
    cursor.execute("select f.note_info from focus as f inner join info as i on i.id=f.info_id where i.code=%s;", (stock_code, ))
    stock_info = cursor.fetchone()
    note_info = stock_info[0] # 获取这支股票的备注信息
    cursor.close()
    conn.close()

    content =  re.sub(r"\{%note_info%\}",note_info, content)
    content =  re.sub(r"\{%code%\}",stock_code, content)

    return content 


@route(r"/update/(\d+)/(.*)\.html")
def save_stock_info(ret):
    print("save_stock_info")
    stock_code = ret.group(1)
    comment = ret.group(2)
    comment = urllib.parse.unquote(comment)
    conn = pymysql.connect(host='localhost',port=3306,user='root',password='mysql',database='stock_db',charset='utf8')
    cursor = conn.cursor()
    cursor.execute("update focus set note_info=%s where info_id = (select id from info where code=%s)", (comment,stock_code))
    conn.commit()
    cursor.close()
    conn.close()
    return "修改成功...."


def application(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html;charset=utf-8')])
    file_name = environ['PATH_INFO']
    """
    if file_name == "/index.py":
        return index()
    elif file_name == "/center.py":
        return center()
     """  
    logging.basicConfig(level=logging.WARNING,filename='./log.txt',filemode='a',format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')  
    logging.info("访问的是:%s" % file_name)
    # return URL_FUNC_DICT[file_name]()    
    for url , func  in URL_FUNC_DICT.items():
        # print("---url = %s " % url)
        ret = re.match(url,file_name)
        if ret:
            return func(ret)
    else:
        return "请求的rul(%s)没有对应的函数..." % file_name            

            



