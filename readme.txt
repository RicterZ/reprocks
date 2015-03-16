client : start socks5 proxy , and you can chose transmit the proxy or another service like Windows RDP to your computer.

server : run on your computer to supply the transmit service.you just need input 2 port number.

warning: This program just for test.

客户端 ：开启一个socks5代理，你可以选择把这个代理服务转发到你的机器上，或者一些其他的服务比如Windows远程桌面。 

服务端 ：在你自己的机器上运行，仅仅是提供一个转发的服务而已，你只需要提供两个端口号，第一个和客户端通信，第二个是转发后的端口号，你可以连接它达到连接到你所控制的机器上的服务。

reprocks_client.py和reprocks_server.py是python的源代码文件，它应该运行在你所控制的机器上，前提是安装了python。
windows 目录是用py2exe制作的windows下无需python的可执行文件，该目录下的所有文件在运行时都是必须的。所以需要一起上传。

reprocks_client.py的socks5代理默认绑定在50000端口上，你可以指定它，或者在python源文件中第12行将其修改。

注意：本程序只供研究测试使用。