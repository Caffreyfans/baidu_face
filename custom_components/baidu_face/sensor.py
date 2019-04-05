""" 利用百度人脸识别 APIv3 进行人脸识别. """
from homeassistant.components.sensor import PLATFORM_SCHEMA
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import time
import logging
import requests
import json
from homeassistant.helpers.entity import Entity
import base64

_LOGGER = logging.getLogger(__name__)

ATTR_GROUP_ID = 'group_id'
ATTR_SCORE = 'score'
ATTR_UID = 'user_id'
ATTR_USER_INFO = 'user_info'

ATTR_LIST = {
	ATTR_GROUP_ID : "null",
	ATTR_SCORE : "null",
	ATTR_UID : "null",
	ATTR_USER_INFO : "null"
}

CONF_APIKEY = 'api_key'
CONF_CAMERA_ENTITY_ID = 'camera_entity_id'
CONF_GROUP_LIST = 'group_list'
CONF_LIVENESS = 'liveness'
CONF_NAME = 'name'
CONF_PORT = 'port'
CONF_PIC_URL = 'pic_url'
CONF_SECRETKEY = 'secret_key'
CONF_TOKEN = 'token'





DEFAULT_NAME = "ren lian shi bie"
DEFAULT_PIC_URL = 'https://dev.tencent.com/u/Caffreyfans/p/public-sources/git/raw/master/1.gif'
DEFAULT_PORT = 8123
DEFAULT_LIVENESS = 'NORMAL'

LOCAL_PATH = '/local/images/'
PASS_SCORE = 80.0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_APIKEY): cv.string,
    vol.Required(CONF_CAMERA_ENTITY_ID): cv.string,
    vol.Required(CONF_GROUP_LIST): cv.string,
    vol.Optional(CONF_LIVENESS, default=DEFAULT_LIVENESS): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_PIC_URL, default=DEFAULT_PIC_URL): cv.string,
    vol.Required(CONF_SECRETKEY): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
})


def setup_platform(hass, config, add_devices,
	               discovery_info=None):
    """ add sensor components """
    api_key = config.get(CONF_APIKEY)
    camera_entity_id = config.get(CONF_CAMERA_ENTITY_ID)
    group_list = config.get(CONF_GROUP_LIST)
    liveness = config.get(CONF_LIVENESS)
    name = config.get(CONF_NAME)
    port = config.get(CONF_PORT)
    pic_url = config.get(CONF_PIC_URL)
    secret_key = config.get(CONF_SECRETKEY)
    token = config.get(CONF_TOKEN)

    add_devices([FaceSensor(api_key, camera_entity_id, group_list, liveness, name, port, pic_url, secret_key, token)])


class FaceSensor(Entity):

	def __init__(self, api_key, camera_entity_id, group_list, liveness, name, port, pic_url, secret_key, token):
		self._api_key = api_key
		self._camera_entity_id = camera_entity_id
		self._group_list = group_list
		self._liveness = liveness
		self._name = name
		self._port = str(port)
		self._pic_url = pic_url
		self._secret_key = secret_key
		self._token = token
		self._state = False
		self._save_path = ""
		self._pic_name = ""
		self.exists_path()

	@property
	def name(self):
		return self._name
	
	@property
	def entity_picture(self):
		if (self._state == True):
			pic_path = LOCAL_PATH + self._pic_name
			return pic_path
		else:
			return self._pic_url

	@property
	def state(self):
		return self._state
	
	@property
	def device_state_attributes(self):
		return ATTR_LIST

	
	def update(self):
		save_path = self._save_path + "tmp.jpg"
		self.download_picture(save_path)
		ret = self.face_searching(save_path)
		if (ret == True):
			self._state = True
		else:
			self._state = False

			
	def download_picture(self, savePath):
		""" download picture from homeassistant """
		from http import HTTPStatus
		t = int(round(time.time()))
		http_url = "http://127.0.0.1:{}".format(self._port)
		https_url = "https://127.0.0.1:{}".format(self._port)
		url = http_url
		try:
			status_code = requests.get(url).status_code
		except:
			status_code = HTTPStatus.INTERNAL_SERVER_ERROR
		if status_code == HTTPStatus.OK :
			url = http_url
		else:
			url = https_url
		camera_url = "{}/api/camera_proxy/{}?time={} -o image.jpg".format(url, self._camera_entity_id, t)
		headers = {'Authorization': "Bearer {}".format(self._token),
					'content-type': 'application/json'}
		response = requests.get(camera_url, headers=headers)
		with open(savePath, 'wb') as fp:
		    fp.write(response.content)

	def get_base64_file_content(self, filePath):
	    with open(filePath, 'rb') as fp:
	        return base64.b64encode(fp.read())

	def get_token(self):
		grant_type = 'client_credentials'
		request_url = "https://aip.baidubce.com/oauth/2.0/token"
		params = {'client_id' : self._api_key, "client_secret" : self._secret_key, 'grant_type' : grant_type}
		response = requests.post(url=request_url, params=params)
		access_json = json.loads(response.text)
		if ("access_token" in access_json):
			return access_json['access_token']
		else:
			_LOGGER.error("There is some wrong about your baidu api settings")
			return None


	def face_searching(self, picPath):
		request_url = "https://aip.baidubce.com/rest/2.0/face/v3/search"
		headers = {'Content-Type' : 'application/json'}
		group_id_list = eval(self._group_list)
		img = self.get_base64_file_content(picPath)
		data = {'image_type' : 'BASE64',
				 'image' : img,
				 'access_token' : self.get_token(),
				 'group_id_list' : group_id_list,
				 'liveness_control' : self._liveness}
		response = requests.post(url=request_url, headers=headers, data=data)
		ret_json = json.loads(response.text)
		for key in ATTR_LIST:
			ATTR_LIST[key] = 'null'
		if ret_json['result']:
			score = ret_json['result']['user_list'][0]['score']
			if (score > PASS_SCORE):
				for key in ATTR_LIST:
					ATTR_LIST[key] = ret_json['result']['user_list'][0][key]
				self._pic_name = ATTR_LIST[ATTR_UID] + ".jpg"
				save_path = self._save_path + self._pic_name
				import shutil
				shutil.copyfile(picPath, save_path)
				return True
		return False

	def exists_path(self):
		import os
		docker_path = "/config"
		hassbian_path = "/home/homeassistant/.homeassistant"
		raspbian_path = "/home/pi/.homeassistant"
		path_list = [docker_path, hassbian_path, raspbian_path]
		for path in path_list:
			if (os.path.exists(path)):
				path = path + "/www/images/"
				if not (os.path.exists(path)):
					os.makedirs(path)
				self._save_path = path
				break