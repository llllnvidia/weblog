FROM lepinkainen/ubuntu-python-base
MAINTAINER "linw" <815750986@qq.com>
RUN apt-get update
RUN apt-get install -y curl wget tar bzip2 unzip vim
RUN apt-get install -y nginx git build-essential
RUN apt-get clean all
RUN echo "daemon off;" >> /etc/nginx/nginx.conf

RUN pip install supervisor gunicorn

ADD supervisord.conf /etc/supervisord.conf

RUN mkdir -p /etc/supervisor.conf.d && \
    mkdir -p /var/log/supervisor
RUN mkdir -p /usr/src/app && mkdir -p /var/log/gunicorn

WORKDIR /usr/src/app
ADD requirements.txt /usr/src/app/requirements.txt
RUN pip install -r /usr/src/app/requirements.txt

COPY . /usr/src/app
RUN ln -s /usr/src/app/codeblog_nginx.conf /etc/nginx/sites-enabled
EXPOSE 8000 5000 25

CMD ["/usr/local/bin/supervisord", "-n"]
