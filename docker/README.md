# Business API Ecosystem Docker Image

The [Business API Ecosystem](https://github.com/FIWARE-TMForum/Business-API-Ecosystem) can be deployed with Docker using
two different approaches. On the one hand, for all the components that made up the Business API Ecosystem it has been 
provided a Docker image that can be used jointly with `docker-compose` in order to deploy and configure the ecosystem.
On the other hand, this repo includes a single Docker image which already includes all the different Business API Ecosystem
modules.

The Business API Ecosystem requires instances of MySQL and MongoDB running. In this regard, you have three possibilities:
* You can have your own instances deployed in your machine
* You can manually run docker containers before executing the Business API Ecosystem
* You can use docker-compose to automatically deploy both components

## OAuth2 Authentication

The Business API Ecosystem authenticates with the [FIWARE identity manager](http://fiware-idm.readthedocs.io/en/latest/). In this regard, it is needed to register an application in this portal in order to acquire the OAuth2 credentials.

There you have to use the following info for registering the app:
* Name: The name you want for your instance
* URL: Host and port where you plan to run the instance. http|https://host:port/
* Callback URL: URL to be called in the OAuth process. http|https://host:port/auth/fiware/callback

## BAE Deployment

### BAE Modules Images

As stated, it is possible to deploy the Business API Ecosystem using the Docker images available for each of the BAE
modules with `docker-compose`. In particular, the following images have to be deployed:

* [biz-ecosystem-apis](https://hub.docker.com/r/conwetlab/biz-ecosystem-apis/): Image including the TMForum APIs
* [biz-ecosystem-rss](https://hub.docker.com/r/conwetlab/biz-ecosystem-rss/): Image Including the RSS module
* [biz-ecosystem-charging-backend](https://hub.docker.com/r/conwetlab/biz-ecosystem-charging-backend/): Image including the charging backend module
* [biz-ecosystem-logic-proxy](https://hub.docker.com/r/conwetlab/biz-ecosystem-logic-proxy/): Image including the logic proxy module

For deploying the BAE using this method the first step is creating a `docker-compose.yml` file with the following contents:

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
          - PAYPAL_CLIENT_ID=
          - PAYPAL_CLIENT_SECRET=

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
It is possible to find valid configuration files (as well as the `docker-compose.yml`) in the [GitHub repo of the BAE](https://github.com/FIWARE-TMForum/Business-API-Ecosystem)

As you can see, the different modules include environment variables and volumes. In particular:

**Charging**

The biz-ecosystem-charging-backend needs the following environment variables:
* **PAYPAL_CLIENT_ID**: the client id of your application PayPal credentials used for charging users (a Sandbox account can be used for testing).
* **PAYPAL_CLIENT_SECRET**: the client secret of your application PayPal credentials used for charging users (a Sandbox account can be used for testing).

Additionally, the biz-ecosystem-charging-backend image contains 5 volumes. In particular:
* */business-ecosystem-charging-backend/src/media/bills*: This directory contains the PDF invoices generated by the Business Ecosystem Charging Backend
* */business-ecosystem-charging-backend/src/media/assets*: This directory contains the different digital assets uploaded by sellers to the Business Ecosystem Charging Backend
* */business-ecosystem-charging-backend/src/plugins*: This directory is used for providing asset plugins (see section *Installing Asset Plugins*)
* */business-ecosystem-charging-backend/src/user_settings*: This directory must include the *settings.py* and *services_settings.py* files with the software configuration.
* */business-ecosystem-charging-backend/src/wstore/asset_manager/resource_plugins/plugins*: This directory includes the code of the plugins already installed

**Proxy**

The biz-ecosystem-logic-proxy image contains 4 volumes. In particular:
* */business-ecosystem-logic-proxy/etc*: This directory must include the `config.js` file with the software configuration
* */business-ecosystem-logic-proxy/indexes*: This directory contains the indexes used by the Business API Ecosystem for searching
* */business-ecosystem-logic-proxy/themes*: This directory contains the themes that can be used to customize the web portal
* */business-ecosystem-logic-proxy/static*: This directory includes the static files ready to be rendered including the selected theme and js files

Finally, the biz-ecosystem-logic-proxy uses the environment variable *NODE_ENV* to determine if the software is being used
in *development* or in *production* mode. 

> **Note**
> The *config.js* file must include an extra setting not provided by default called *config.extPort* that must include the port where the proxy is going to run in the host machine

Once you have created the files, run the following command:

```
docker-compose up
```

Then, the Business API Ecosystem should be up and running in `http://YOUR_HOST:PORT/` replacing `YOUR_HOST` by the host of your machine and `PORT` by the port provided in the Business Ecosystem Logic Proxy configuration 

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

## Installing Asset Plugins

As you may know, the Business API Ecosystem is able to sell different types of digital assets
by loading asset plugins in its Charging Backend. In this context, it is possible to install
asset plugins in the current Docker image as follows:

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
./manage.py loadplugin ./plugins/pluginfile.zip
```

5) Restart Apache
```
service apache2 restart
```