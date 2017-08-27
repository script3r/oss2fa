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
oss2fa    |               Listener 1: tcp (addr: "0.0.0.0:8300", tls: "enabled")
oss2fa    |                   Tenant: d28dd5a018294562dbc9a18c95554d52b5d12390
oss2fa    |              Integration: d28dd5a018294562dbc9a18c95554d52b5d12390
oss2fa    |                  Version: OSS2FA v1.0
oss2fa    | 
oss2fa    | ==> OSS2FA server started
```

For your convenience, a default integration has been created on your behalf. 

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

To create an enrollment:

```text
POST /integrations/enrollments HTTP/1.1
```

```text
Host: 127.0.0.1:8300
Accept: application/json; version=1.0
X-Integration-Token: d28dd5a018294562dbc9a18c95554d52b5d12390
```


```json
{
  "username": "john.doe"
}
```
