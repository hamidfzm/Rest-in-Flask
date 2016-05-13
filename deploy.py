#!/usr/bin/env python

# project imports
from application import create_app
from application.config import DeploymentConfig


app = create_app(DeploymentConfig)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
