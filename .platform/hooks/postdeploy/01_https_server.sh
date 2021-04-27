#!/bin/bash
# Ugly hack to force Elastic Beanstalk to pick up our extended NGINX configuration for HTTPS
# Because what's documented for Amazon Linux 2 environments flat-out does not work with Docker, apparently
# https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/platforms-linux-extend.html

# TODO: Once Elastic Beanstalk supports NGINX extensions in Linux Docker envs (which it purports to)
# in the format AWS has documented, move the server block into the following location from project root:
# .platform/nginx/conf.d/https.conf

sudo mkdir -p /etc/nginx/conf.d
rm -f /etc/nginx/conf.d/https.conf

echo "
# HTTPS server
server {
    listen       443 ssl;
    server_name  *.ece-pensieve.ctoecskylight.com;

    ssl_certificate      /etc/pki/tls/certs/server.crt;
    ssl_certificate_key  /etc/pki/tls/certs/server.key;

    ssl_session_timeout  5m;

    ssl_protocols  TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers   on;

    client_max_body_size 5M;

    location / {
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$http_host;
        proxy_set_header X-NginX-Proxy true;
        proxy_pass http://127.0.0.1:8088;
        proxy_redirect off;
    }
}
" >> https.conf

sudo cp https.conf /etc/nginx/conf.d/https.conf
rm https.conf

sudo service nginx restart