# easy-http-server
a easy http server by python / 一个python写的简单的http server

python版本：2.7.15

---

## easy_http_server_1.py

实现了一个简单的静态服务器，通过在static/目录下放置文件，就可以通过浏览器对该文件进行访问。同时它还能解析http request请求。

代码精简，很适合用来学习http协议。

运行：python easy_http_server_1.py

访问：`http://127.0.0.1:8080/index.html`

`http://127.0.0.1:8080/img/img_1.jpg`

...

以及其他任何您添加到static/下的文件

---

## easy_http_server_2.py

一个静态和动态web服务器，简单的http server

对server进行了简单的封装，有微型框架的样子

可插拔的插件添加，语义化的路由

```
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

```
