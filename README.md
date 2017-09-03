## What is OSS2FA?

OSS2FA is a two-factor authentication (2FA) framework that helps you integrate modern multi-factor authentication solutions in all of your projects.

- **Simple** - With a minimal API surface, oss2fa is designed to be easy to learn and simple to use
- **Modern** - In addition to established device types, such as email and sms, OSS2FA ships with built-in support for Yubikeys, HOTP/TOTP, and FIDO U2F tokens.
- **Extensible** - Adding support for new devices, or adapting behavior of existing modules is as simple as it gets.
- **Integrations** - Use OSS2FA to provide 2FA support for a variety of projects: whether it is a Citrix Netscaler environment, a VPN appliance, or an Identity Management solution, OSS2FA can help.

## Documentation

## Install

Install with Docker:

```bash
docker run --name oss2fa -d oss2fa
```

You should see a command output similar to:

```bash
oss2fa_1  | ===> OSS2FA bootstrap complete!
oss2fa_1  | ===> To get you started, we have created a default tenant and integration.
oss2fa_1  | ===> Integration (name=`Default`, access_key=`1gIlZa2AIJV3bNQP5pLZ89F7gD3PFp0W`, secret_key=`6btwD4cpPsx5y7Gqk19uR6EVapyonkqiHiIQUoOPQwDotJZe`)
```

For your convenience, a default tenant and integration have been created on your behalf.

### Architecture Overview

The oss2fa architecture is composed of a few building blocks.

#### Tenant

The framework ships with built-in support for multi-tenancy. It is a perfect candidate to be used within
corporations where projects are often owned by a large amount of teams.

#### Integration

An integration is an abstraction for an application that is to be protected with oss2fa. For example, an organization
looking to protect its VPN appliances and a web application, will need two integrations. An integration belongs to a tenant.

#### Client

A client is the end-user of the system; it is the individual that is undergoing 2fa.

#### Enrollment

An enrollment is the process of on-boarding a client into an integration.

#### Device

A device is an abstraction of ways which a user can answer a 2fa challenge. For example, an email account,
and a Yubikey token are considered devices within oss2fa.

#### Challenge

A challenge is the process of challenging a client to a 2fa session.


### Example

#### Creating an enrollment

To create an enrollment, use the `/integration/enrollments` endpoint.

You can use clients such as `httpie` to issue the request. By default, http basic authentication is used, however, `oss2fa` comes with other recommended authentication mechanisms. See documentation for those.

```bash
http --verbose -a 1gIlZa2AIJV3bNQP5pLZ89F7gD3PFp0W:6btwD4cpPsx5y7Gqk19uR6EVapyonkqiHiIQUoOPQwDotJZe http://localhost:8000/integration/enrollments username=isaace
```

```json
POST /integration/enrollments HTTP/1.1
Accept: application/json, */*
Accept-Encoding: gzip, deflate
Authorization: Basic MWdJbFphMkFJSlYzYk5RUDVwTFo4OUY3Z0QzUEZwMFc6NmJ0d0Q0Y3BQc3g1eTdHcWsxOXVSNkVWYXB5b25rcWlIaUlRVW9PUFF3RG90Slpl
Connection: keep-alive
Content-Length: 22
Content-Type: application/json
Host: localhost:8000
User-Agent: HTTPie/0.9.8

{
    "username": "isaace"
}
```

The server will respond with an enrollment creation.

```json
HTTP/1.0 201 Created
Allow: POST, OPTIONS
Content-Length: 171
Content-Type: application/json
Date: Sun, 03 Sep 2017 17:08:36 GMT
Server: WSGIServer/0.1 Python/2.7.12
Vary: Accept
X-Frame-Options: SAMEORIGIN

{
    "created_at": "2017-09-03T17:08:36.187498Z",
    "device_selection": null,
    "expires_at": "2017-09-03T17:13:36.187244Z",
    "pk": 2,
    "public_details": null,
    "status": 1,
    "username": "isaace"
}
```

#### Choosing available device types

OSS2FA is a modular system that supports enrollments of multiple type of devices, ranging from phones to TOTP tokens. To add a new device type, see documentation.

To list available devices:

```bash
http  -a 1gIlZa2AIJV3bNQP5pLZ89F7gD3PFp0W:6btwD4cpPsx5y7Gqk19uR6EVapyonkqiHiIQUoOPQwDotJZe get http://localhost:8000/devices-kind
```

```json
GET /devices-kind HTTP/1.1
Accept: */*
Accept-Encoding: gzip, deflate
Authorization: Basic MWdJbFphMkFJSlYzYk5RUDVwTFo4OUY3Z0QzUEZwMFc6NmJ0d0Q0Y3BQc3g1eTdHcWsxOXVSNkVWYXB5b25rcWlIaUlRVW9PUFF3RG90Slpl
Connection: keep-alive
Host: localhost:8000
User-Agent: HTTPie/0.9.8



HTTP/1.0 200 OK
Allow: GET, HEAD, OPTIONS
Content-Length: 51
Content-Type: application/json
Date: Sun, 03 Sep 2017 17:24:34 GMT
Server: WSGIServer/0.1 Python/2.7.12
Vary: Accept
X-Frame-Options: SAMEORIGIN

[
    {
        "description": "OTP Devices",
        "name": "OTP",
        "pk": 1
    }
]
```

#### Choosing to enroll a TOTP device

Once an enrollment is created, the framework needs to know which device will be used to complete the enrollment:

```bash
http -a 1gIlZa2AIJV3bNQP5pLZ89F7gD3PFp0W:6btwD4cpPsx5y7Gqk19uR6EVapyonkqiHiIQUoOPQwDotJZe --verbose http://localhost:8000/integration/enrollments/2/prepare-device kind:=1 options:='{"generate_qr_code": true}'
```

```json
POST /integration/enrollments/2/prepare-device HTTP/1.1
Accept: application/json, */*
Accept-Encoding: gzip, deflate
Authorization: Basic MWdJbFphMkFJSlYzYk5RUDVwTFo4OUY3Z0QzUEZwMFc6NmJ0d0Q0Y3BQc3g1eTdHcWsxOXVSNkVWYXB5b25rcWlIaUlRVW9PUFF3RG90Slpl
Connection: keep-alive
Content-Length: 52
Content-Type: application/json
Host: localhost:8000
User-Agent: HTTPie/0.9.8

{
    "kind": 1,
    "options": {
        "generate_qr_code": true
    }
}

HTTP/1.0 200 OK
Allow: POST, OPTIONS
Content-Length: 2998
Content-Type: application/json
Date: Sun, 03 Sep 2017 17:26:56 GMT
Server: WSGIServer/0.1 Python/2.7.12
Vary: Accept
X-Frame-Options: SAMEORIGIN

{
    "created_at": "2017-09-03T17:08:36.187498Z",
    "device_selection": 1,
    "expires_at": "2017-09-03T17:13:36.187244Z",
    "pk": 2,
    "public_details": {
        "provisioning_uri": "otpauth://totp/oss2fa:isaace?secret=BNVE2U3MKDBXU7IHPEBLC5GIBQ5GB64S&issuer=oss2fa",
        "qr_code": "iVBORw0KGgoAAAANSUhEUgAAAZoAAAGaCAIAAAC5ZBI0AAAHuklEQVR4nO3dQU5kORBAQRhx/ysz216MrJHcJu1HxB6qKODJi0z/jw8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOj6nHrh7+/vqZc+5PNz9WH2ft4d689qx7nP+cX3POXcZ7X2z8irAvx1cgZEyBkQIWdAhJwBEXIGRMgZECFnQIScARFf02/gv01NFa/tTG/fOVN+bpNh5+ddv+7Od35xc6P3v3CO0xkQIWdAhJwBEXIGRMgZECFnQIScARFyBkTIGRBx6VbA2ov3wa9NTfafm7/fMbVBceeOxFrvf2GH0xkQIWdAhJwBEXIGRMgZECFnQIScARFyBkTIGRDx5FZAz53z6Odm6O+8s//F98yfnM6ACDkDIuQMiJAzIELOgAg5AyLkDIiQMyBCzoAIWwEPmJrs3/nOO1/be2IDP8PpDIiQMyBCzoAIOQMi5AyIkDMgQs6ACDkDIuQMiHhyK6A3gf3irfxTGwU7pj7nc3r/CzuczoAIOQMi5AyIkDMgQs6ACDkDIuQMiJAzIELOgIhLtwKmpsbPuXPu/9zOwJ3v+c6vXev9L5zjdAZEyBkQIWdAhJwBEXIGRMgZECFnQIScARFyBkSMbQW44/xPL87uT+lNyd/5Ob/I6QyIkDMgQs6ACDkDIuQMiJAzIELOgAg5AyLkDIgYG0feme0+NyV/533w56bG73zdHVMT9nc+Z+CcO9+z0xkQIWdAhJwBEXIGRMgZECFnQIScARFyBkTIGRBx48Dxx9yM9Z1z/3fO0E99Vms2KH7GnbsKTmdAhJwBEXIGRMgZECFnQIScARFyBkTIGRAhZ0DEpc8KuPPG9ylTWxA77nzdHbZN/j/PCgDYImdAhJwBEXIGRMgZECFnQIScARFyBkTIGRBx44XfH7dOq09Nfq+du1l/akfiznvoX9wYWbvzmQw7nM6ACDkDIuQMiJAzIELOgAg5AyLkDIiQMyBCzoCIr+k38Pe9OPffm88+58XP6sXti/W7uvNZH05nQIScARFyBkTIGRAhZ0CEnAERcgZEyBkQIWdAxNhWwLlJ6BefM3DOnU8S2Pk0XpywP/e1a1P/C1OczoAIOQMi5AyIkDMgQs6ACDkDIuQMiJAzIELOgIgnnxXw4hT1jqmnH9z5bIS1c5/VuZ93avvizj2WHU5nQIScARFyBkTIGRAhZ0CEnAERcgZEyBkQIWdAxNhWwIuT/VO31E/NlO+Ymjh/cZNh7dxex447NwqczoAIOQMi5AyIkDMgQs6ACDkDIuQMiJAzIELOgIhLrwOfmu2emrCfutP9xWcjnDN1K/+d33nNVgDAQXIGRMgZECFnQIScARFyBkTIGRAhZ0CEnAERY88K2PHire3nXnftt20ynJtHf3FX4cXX3eF0BkTIGRAhZ0CEnAERcgZEyBkQIWdAhJwBEXIGRIxtBdw5NX7nZP+5131x4vy3bSOcc+d/yg6nMyBCzoAIOQMi5AyIkDMgQs6ACDkDIuQMiJAzIGJsK+DFKeoXZ8rvvFn/3Lvq/URT3/nOuf81pzMgQs6ACDkDIuQMiJAzIELOgAg5AyLkDIiQMyDivdH8j7k56XPO3cs+tW+wdueU/M7r7ujthExxOgMi5AyIkDMgQs6ACDkDIuQMiJAzIELOgAg5AyLGnhWwM6985z30d96t/uJGwZ2//bVzfxu/bftih9MZECFnQIScARFyBkTIGRAhZ0CEnAERcgZEyBkQMbYVsGNnXnlqPvucF2/H7zn3N7nztVNP1ZjaGXA6AyLkDIiQMyBCzoAIOQMi5AyIkDMgQs6ACDkDIsYu/L5zqnjH1Fz4jnP30E9tFExNuk9tqvR+CzuczoAIOQMi5AyIkDMgQs6ACDkDIuQMiJAzIELOgIhLtwLOmZqiPjet3nvdtd67mvLi7s2a0xkQIWdAhJwBEXIGRMgZECFnQIScARFyBkTIGRBRGwu+1tRd8msv7gz8ttddm3rOwJ0bBU5nQIScARFyBkTIGRAhZ0CEnAERcgZEyBkQIWdAxNfUC794t/raek76zinqc6b2HNbunHS/8129+BfrdAZEyBkQIWdAhJwBEXIGRMgZECFnQIScARFyBkSMbQWs3TmR/OImw7np/J3f0dTd+efe851PEjj3NIA7NxmczoAIOQMi5AyIkDMgQs6ACDkDIuQMiJAzIELOgIhLtwLWzk3n96bVz+nNlJ/7u3rx2Qgv7sA4nQERcgZEyBkQIWdAhJwBEXIGRMgZECFnQIScARFPbgX07Exgn7ulfmqm/MUnGNz5rIAdL+4MOJ0BEXIGRMgZECFnQIScARFyBkTIGRAhZ0CEnAERtgJ+yItPIejp3Z1/7rd/58+75nQGRMgZECFnQIScARFyBkTIGRAhZ0CEnAERcgZEPLkV8OKk+7kZ63P3/e+4c8J+6kkCazu/ozs/5ylOZ0CEnAERcgZEyBkQIWdAhJwBEXIGRMgZECFnQMSlWwG/bZp5bWru/9xN8+d+ot7TANZ23vOL2zVrTmdAhJwBEXIGRMgZECFnQIScARFyBkTIGRAhZwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHC9fwGCF8bgtM93cAAAAABJRU5ErkJggg=="
    },
    "status": 2,
    "username": "isaace"
}
```

Notice that we have requested the framework to generate the QR code on our behalf. It is a base64 encoded PNG image:

![QR Code corresponding to enrollment above](static/docs/img/qr.png "QR Code for Enrollment")

#### Finalizing the enrollment

After importing the token in your favorite authenticator application, you
can proceed to provide the current secret to the enrollment endpoint to finalize the process:

```text
POST /integrations/enrollments/1/complete HTTP/1.1
```

```text
Host: 127.0.0.1:8300
Accept: application/json; version=1.0
X-Integration-Token: CVrMbfDlwm7bRjPOGpb4grz3r9TnVYhEMb0SPe1uC5HsasFd
```

```json
{
  "token": "12345"
}
```

If everything is ok, the framework will return a 201 status, and set a client id header:

```text
Content-Length: 0
Vary: Accept
X-Client-Id: 1
Allow: POST, OPTIONS
X-Frame-Options: SAMEORIGIN
```
