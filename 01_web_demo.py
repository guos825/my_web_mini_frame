import socket 
import re
import multiprocessing
import time
#import dynamic.mini_frame
import sys

class WSGIService(object):


    def __init__(self, port, app, static_path):
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(("" , port))
        self.tcp_socket.listen(128)
        self.application = app
        self.static_path = static_path

    
    def service_client(self , new_socket):
        request = new_socket.recv(1024).decode("utf-8")
        request_list = request.splitlines()
        
        ret = re.match(r"[^/]+(/[^ ]*)", request_list[0])
        if ret:
            file_name = ret.group(1)
            if file_name == "/":
                file_name = "/index.html"
            print(file_name)
#        print(request)
        
        # 如果请求的资源不是以.py 结尾的. 那么就认为是静态资源
        if not file_name.endswith(".html"): 
            try:
                f = open(self.static_path+ file_name, "rb")
            except:
                response = "HTTP/1.1 404 NOT FOUND\r\n"
                response += "\r\n"
                response += "---file not found---"
                new_socket.send(response.encode("utf-8"))
            else:
                html_content = f.read()
                f.close()
                response = "HTTP/1.1 200 OK\r\n"
                response += "\r\n"
                new_socket.send(response.encode("utf-8"))
                new_socket.send(html_content)
                
        else:
            # 如果以.py 结尾, 那么就认为是动态资源的请求
            # body = mini_frame.login()
            # body = mini_frame.application(file_name)
            env = dict()
            env['PATH_INFO'] = file_name
            # body = dynamic.mini_frame.application(env ,self.set_response_header)
            body = self.application(env ,self.set_response_header)
            header = "HTTP/1.1 %s\r\n" % self.status
            for temp in self.headers:
                header += "%s:%s\r\n" % (temp[0], temp[1])

            header += "\r\n"
            response = header + body
            new_socket.send(response.encode("utf-8"))

        new_socket.close()

    def set_response_header(self,status,headers):
        self.status = status
        self.headers = [("server", "mini_web v8.8")]
        self.headers += headers

    def run_forever(self):
        while True:
            new_socket , client_addr = self.tcp_socket.accept()
            p = multiprocessing.Process(target = self.service_client , args = (new_socket , ))
            # service_client(new_socket)
            p.start()
            new_socket.close()
        self.tcp_socket.close()



def main():
    if len(sys.argv) ==3:
        try:
            port = int(sys.argv[1]) # 端口号
            frame_app_name = sys.argv[2] # mini_frame:application
        except Exception as ret:
            print("端口号有误....")
            return
    else:
        print("请按照以下方式运行:")
        print("python3 xxx.py 端口号 框架名...")
        return
    




    ret = re.match(r"([^:]+):(.*)",frame_app_name)
    if ret:
        frame_name = ret.group(1) # mini_frame
        app_name = ret.group(2) # application
    else:
        print("请按照以下方式运行:")
        print("python3 xxx.py 端口号 框架名...")
        return

    with open("./web_server.conf") as f:
        conf_info = eval(f.read())

    # 增加目录的上一级
    sys.path.append(conf_info['dynamic_path'])
    frame = __import__(frame_name) # 返回值标记的这个导入的OK
    app = getattr(frame, app_name)# 此时app 只想了dynamic中的application函数
    # print(app)

    wsgi_server = WSGIService(port, app, conf_info['static_path'])
    wsgi_server.run_forever()

if __name__ == "__main__":
    main()
