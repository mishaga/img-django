# img project

Project for storing and resizing images.

Source images are stored in a private directory, resized images – in public one.  
Django doesn't return resized images, nginx does this.

## How to run project locally

1. Locate to the project dir: `cd /path/to/project`
2. Build project: `make build`
3. Create `docker-compose.override.yml` file, define `POSTGRES_PASSWORD` for each service and `SECRET_KEY` for web service (see sample below)
4. Run database `docker-compose up -d db`
5. Migrate: `make migrate`
6. Enter the shell: `make shell`
7. Create superuser: `python manage.py createsuperuser`, type `exit` after creation
8. Stop database `make down`
9. Set up nginx to response on server name `img.local` or another you like (see sample below)
10. Start project: `make up`
11. Enter django admin panel: http://img.local/admin/login/
12. Create user here: http://img.local/admin/auth/user/add/  
    Name it for example `test-user`, also create token for him – it's some kind of authorisation for API.  
    Let it be `ea999570-9758-4bac-ab4f-94ad358b925a` for example

Next time you can simply start project with `make up` or `make up-d` command.

### docker-compose.override.yml sample

```yaml
version: "3.3"
services:
  web:
    environment:
      - POSTGRES_PASSWORD=my-fancy-password
      - SECRET_KEY=my-fancy-and-secure-secret-key
  db:
    environment:
      - POSTGRES_PASSWORD=my-fancy-password
```

### nginx settings sample

For each user you need to create nginx rule to his "sizes" path.  
Note, that it's necessary to put slash symbol "/" at the end of the path.

```
server {
    listen 80;
    server_name img.local;

    location / {
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header Host $host;
        proxy_pass http://localhost:8001;
    }

    location /favicon.ico {
        alias /path/to/project/img/app/static/favicon.ico;
    }

    location /test-user/ {
        alias /path/to/project/uploads/resizes/test-user/;
    }
}
```

Don't forget to restart/reload nginx.  
And also don't forget to put your domain name into `/etc/hosts`

## API

There are three API methods: for upload, resize and delete image.  
All of them required `X-Auth-Token` header, user token has to be passed as value of this header.

### Upload

URL: `/upload/`  
Method: `POST`  
Required header: `X-Auth-Token`  
Params:
1. `file` (file, required) file of an image (any format – jpeg, png, tiff, gif, etc)
2. `sizes` (str, not required) "size" in this context is "x"-separated width and height of image,  
   sizes are comma-separated size list. For example: `100x100,500x500`

Returns filename and links to resized images. Note that all resized images are public, the original image is private.  
All images stored in `/uploads/` directory in the project.

**Samples**

_Request with sizes_

```bash
curl --request POST \
  --url http://img.local/upload/ \
  --header 'Content-Type: multipart/form-data' \
  --header 'X-Auth-Token: ea999570-9758-4bac-ab4f-94ad358b925a' \
  --form file=@/path/to/image.jpg \
  --form 'sizes=200x300,400x500,700x600,1024x768'
```

_Response_

```json
{
	"code": 1,
	"message": {
		"filename": "5a673ebe07164916834d1d039a4d14b5.jpeg",
		"sizes": {
			"200x300": "http://img.local/test-user/200x300/5a673ebe07164916834d1d039a4d14b5.jpeg",
			"400x500": "http://img.local/test-user/400x500/5a673ebe07164916834d1d039a4d14b5.jpeg",
			"700x600": "http://img.local/test-user/700x600/5a673ebe07164916834d1d039a4d14b5.jpeg",
			"1024x768": "http://img.local/test-user/1024x768/5a673ebe07164916834d1d039a4d14b5.jpeg"
		}
	}
}
```

_Request with no sizes_

```bash
curl --request POST \
  --url http://img.local/upload/ \
  --header 'Content-Type: multipart/form-data' \
  --header 'X-Auth-Token: ea999570-9758-4bac-ab4f-94ad358b925a' \
  --form file=@/path/to/image.jpg
```

_Response_

```json
{
	"code": 1,
	"message": {
		"filename": "01966268e1554ca6a160fa46573e5f39.jpeg",
		"sizes": null
	}
}
```

### Resize

URL: `/<filename>.<ext>`  
Method: `POST`  
Required header: `X-Auth-Token`  
Params:
1. `width` (int > 0, required) new needed width of an image
2. `height` (int > 0, required) new needed height of an image

If you didn't pass sizes parameter when uploaded image or if you need a new size, you can request it.

**Sample**

_Request_

```bash
curl --request POST \
  --url http://img.local/01966268e1554ca6a160fa46573e5f39.jpeg \
  --header 'Content-Type: multipart/form-data' \
  --header 'X-Auth-Token: ea999570-9758-4bac-ab4f-94ad358b925a' \
  --form width=800 \
  --form height=600
```

_Response_

```json
{
	"code": 1,
	"message": "http://img.local/test-user/800x600/01966268e1554ca6a160fa46573e5f39.jpeg"
}
```

### Delete

URL: `/<filename>.<ext>`  
Method: `DELETE`  
Required header: `X-Auth-Token`  
Params: no params needed

Deletes all resized images and original one as well.

**Sample**

_Request_

```bash
curl --request DELETE \
  --url http://img.local/01966268e1554ca6a160fa46573e5f39.jpeg \
  --header 'X-Auth-Token: ea999570-9758-4bac-ab4f-94ad358b925a'
```

_Response_

```json
{
	"code": 1,
	"message": "Deleted"
}
```

### List of codes

API always returns `code` along the `message` parameter.  
So `code` could contain int only. If it equals one, then it's okay, there is no error.  
But in other situations `code` could contain one of these values:

* `1` – Okay, no error
* `0` – Unknown error
* `-1` – Incorrect request / Error in request
* `-2` – Error in parameters of request
* `-3` – Server side error

## How to stop project

If you have started project with `make up` command, press `Ctrl+C`.  
If it was started in background with `make up-d` command, run `make down` in project directory.

## Development

If you'd like, you can fork project and modify it for your own proposes.

Don't forget about tests. You can run them with `make autotests` command.

Also, it's nice to maintain good quality of your code. To check it you can use `make link` command,
it runs `flake8` and `mypy`.

## Resize all images

There is also management command `create_resizes` that will create certain resizes for all images of the user.

**Sample**

```bash
make shell
python manage.py create_resizes --width=700 --height=700 --username=test-user
```
