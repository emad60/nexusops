FROM nginx:1.27-alpine
# The official image envsubst-renders /etc/nginx/templates/*.template into
# conf.d/ using the container's environment (API_UPSTREAM, WEB_UPSTREAM).
COPY default.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 8080
