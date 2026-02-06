# Verifiable Credential Backend

This project implements a server for issuing and verifying verifiable credentials. The server is implemented in Python using the Flask framework.

## Usage

### To pull the Git Submodule use this Command:

`git submodule update --init --recursive`

### Before starting the server

If you are planning to use an app, you need to update the server url in main.py to your local network ip address. This is necessary because the app is running on a different device than the server.

### To start the server, run the following command:

```bash
docker compose up --build
```

### Possible Error on Windows Machine

If you using a Windows Machine, the Docker script will most like throw an error `./build.sh not found`

To resolve this Error, please change the Encoding manually:  
![image](https://github.com/user-attachments/assets/9c0b9a60-a670-4784-aad1-10df1c111f21)

Further readings: https://stackoverflow.com/questions/36001786/file-not-found-in-docker-container

## Demo

Install the dependancies using `pip install -r requirements.txt`.

To run the demo the server has to be running see [Usage](#Usage).

The demo rellies on the bbs-core library. To build the library navigate to `bbs-core/python` and run the corresponding `build` script depending on your operating system (Windows or Unix).

After building the library run `main.py` in the `demo` folder. The demo will guide you through the process of issuing and verifying a verifiable credential.

## Protocol

### Issuance

![Issuance](/documentation/issuance-protocol.jpg)

### Verification

![Verification](/documentation/verification-protocol.jpg)

## BBS-Core

![BBS-Core](/documentation/bbs.jpg)

## Structure

The server is divided into three parts: issuance, verification and validation.
Each of the parts is implemented in a separate module. Dividing the modules entails also spliting the database.
