FROM node:22-slim

WORKDIR /srv
COPY app/ /srv/app/
COPY fixed/ /srv/fixed/
COPY lib/ /srv/lib/
COPY package.json /srv/

ENV PORT=3000
# Which build to run: "app" (vulnerable, default) or "fixed".
ENV BUILD=app

CMD ["sh", "-c", "node /srv/${BUILD}/server.js"]
