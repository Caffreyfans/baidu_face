# face identity for [Home Assistant](https://home-assistant.io)
TODO: add face identity sensor 

    
## 使用
下载插件, 并将 baidu_face.py 放置于 custom_components/sensor 文件夹下

## 配置示例 :
```YAML
sensor:
  - platform : baidu_face
    # 必须项
    #从百度ai开放平台人脸识别应用中获取
    api_key : "*************"
    secret_key: "***********"
    group_id: "*************"
    #摄像头entity_id
    camera_entity_id: "*****"    
    # token
    token: "****************"
    #刷新间隔(1~30s)
    scan_interval: 2
    # 可选项
    # name: "***************"
    # port: 8123
    # pic_url: "网络、本地图片地址"
```

![演示](https://raw.githubusercontent.com/Caffreyfans/baidu_identity/master/gif/demo.gif)
