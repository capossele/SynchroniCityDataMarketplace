#!/bin/bash

apt-get install unzip
/business-ecosystem-charging-backend/src/manage.py loadplugin /business-ecosystem-charging-backend/src/plugins/Orion.zip

mkdir /business-ecosystem-charging-backend/src/wstore/asset_manager/resource_plugins/plugins/orion-query
unzip /business-ecosystem-charging-backend/src/plugins/Orion.zip /business-ecosystem-charging-backend/src/wstore/asset_manager/resource_plugins/plugins/orion-query

service apache2 restart
