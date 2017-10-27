django_selectel
===================


The file store in the [Selectel cloud store](https://selectel.ru/services/cloud/storage/) for Django

Storage and CDN creation
-------------
 - Log in to your personal [account](https://my.selectel.ru/login/) in
   Selectel. 
 - Create a [new user](https://my.selectel.ru/storage/users)
   to work with the store.
 - [Create a new](https://my.selectel.ru/storage/containers) private or public
   container.

Installation
-------------
Install using `pip`...

    pip install django_selectel
  
In `settings.py` add the following:

    INSTALLED_APPS = (
	    ...
	    'django_selectel',
	)

Settings
-------------------
All settings are optional, you can specify them when initializing the storage class

    SELECTEL_STORAGE = {
	    "USER": "",
	    "PASSWORD": "",
	    "DOMAINS": {},
	    "OVERWRITE_FILES": False,
	    "USE_GZ": False,
	    "AUTH_URL": "https://auth.selcdn.ru/",
	    "API_THRESHOLD": 30 * 60,
	    "API_MAX_RETRY": 3,
	    "API_RETRY_DELAY": 0.1
	}
	
	# or
	
	from django_selectel.storages import ApiStorage
	
	cdn_storage = ApiStorage(
		user="",
		password="",
		domains={},
		use_gz=False,
		overwrite_files=False
	)

#### **USER**
The username of the storage that is available

#### **PASSWORD**
Password from the user

#### **DOMAINS**

Associate a domain with a specific container. You can bind the domain in the container settings

Example:

    "DOMAINS": {
	    "my_public_container": "https://cdn.mysite.com"
    }

#### **OVERWRITE_FILES**
Allows you to overwrite files when the name is repeated

#### **USE_GZ**
For the storage of files will use the algorithm of compression [Gzip](http://www.gzip.org/zlib/rfc-gzip.html). This will reduce the volume of the container and transmitted traffic

> **Warning:**
> It is **not recommended for use in public containers**, since the files that will be downloaded directly from the CDN without processing will be in Gzip format

#### **AUTH_URL**

URL to get a token to work with the API

#### **API_THRESHOLD**

If the token expires less than the specified time (in seconds), it automatically updates

#### **API_MAX_RETRY**
The maximum number of attempts to download the file.
Helps avoid errors when the connection is not stable.

#### **API_RETRY_DELAY**
Delay in seconds between attempts

Using
-------------------

In `settings.py` add the following:

    SELECTEL_STORAGE = {
	    "USER": "MyUserName",
	    "PASSWORD": "MyPassword",
	}
The remaining settings can be omitted, because are not required, they will be used as default values if they are not passed as a class parameter

Create a model with a file field that will work with the cloud-based file system

    from django.db import models
    from django_selectel.storages import ApiStorage
    from django.core.files.base import ContentFile
	
	class Image(models.Model):
		...
		# for a public container
		file = models.FileField(upload_to='my_public_container', storage=ApiStorage()) 
		# for a private container
		file = models.FileField(upload_to='my_private_contrainer', storage=ApiStorage(use_gz=True))
	
	with open("my_image.jpg") as fh:
		Image.objects.create(
			...
			file=fh
		)
	image = Image.objects.first()
	print image.file.read()
	print image.size
	image.file.delete()

The first directory in the upload_to path describes which container the record will be written to. So you can use an unlimited number of containers.
You can specify a function that will return the path

    from datetime import date
    from django.db import models
    from django_selectel.storages import ApiStorage
    
    def image_upload_to(instance, filename):
        return "my_container/{:%Y-%m-%d}/{}".format(date.today(), filename)

	class Image(models.Model):
		...
		file = models.FileField(upload_to=image_upload_to, storage=ApiStorage())
