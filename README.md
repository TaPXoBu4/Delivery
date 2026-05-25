# Delivery

## Order cleanup

The web app does not run background cleanup jobs inside the Flask process. On
production Linux, run the dedicated CLI command from a single systemd timer:

```bash
flask --app wsgi orders cleanup
```

By default it deletes orders older than 6 months. Override the retention window
with `ORDER_RETENTION_MONTHS` or a one-off CLI option:

```bash
flask --app wsgi orders cleanup --months 6
```

Systemd unit templates are in `deploy/systemd`. The timer is intended to run at
03:00 on the first day of each month in the server local timezone. For the VDS,
set the server timezone to Irkutsk:

```bash
sudo timedatectl set-timezone Asia/Irkutsk
```
