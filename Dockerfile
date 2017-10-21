FROM python:3.6

RUN apt-get update \
	&& apt-get install -yq --fix-missing ca-certificates nginx gettext-base supervisor

RUN pip install uwsgi

## #################
##      Nginx
## #################

# forward request and error logs to docker log collector
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log \
	&& echo "daemon off;" >> /etc/nginx/nginx.conf \
	&& rm /etc/nginx/sites-enabled/default

# Copy the modified Nginx conf
COPY ./docker/nginx.conf /etc/nginx/conf.d/
# Copy the base uWSGI ini file to enable default dynamic uwsgi process number
COPY ./docker/uwsgi.ini /etc/uwsgi/


## #################
##   Supervisord
## #################

# Custom Supervisord config
COPY ./docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf


## #################
##     Project
## #################
COPY  ./project/ /project/
WORKDIR /project

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80 443
CMD ["/usr/bin/supervisord"]