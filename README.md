# REST in Flask


## Run in development mode

In order to run this project in deployment mode you should create a python virtual environment using this command

```
$ virtualenv env
```

Then activate your virtual environment and install required packages

```
$ source env/bin/activate && pip install -r requirements
```

After that run project using project manager

```
$ ./manager.py run
```

## Available routes

To see project available routes use this command

```
$ ./manager.py routes
```

## Update Python Packages

Update python packages using this commend:

```
$ pip freeze | grep -v '^\-e' | cut -d = -f 1  | xargs pip install -U
```

## Generate API documentation

First, install apidoc js
```
$ ./manager.py doc
```


## Database
### Create database
```
./manager.py database create
```
### Drop database
```
./manager.py database drop
```
### Drop & Create database
```
./manager.py database recreate
```
### Generate fake data
This will generate some fake data for development use.
A development `user` will be create with last living access token.

```
./manager.py database fake
```
#### Development user info:

- Username: `rishe`
- Phone : `09123456789`
- Password : `123123`
- Access-Token : `123456`

## Migration
Sometimes you make changes in database models and you want to apply them to your database you can use migration for this purpose.
first run migration init command and then use migrate and upgrade command to apply your migration

**Note** that this tool is not 100% trusted and  you should review generated migration scripts code and then use upgrade command.

### Init migration
```
./manager.py migration init
```
### Generate migration code
```
./manager.py migration migrate
```
### Run migration code and upgrade database
```
./manager.py migration upgrade
```
### Migration Help
To see other commands use help.

```
./manager.py migration --help
```

