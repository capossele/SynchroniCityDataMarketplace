# SynchroniCity IoT Data Marketplace Docker Image

The [SynchroniCity IoT Data Marketplace](https://github.com/caposseleDigicat/SynchroniCityDataMarketplace/) can be deployed with Docker.
For all the components that made up the SynchroniCity IoT Data Marketplace (based on the Business API Ecosystem (https://github.com/FIWARE-TMForum/Business-API-Ecosystem) it has been 
provided a Docker image that can be used jointly with `docker-compose` in order to deploy and configure the ecosystem.

The SynchroniCity IoT Data Marketplace requires instances of MySQL and MongoDB running. In this regard, you have three possibilities:
* You can have your own instances deployed in your machine
* You can manually run docker containers before executing the Business API Ecosystem
* You can use docker-compose to automatically deploy both components

## OAuth2 Authentication

The SynchroniCity IoT Data Marketplace authenticates with the [FIWARE identity manager](http://fiware-idm.readthedocs.io/en/latest/). 
It is needed to register an application in this portal in order to acquire the OAuth2 credentials.

There you have to use the following info for registering the app:
* Name: The name you want for your instance
* URL: Host and port where you plan to run the instance. [http]|https://host:port/
* Callback URL: URL to be called in the OAuth process. [http]|https://host:port/auth/fiware/callback

You must also create a new role called 'seller' and assign this role to the user authorized to be seller (data provider) in the marketplace.

## SynchroniCity IoT Data Marketplace Deployment

### SynchroniCity IoT Data Marketplace Modules Images

As stated, it is possible to deploy the SynchroniCity IoT Data Marketplace using the Docker images available for each of its
modules with `docker-compose`. In particular, the following images have to be deployed:

* [bae-apis-synchronicity](https://hub.docker.com/r/angelocapossele/bae-apis-synchronicity/): Image including the TMForum APIs
* [biz-ecosystem-rss](https://hub.docker.com/r/conwetlab/biz-ecosystem-rss/): Image Including the BAE RSS module
* [charging-backend-synchronicity](https://hub.docker.com/r/angelocapossele/charging-backend-synchronicity/): Image including the charging backend module
* [logic-proxy-synchronicity](https://hub.docker.com/r/conwetlab/angelocapossele/logic-proxy-synchronicity/): Image including the logic proxy module

For deploying the SynchroniCity IoT Data Marketplace the first step is creating a `docker-compose.yml` file with the following contents (or use the one provided in this GitHub repo):

```
version: '3'
services:
    mongo:
        image: mongo:3.2
        restart: always
        ports:
            - 27017:27017
        networks:
            main:
        volumes:
            - ./mongo-data:/data/db

    mysql:
        image: mysql:latest
        restart: always
        ports:
            - 3333:3306
        volumes:
            - ./mysql-data:/var/lib/mysql
        networks:
            main:
        environment:
            - MYSQL_ROOT_PASSWORD=my-secret-pw
            - MYSQL_DATABASE=RSS

    charging:
        image: angelocapossele/charging-backend-synchronicity:v6.4.0
        restart: always
        links:
            - mongo
        depends_on:
            - mongo
            - apis
            - rss
        ports:
            - 8006:8006
        networks:
            main:
                aliases:
                    - charging.docker
        volumes:
            - ./charging-bills:/business-ecosystem-charging-backend/src/media/bills
            - ./charging-assets:/business-ecosystem-charging-backend/src/media/assets
            - ./charging-plugins:/business-ecosystem-charging-backend/src/plugins
            - ./charging-settings:/business-ecosystem-charging-backend/src/user_settings
        environment:
          - PAYPAL_CLIENT_ID=client_id_here
          - PAYPAL_CLIENT_SECRET=client_secret_here

    proxy:
        image: angelocapossele/logic-proxy-synchronicity:v6.4.0
        restart: always
        links:
            - mongo
        depends_on:
            - mongo
            - apis
        ports:
            - 8004:8004
        networks:
            main:
                aliases:
                    - proxy.docker
        volumes:
            - ./proxy-conf:/business-ecosystem-logic-proxy/etc
            - ./proxy-indexes:/business-ecosystem-logic-proxy/indexes
            - ./proxy-themes:/business-ecosystem-logic-proxy/themes
            - ./proxy-static:/business-ecosystem-logic-proxy/static
        environment:
            - NODE_ENV=development

    apis:
        image: angelocapossele/bae-apis-synchronicity:v6.4.0
        restart: always
        ports:
            - 4848:4848
            - 8080:8080
        links:
            - mysql
        depends_on:
            - mysql
        networks:
            main:
                aliases:
                    - apis.docker
        volumes:
            - ./apis-conf:/etc/default/tmf/
        environment:
            - MYSQL_ROOT_PASSWORD=my-secret-pw
            - MYSQL_HOST=mysql

    rss:
        image: conwetlab/biz-ecosystem-rss:v6.4.0
        restart: always
        ports:
            - 9999:8080
            - 4444:4848
            - 1111:8181
        links:
            - mysql
        depends_on:
            - mysql
        networks:
            main:
                aliases:
                    - rss.docker
        volumes:
            - ./rss-conf:/etc/default/rss

networks:
    main:
        external: true
```

The next step is providing all the configuration files required by the different components using the configured volumes.
It is possible to find valid configuration files (as well as the `docker-compose.yml`) in this GitHub repo (https://github.com/caposseleDigicat/SynchroniCityDataMarketplace)

As you can see, the different modules include environment variables and volumes. In particular:

**Charging**

The charging-backend-synchronicity needs the following environment variables:
* **PAYPAL_CLIENT_ID**: the client id of your application PayPal credentials used for charging users (a Sandbox account can be used for testing).
* **PAYPAL_CLIENT_SECRET**: the client secret of your application PayPal credentials used for charging users (a Sandbox account can be used for testing).

Additionally, the charging-backend-synchronicity image contains 4 volumes. In particular:
* */business-ecosystem-charging-backend/src/media/bills*: This directory contains the PDF invoices generated by the Business Ecosystem Charging Backend
* */business-ecosystem-charging-backend/src/media/assets*: This directory contains the different digital assets uploaded by sellers to the Business Ecosystem Charging Backend
* */business-ecosystem-charging-backend/src/plugins*: This directory is used for providing asset plugins (see section *Installing Asset Plugins*)
* */business-ecosystem-charging-backend/src/user_settings*: This directory must include the *settings.py* and *services_settings.py* files with the software configuration. More specifically, the *services_settings.py* includes:
    * KEYSTONE_PROTOCOL: http or https
    * KEYSTONE_HOST: host where is running the IDM (e.g., 'idm.docker')
    * KEYROCK_PORT: port number where the *Keyrock* instance is listening (e.g., '8000')
    * KEYSTONE_PORT: port number where the *Keystone* instance  is listening (e.g., '5000')
    * KEYSTONE_USER: admin username of the IDM (e.g., 'idm')
    * KEYSTONE_PWD: admin password of the IDM (e.g., 'idm')
    * ADMIN_DOMAIN: admin domain on the IDM (e.g., 'Default') 
    * APP_CLIENT_ID: Client ID of the Orion context broker registered on the IDM
    * APP_CLIENT_SECRET: Client Secret of the Orion Context Broker registered on the IDM


**Proxy**

The logic-proxy-synchronicity image contains 4 volumes. In particular:
* */business-ecosystem-logic-proxy/etc*: This directory must include the `config.js` file with the software configuration
* */business-ecosystem-logic-proxy/indexes*: This directory contains the indexes used by the SynchroniCity IoT Data Marketplace for searching
* */business-ecosystem-logic-proxy/themes*: This directory contains the themes that can be used to customize the web portal
* */business-ecosystem-logic-proxy/static*: This directory includes the static files ready to be rendered including the selected theme and js files

Finally, the logic-proxy-synchronicity uses the environment variable *NODE_ENV* to determine if the software is being used
in *development* or in *production* mode. 

> **Note**
> The *config.js* file must include an extra setting not provided by default called *config.extPort* that must include the port where the proxy is going to run in the host machine

Once you have created the files, run the following command:

```
docker-compose up
```

Then, the SynchroniCity IoT Data Marketplace should be up and running in `http://YOUR_HOST:PORT/` replacing `YOUR_HOST` by the host of your machine and `PORT` by the port provided in the Business Ecosystem Logic Proxy configuration 

Once the different containers are running, you can stop them using:

```
docker-compose stop
```

And start them again using:

```
docker-compose start
```

Additionally, you can terminate the different containers by executing:

```
docker-compose down
```

## Installing Orion Query Plugin

As you may know, the SynchroniCity IoT Data Marketplace is able to sell different types of data sources. To support this functionality, it must be installed the Orion Query plugin (also included in the current Github repo) as follows:

1) Copy the plugin file into the host directory of the volume */business-ecosystem-charging-backend/src/plugins*

2) Enter the running container:
```
docker exec -i -t your-container /bin/bash
```

3) Go to the installation directory
```
cd /apis/business-ecosystem-charging-backend/src
```

4) Load the plugin
```
./manage.py loadplugin ./plugins/Orion.zip
```

5) Restart Apache
```
service apache2 restart
```