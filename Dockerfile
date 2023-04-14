FROM nginx
WORKDIR /
RUN ls -al
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
EXPOSE 80
RUN groupadd --gid 53150 -r notroot  && useradd -r -g notroot -s "/opt/homebrew/bin/bash" --create-home --uid 53150 notroot
 USER notroot
