# E2E-only image: a node that really runs nginx, with a python3 for the agent.
#
# The Phase 4 journey enrolls a *real* agent against a throwaway stack and lets
# the control plane's apply pipeline write to this container's nginx. That needs
# the genuine thing: the nginx binary, a running master, and `nginx -t`, because
# the routing pre-flight (domain-routing.md §5) checks all three and refuses the
# node otherwise. `nginx:1.27-alpine` is the same base the repo's own edge image
# uses, so the layer is already local.
#
# The agent script is bind-mounted at run time by the spec (`-v $REPO/agent/
# nexusops_agent.py:/opt/nexusops/nexusops_agent.py:ro`) rather than copied, so
# this image never drifts from the file under test.
FROM nginx:1.27-alpine

# The agent is stdlib-only; python3 is all it needs.
RUN apk add --no-cache python3

# nginx is started by the spec before the agent so the pre-flight sees a running
# master; the image's own default configuration already listens on :80 (one
# non-default server), which is what `listener_80: MANAGED` requires.
CMD ["nginx", "-g", "daemon off;"]
