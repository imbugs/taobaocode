#!/bin/sh
python manage.py makemessages -l zh_CN -a
python manage.py compilemessages
