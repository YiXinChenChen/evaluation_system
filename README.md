# medusa项目说明  

## 开发环境  
1. 安装django 1.9.5  
2. 在medusa文件夹下面创建dev_settings.py,dev_urls.py_文件  
3. dev_settings.py文件设置  
    DEBUG=False
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'subjective_test',
            'USER': 'subjective_test',
            'PASSWORD': '123456',
            'HOST': '172.19.101.12',
            'PORT': '',
        }
    }
4. 安装Apache  
5. 设置Apache的反向代理  
    <VirtualHost *:80>
        ServerName utest.yy.com
        ProxyPreserveHost On
        ProxyRequests Off
        <Proxy *>
            Order deny,allow
            Allow from all
        </Proxy>
        ProxyPass / http://127.0.0.1:8000/
        ProxyPassReverse / http://127.0.0.1:8000/
    </VirtualHost>
6. 设置hosts  
    127.0.0.1 utest.yy.com

## 部署
注意:assets的文件是通过Apache配置的,而不是通过django配置

## 浏览器兼容性

### 小屏幕(1280\*800)  
浏览器|版本|兼容性|
------|----|------|
IE9|9.0.8112.16421|OK|
IE10|10.0.9200.17457|OK|
IE11|11.0.9006.17843|OK|
Chrome|49.0.2623.112|OK|

### 中屏幕(1920\*1080)  
浏览器|版本|兼容性|
------|----|------|
IE9|9.0.8112.16421|OK|
IE10|10.0.9200.17457|OK|
IE11|11.0.9006.17843|OK|
Chrome|49.0.2623.110 m|OK|
FireFox|45.0.2|OK|
360浏览器|?|OK|
