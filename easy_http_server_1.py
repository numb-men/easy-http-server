# -*- coding:utf-8 -*-
import socket
import os
import re

"""
一个静态web服务器，简单的http server
作者：衡与墨 www.hengyumo.cn
2019-7-13 新建
"""

def parseRequest(request_content):
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
        'addr': addr,
        'method': method,
        'url': url,
        'http_version': http_version,
        'headers': request_headers,
        'body': request_body
    }

    return request

def get_files(files_dir='.'):
    """ 获取某个路径所有的文件路径
    """
    files_dir = os.path.join(os.getcwd(), files_dir)
    files_all = []
    def get_files_(files_dir='.', r_path=''):
        if files_dir[-1:] != '/':
            files_dir += '/'
        files = os.listdir(files_dir)
        for file in files:
            file_path = os.path.join(files_dir, file)
            if os.path.isdir(file_path):
                get_files_(file_path, file)
            else:
                if r_path:
                    files_all.append('%s/%s' % (r_path, file))
                else:
                    files_all.append(file)
    get_files_(files_dir)
    return files_all

def loadStatic(static_path='static'):
    """ 加载静态文件
    """
    statics = get_files(static_path)
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


if __name__ == '__main__':
    # 加载静态文件
    statics = loadStatic()

    # family: 套接字家族可以使AF_UNIX或者AF_INET
    # type: 套接字类型可以根据是面向连接的还是非连接分为SOCK_STREAM或SOCK_DGRAM
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 绑定地址（host,port）到套接字， 在AF_INET下,以元组（host,port）的形式表示地址。
    s.bind(('localhost', 8080))
    while(True):
        # 开始TCP监听。backlog指定在拒绝连接之前，操作系统可以挂起的最大连接数量。
        # 该值至少为1，大部分应用程序设为5就可以了。
        s.listen(3)
        # 被动接受TCP客户端连接,(阻塞式)等待连接的到来
        conn, addr = s.accept()
        # 接收TCP数据，数据以字符串形式返回，bufsize指定要接收的最大数据量。
        # flag提供有关消息的其他信息，通常可以忽略。
        request_content = conn.recv(1024)

        # 没有内容的连接，防止keep-alive导致错误断开
        try:
            request = parseRequest(request_content)
        except e:
            conn.close()
            break

        mime_type = {
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'html': 'text/html'
        }
        file_suf = request['url'].split('.')[-1]
        if file_suf in mime_type:
            content_type = mime_type[file_suf]
        else:
            content_type = 'text/html'

        response = 'HTTP/1.1 200 OK\r\nContent-Type:%s\r\n\r\n' % content_type

        print request['url']

        if request['url'] in statics:
            print 'match static'
            response += statics[request['url']]

        # 给客户端返回内容
        conn.sendall(response)
        # 关闭连接
        conn.close()