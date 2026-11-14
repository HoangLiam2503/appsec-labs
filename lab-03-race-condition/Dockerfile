FROM python:3.12-slim

WORKDIR /srv
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bring in both builds + the seeder.
COPY app/ /srv/app/
COPY fixed/ /srv/fixed/

ENV DB_PATH=/data/bank.db
# Which build to run: "app" (vulnerable, default) or "fixed".
ENV BUILD=app

CMD sh -c "python /srv/app/init_db.py && python /srv/${BUILD}/app.py"
