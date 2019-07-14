# -*- coding:utf-8 -*-
import socket
import os
import re

"""
一个静态和动态web服务器，简单的http server
可插拔的插件添加，语义化的路由

作者：衡与墨 www.hengyumo.cn
2019-7-14 新建
"""

class Server:
    """ 使用init初始化，由host和port生成http server，
    """
    def __init__(self, init=None, host='localhost', port=6060):
        self.host = host
        self.port = port
        self.init = init
        self.plugins = None

        self.isEnd = False
        self.conn = None
        self.addr = None
        self.request = None
        self.response = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))

        # 执行init，只执行一次
        if self.init:
            self.init.run(self)

    def addPlugin(self, plugins):
        self.plugins = plugins

        # 执行插件的初始化
        if self.plugins:
            self.plugins.init(self)

    def accept(self):
        self.socket.listen(3)
        self.conn, self.addr = self.socket.accept()

    def run(self, handle=None):

        print '===== easy-http-server 0.1.2 %s %d =====' % (self.host, self.port)

        self.handle = handle

        while True:
            self.isEnd = False
            self.accept()
            self._handle()
            if (not self.isEnd):
                self.end()


    def _handle(self):
        request_content = self.conn.recv(1024)

        # 没有内容的连接，防止keep-alive导致错误断开
        try:
            self.request = self.parseRequest(request_content)
        except Exception as e:
            print e
            self.end()

        print self.request['method'], self.request['url']

        self.createResponse()

        # 执行插件
        if self.plugins:
            self.plugins.run(self)

        # 执行handle
        if not self.isEnd and self.handle:
            self.handle.run(self)


    def end(self, data=''):
        self.conn.sendall(self.packResponse(data))
        self.conn.close()
        self.isEnd = True

    def parseRequest(self, request_content):
        """ 解析请求数据
        """
        request_split = request_content.split('\r\n')

        # 请求行
        method, url, http_version = request_split[0].split(' ')

        # 请求头
        request_headers = {}
        for i in range(1, len(request_split)):
            if request_split[i] == '':
                break
            else:
                key, value = request_split[i].split(': ')
                request_headers[key] = value

        # 请求数据
        request_body = []
        for i in range(2+len(request_headers), len(request_split)):
            request_body.append(request_split[i])

        request_body = '\r\n'.join(request_body)

        # 打包成请求字典
        request = {
            'method': method,
            'url': url,
            'http_version': http_version,
            'headers': request_headers,
            'body': request_body
        }

        return request

    def createResponse(self):
        """ 生成响应对象
        """
        self.response = {
            'status': 200,
            'headers': {},
            'data': ''
        }

    def addHeader(self, key, value):
        """ 添加响应header
        """
        self.response['headers'][key] = value


    def packResponse(self, data):
        """ 打包响应内容
        """
        responseString = 'HTTP/1.1 %d OK\r\n' % self.response['status']
        headerString = '\r\n'.join(['%s: %s' % (key, self.response['headers'][key])
            for key in self.response['headers']])
        responseString += '%s\r\n\r\n%s' % (headerString, data)

        return responseString

class Initiator:
    def __init__(self):
        self.init_funs = []

    def add(self, init_fun):
        self.init_funs.append(init_fun)

    def run(self, server):
        for init_fun in self.init_funs:
            init_fun(server)


class Handle:
    def __init__(self):
        self.handle_funs = []

    def add(self, handle_fun):
        self.handle_funs.append(handle_fun)

    def run(self, server):
        for handle_fun in self.handle_funs:
            handle_fun(server)
            if server.isEnd:
                break

class Plugins:
    def __init__(self):
        self.plugins = []

    def add(self, plugin):
        self.plugins.append(plugin)

    def init(self, server):
        for plugin in self.plugins:
            plugin.init(server)

    def run(self, server):
        for plugin in self.plugins:
            if server.isEnd:
                break
            plugin.run(server)

class RouterPlugin:
    def __init__(self):
        self.routes = {
            'GET': {},
            'POST': {},
            'PUT': {},
            'DELETE': {}
        }

    def addRoute(self, method, url, handle):
        self.routes[method][url] = handle

    def get(self, url, handle):
        self.addRoute('GET', url, handle)

    def post(self, url, handle):
        self.addRoute('POST', url, handle)

    def put(self, url, handle):
        self.addRoute('PUT', url, handle)

    def delete(self, url, handle):
        self.addRoute('DELETE', url, handle)

    def init(self, server):
        print 'init router plugin'
        server.router = self
        server.get = self.get
        server.post = self.post
        server.put = self.put
        server.delete = self.delete

    def run(self, server):
        method = server.request['method']
        url = server.request['url']

        if method in self.routes:
            if url in self.routes[method]:
                self.routes[method][url](server)
                print 'match router plugin'
                return

        server.response['status'] = 404
        server.end(u'页面不存在'.encode('utf-8'))

class StaticPlugin:
    def __init__(self, files_dir='static'):
        self.files_dir = files_dir

    def init(self, server):
        # 必须实现init函数，只在初始化加载一次
        print 'init static plugin'
        server.statics = self.loadStatic(self.files_dir)

    def run(self, server):
        # 必须实现run函数，在每次获取到请求都执行
        self.handleStatic(server)

    def getFiles(self, files_dir):
        """ 获取某个路径所有的文件路径
        """
        files_dir = os.path.join(os.getcwd(), files_dir)
        files_all = []
        def get_files(files_dir='.', r_path=''):
            if files_dir[-1:] != '/':
                files_dir += '/'
            files = os.listdir(files_dir)
            for file in files:
                file_path = os.path.join(files_dir, file)
                if os.path.isdir(file_path):
                    get_files(file_path, file)
                else:
                    if r_path:
                        files_all.append('%s/%s' % (r_path, file))
                    else:
                        files_all.append(file)
        get_files(files_dir)
        return files_all

    def loadStatic(self, static_path):
        """ 加载静态文件
        """
        statics = self.getFiles(static_path)
        static_path = os.path.join(os.getcwd(), static_path)
        statics_dict = {}
        # 设置下列文件后缀使用二进制读取
        byte_files_suf = ('jpg', 'png')
        for file_name in statics:
            file_suf = file_name.split('.')[-1]
            file_path = os.path.join(static_path, file_name)
            if file_suf in byte_files_suf:
                file = open(file_path, 'rb')
            else:
                file = open(file_path, 'r')
            statics_dict['/'+file_name] = file.read()
            file.close()

        return statics_dict

    def handleStatic(self, server):
        """ 处理静态文件
        """
        request = server.request
        response = server.response
        statics = server.statics

        mime_type = {
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'html': 'text/html'
        }
        # 文件后缀名
        file_suf = request['url'].split('.')[-1]
        if file_suf in mime_type:
            content_type = mime_type[file_suf]
        else:
            content_type = 'text/html;charset=utf-8'

        server.addHeader('Content-Type', content_type)

        if request['url'] in statics:
            print 'match static plugin'
            server.end(statics[request['url']])

if __name__ == '__main__':

    # initiator = Initiator()
    # initiator.add(loadStatic)

    # server = Server(initiator)

    # handle = Handle()
    # handle.add(handleStatic)

    server = Server()

    # server.addPlugin(StaticPlugin()) 这样只能添加一个插件

    # 添加多个插件
    plugins = Plugins()
    # 静态路由支持
    plugins.add(StaticPlugin())
    # 动态路由支持
    plugins.add(RouterPlugin())

    server.addPlugin(plugins)

    # GET /hello
    server.get('/hello', lambda server: server.end('<h1>hello</h1>'))

    server.run()

"""
改进：
    1、将Initiator、Handle、Plugins内置到server里面，增加Model部分
    2、提供更友好的Router和service的分离体验
    3、将函数模块化分离
"""