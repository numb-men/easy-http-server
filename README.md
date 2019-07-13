# easy-http-server
a easy http server by python / 一个python写的简单的http server

python版本：2.7.15

easy_http_server_1.py实现了一个简单的静态服务器，通过在static/目录下放置文件，就可以通过浏览器对该文件进行访问。同时它还能解析http request请求。
代码精简，很适合用来学习http协议。

运行：python easy_http_server_1.py

访问：`http://127.0.0.1:8080/index.html`
`http://127.0.0.1:8080/img/img_1.jpg`
...
以及其他任何您添加到static/下的文件
