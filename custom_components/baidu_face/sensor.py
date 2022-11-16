""" 利用百度人脸识别 APIv3 进行人脸识别. """
from homeassistant.components.sensor import PLATFORM_SCHEMA
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import logging
import requests
import time
import hass
from homeassistant.helpers.entity import Entity
import base64
from datetime import timedelta
from aip import AipFace
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_API_KEY,
    CONF_NAME,
    CONF_ENTITY_ID
)

_LOGGER = logging.getLogger(__name__)

ATTR_GROUP_ID = 'group_id'
ATTR_SCORE = 'score'
ATTR_UID = 'user_id'
ATTR_USER_INFO = 'user_info'
ATTR_FACE_NUM = 'face_num'
ATTR_MATCH_NUM = 'match_num'
ATTR_USER_LIST = 'user_list'

CONF_APP_ID = 'app_id'
CONF_SECRET_KEY = 'secret_key'
CONF_GROUP_LIST = 'group_list'
CONF_LIVENESS = 'liveness'
CONF_SCORE = 'score'
CONF_PORT = 'port'

DEFAULT_NAME = "face indentity"
DEFAULT_WAITING_PIC = 'https://gitee.com/caffreyfans/baidu_face/raw/dev/src/waiting.gif'
DEFAULT_PORT = 8123
DEFAULT_LIVENESS = 'NORMAL'
DEFAULT_SCORE = 80
DEFAULT_REQUEST_TYPE = "HTTP"

SCAN_INTERVAL = timedelta(seconds=2)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_APP_ID): cv.string,
    vol.Required(CONF_API_KEY): cv.string,
    vol.Required(CONF_SECRET_KEY): cv.string,
    vol.Required(CONF_ENTITY_ID): cv.string,
    vol.Required(CONF_GROUP_LIST): cv.string,
    vol.Required(CONF_ACCESS_TOKEN): cv.string,
    vol.Optional(CONF_LIVENESS, default=DEFAULT_LIVENESS): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_SCORE, default=DEFAULT_SCORE): cv.Number
})


def setup_platform(hass, config, add_devices,
                   discovery_info=None):
    tmp_path = hass.config.path('www/baidu_face/')
    import os
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    response = requests.get(DEFAULT_WAITING_PIC)
    path = tmp_path + 'waiting.gif'
    with open(path, 'wb') as fp:
        fp.write(response.content)
        fp.close()
    """ add sensor components """
    app_id = config.get(CONF_APP_ID)
    api_key = config.get(CONF_API_KEY)
    secret_key = config.get(CONF_SECRET_KEY)
    camera_entity_id = config.get(CONF_ENTITY_ID)
    group_list = config.get(CONF_GROUP_LIST)
    liveness = config.get(CONF_LIVENESS)
    name = config.get(CONF_NAME)
    port = config.get(CONF_PORT)
    token = config.get(CONF_ACCESS_TOKEN)
    score = config.get(CONF_SCORE)
    """ check SSL/HTTPS type """
    try: 
        http_url = "https://127.0.0.1:{}".format(port)
        camera_url = "{}/api/camera_proxy/{}".format(http_url, camera_entity_id)
        headers = {'Authorization': "Bearer {}".format(token),
               'content-type': 'application/json'}
        response = requests.get(camera_url, headers=headers, verify=False)
        if response.status_code == 200:
            DEFAULT_REQUEST_TYPE = "HTTPS"
    except BaseException:
        DEFAULT_REQUEST_TYPE = "HTTP"
    baidu_client = AipFace(app_id, api_key, secret_key)
    options = {}
    options["max_face_num"] = 10
    options["match_threshold"] = score
    options["quality_control"] = 'NONE'
    options["liveness_control"] = liveness
    options["max_user_num"] = 10
    add_devices([FaceSensor(name, camera_entity_id, port, token, baidu_client, group_list, options, tmp_path, DEFAULT_REQUEST_TYPE)])

class FaceSensor(Entity):

    def __init__(self, name, camera_entity_id, port, token, baidu_client:AipFace, group_list, options, tmp_path, request_type):
        self._camera_entity_id = camera_entity_id
        self._name = name
        self._port = str(port)
        self._token = token
        self._baidu_client = baidu_client
        self._group_list = group_list
        self._options = options
        self._state = False
        self._attr = None
        self._tmp_dir = tmp_path
        self._type = request_type

    @property
    def name(self):
        return self._name

    @property
    def entity_picture(self):
        pic_path = '/local/baidu_face/'
        if self._state:
            pic_path += self._attr[ATTR_UID] + '.jpg'
        else:
            pic_path += 'waiting.gif'
        return pic_path

    @property
    def state(self):
        return self._state

    @property
    def device_state_attributes(self):
        return self._attr

    def update(self):
        self._state = await hass.async_add_executor_job(self.face_searching)

    def get_picture(self):
        """ download picture from homeassistant """
        t = int(round(time.time()))
        headers = {'Authorization': "Bearer {}".format(self._token),
                   'content-type': 'application/json'}
        if self._type == "HTTP":
            http_url = "http://127.0.0.1:{}".format(self._port)
            camera_url = "{}/api/camera_proxy/{}?time={} -o image.jpg".format(http_url, self._camera_entity_id, t)
            response = requests.get(camera_url, headers=headers)
            return response.content
        if self._type == "HTTPS": 
            https_url = "https://127.0.0.1:{}".format(self._port)
            camera_url = "{}/api/camera_proxy/{}?time={} -o image.jpg".format(https_url, self._camera_entity_id, t)
            response = requests.get(camera_url, headers=headers, verify=False)
            return response.content

    def save_picture(self, file_name, content):
        import os
        save_path = self._tmp_dir + file_name + '.jpg'
        if not os.path.exists(save_path):
            with open(save_path, 'wb') as fp:
                fp.write(content)
                fp.close()

    def face_searching(self):
        origin_img = self.get_picture()
        encode_img= base64.b64encode(origin_img)
        encode_img = bytes.decode(encode_img)
        image_type = 'BASE64'
        ret = self._baidu_client.multiSearch(encode_img, image_type, self._group_list, self._options)
        self._attr = {}
        self._attr[ATTR_GROUP_ID] = 'None'
        self._attr[ATTR_UID] = 'None'
        self._attr[ATTR_USER_INFO] = 'None'
        self._attr[ATTR_SCORE] = 0
        self._attr[ATTR_FACE_NUM] = 0
        self._attr[ATTR_MATCH_NUM] = 0
        self._attr[ATTR_USER_LIST] = []
        max_score_person = None
        if ret['result'] is not None:
            self._attr[ATTR_FACE_NUM] = ret['result']['face_num']
            for i in ret['result']['face_list']:
                if i['user_list']:
                    if max_score_person is None:
                        max_score_person = i['user_list'][0]
                    elif i['user_list'][0]['score'] > max_score_person['score']:
                        max_score_person = i['user_list'][0]
                    self._attr[ATTR_MATCH_NUM] += 1
                    self._attr[ATTR_USER_LIST].append(i['user_list'][0]['user_id'])
        self._state = False
        if max_score_person is not None:
            self._state = True
            self._attr[ATTR_GROUP_ID] = max_score_person[ATTR_GROUP_ID]
            self._attr[ATTR_UID] = max_score_person[ATTR_UID]
            self._attr[ATTR_USER_INFO] = max_score_person[ATTR_USER_INFO]
            self._attr[ATTR_SCORE] = max_score_person[ATTR_SCORE]
            self.save_picture(max_score_person[ATTR_UID], origin_img)
