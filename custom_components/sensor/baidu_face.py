""" 利用百度人脸识别 API v2 进行人脸识别 """
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

ATTR_SCORES = 'scores'
ATTR_GROUP_ID = 'group_id'
ATTR_UID = 'uid'
ATTR_USER_INFO = 'user_info'
ATTR_FACELIVENESS = "faceliveness"

CONF_NAME = 'name'
CONF_APIKEY = 'api_key'
CONF_SECRETKEY = 'secret_key'
CONF_GROUP_ID = 'group_id'
CONF_PORT = 'port'
CONF_CAMERA_ENTITY_ID = 'camera_entity_id'
CONF_PIC_URL = 'pic_url'
CONF_TOKEN = 'token'


PASS_SCORE = 80
THRESHOLD = 0.393241
DEFAULT_NAME = "ren lian shi bie"
DEFAULT_PIC_URL = "https://dev.tencent.com/u/Caffreyfans/p/public-sources/git/raw/master/1.gif"
DEFAULT_PORT = 8123

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_APIKEY): cv.string,
    vol.Required(CONF_SECRETKEY): cv.string,
    vol.Required(CONF_GROUP_ID): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Required(CONF_CAMERA_ENTITY_ID): cv.string,
    vol.Optional(CONF_PIC_URL, default=DEFAULT_PIC_URL): cv.string,
    vol.Required(CONF_TOKEN): cv.string
})


def setup_platform(hass, config, add_devices,
	               discovery_info=None):
    """ add sensor components """
    name = config.get(CONF_NAME)
    api_key = config.get(CONF_APIKEY)
    secret_key = config.get(CONF_SECRETKEY)
    group_id = config.get(CONF_GROUP_ID)
    port = config.get(CONF_PORT)
    camera_entity_id = config.get(CONF_CAMERA_ENTITY_ID)
    pic_url = config.get(CONF_PIC_URL)
    token = config.get(CONF_TOKEN)

    add_devices([FaceSensor(name, port, camera_entity_id, api_key, secret_key, group_id, pic_url, token)])


class FaceSensor(Entity):

	savePath = ""
	suffix = "tmp.jpg"
	recognise = {}

	def __init__(self, name, port, camera_entity_id, api_key, secret_key, group_id, pic_url, token):
		self._name = name
		self._state = False
		self._port = str(port)
		self._camera_entity_id = camera_entity_id
		self._api_key = api_key
		self._secret_key = secret_key
		self._group_id = group_id
		self._pic_url = pic_url
		self._token = token
		self.exists_path()

		
	@property
	def name(self):
		return self._name

	
	@property
	def entity_picture(self):
		if (self._state == True):
			return '/local/images/' + FaceSensor.suffix
		else:
			return self._pic_url

		
	@property
	def state(self):
		return self._state
	

	@property
	def device_state_attributes(self):
		if (self._state == True):
			if ("result" in FaceSensor.recognise):
				return {
					ATTR_SCORES : FaceSensor.recognise["result"][0]["scores"][0],
					ATTR_UID : FaceSensor.recognise["result"][0]["uid"],
					ATTR_GROUP_ID : FaceSensor.recognise["result"][0]["group_id"],
					ATTR_USER_INFO : FaceSensor.recognise["result"][0]["user_info"],
					ATTR_FACELIVENESS : FaceSensor.recognise["ext_info"]["faceliveness"]
				}
		return {
			ATTR_SCORES : 'null',
			ATTR_UID : 'null',
			ATTR_GROUP_ID : 'null',
			ATTR_USER_INFO : 'null',
			ATTR_FACELIVENESS : 'null'
		}

	
	def update(self):
		self.download_picture()
		ret = self.identify_face()
		if (ret == True):
			self._state = True
		else:
			self._state = False

			
	def download_picture(self):
		""" download picture from homeassistant """
		t = int(round(time.time()))
		url = "http://127.0.0.1:%s/api/camera_proxy/%s?time=%d -o image.jpg"%(self._port, self._camera_entity_id, t)
		headers = {'Authorization': "Bearer %s"%(self._token),
					'content-type': 'application/json'}
		response = requests.get(url, headers=headers)
		path = FaceSensor.savePath + FaceSensor.suffix
		with open(path, 'wb') as fp:
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


	# def detect_face(self):
	# 	from PIL import Image
	# 	request_url = "https://aip.baidubce.com/rest/2.0/face/v2/detect"
	# 	img = self.get_base64_file_content(FaceSensor.savePath)
	# 	params = {
	# 		"access_token" : self.get_token(),
	# 	}
	# 	data = {"image" : img}
	# 	ret = requests.post(url=request_url, params=params, data=data)
	# 	ret_json = json.loads(ret.text)
	# 	if ("result" in ret_json):
	# 		location = ret_json["result"][0]["location"]
	# 		img = Image.open(FaceSensor.savePath)
	# 		left = location["left"]
	# 		upper = location["top"]
	# 		middle = (location["width"] + location["height"]) / 2
	# 		right = left + middle
	# 		lower = upper + middle
	# 		cropped = img.crop((left, upper, right, lower))
	# 		cropped.save(FaceSensor.savePath)
	# 		img = Image.open(FaceSensor.savePath)
	# 		out = img.resize((48, 48),Image.ANTIALIAS)
	# 		out.save(FaceSensor.iconPath)


	def identify_face(self):
		request_url = "https://aip.baidubce.com/rest/2.0/face/v2/identify"
		pic_path = FaceSensor.savePath + FaceSensor.suffix
		img = self.get_base64_file_content(pic_path)	
		params = {'access_token' : self.get_token()}
		data = {
			'image' : img,
			'group_id' : self._group_id,
			'ext_fields' : 'faceliveness'
			}
		ret = requests.post(url=request_url, params=params, data=data)	
		ret_json = json.loads(ret.text)
		if ("result" in ret_json):
			FaceSensor.recognise = ret_json
			scores = ret_json["result"][0]["scores"][0]
			faceliveness = float(ret_json["ext_info"]["faceliveness"])
			FaceSensor.suffix = ret_json["result"][0]["uid"] + ".jpg"
			if ((ret_json["result"][0]["scores"][0] > PASS_SCORE) and (faceliveness > THRESHOLD)):
				return True
		else:
			_LOGGER.error(ret.text)
			return False


	def exists_path(self):
		import os
		docker_path = "/config"
		hassbian_path = "/home/homeassistant/.homeassistant"
		if (os.path.exists(hassbian_path)):
			hassbian_path = hassbian_path + "/www/images/"
			if not (os.path.exists(hassbian_path)):
				os.makedirs(hassbian_path)
			FaceSensor.savePath = hassbian_path
		elif (os.path.exists(docker_path)):
			docker_path = docker_path + "/www/images/"
			if not (os.path.exists(docker_path)):				
				os.makedirs(docker_path)
			FaceSensor.savePath = docker_path
