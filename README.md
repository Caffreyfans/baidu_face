# face identity for [Home Assistant](https://home-assistant.io)  

程序可能存在 BUG,如有任何问题请提出我会在第一时间解决。
    
![演示](https://raw.githubusercontent.com/Caffreyfans/baidu_identity/master/gif/demo.gif)

## 版本更新提示
---
> **2019-05-25**<br />
> 现已适配 0.92.0 之后版本请注意使用最新代码

## 使用
下载插件, 并将 baidu_face 放置于 custom_components 文件夹下

## 配置示例 :
```YAML
sensor:
  - platform : baidu_face
    api_key : "*************"
    secret_key: "***********"
    group_list: "['myself', 'family']" # 格式例子
    camera_entity_id: "*****"    
    token: "****************"
    # liveness: "NORMAL"
    # name: "ren lian shi bie"
    # port: 8123
    # pic_url: "网络、本地图片地址"
    scan_interval: 2
```

| 参数 | 必选 | 类型 | 说明 |
|---|---|---|---|
| api_key | 是 | string | 百度人脸识别应用 **API Key** |
| secret_key | 是 | string | 百度人脸识别应用 **Secret Key** |
| group_list | 是 | string | 人脸库用户组**组名** (1~10) 个之内|
| camera_entity_id | 是 | string | ha 中摄像头实体 **id** |
| token | 是 | string | ha 中永久令牌 **token** |
| scan_interval | 是 | int | 每次检测检测时间<br> # 建议 **2**|
| liveness | 否 | string | 活体检测控制 <br> **NONE**: 不进行控制 <br> **LOW**:较低的活体要求(高通过率 低攻击拒绝率) <br> **NORMAL**: 一般的活体要求(平衡的攻击拒绝率, 通过率) <br> **HIGH**: 较高的活体要求(高攻击拒绝率 低通过率) <br> 默认: **NORMAL** <br> 若活体检测结果不满足要求，则返回结果中会提示活体检测失败 |
| name | 否 | string | 该实体名 <br> # 默认: **"ren lian shi bie"**|
| port | 否 | int | ha 设定的端口号 <br> # 默认: **8123**|
| pic_url | 否 | string | 识别失败时显示的图片 <br> # 默认: **魔方gif图** |
