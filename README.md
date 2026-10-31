# VideoHub
<p align="center">
    <a href="href="https://github.com/ID24-CMR/video_platform/issues" title="Open Issues"><img src="https://img.shields.io/github/issues/ID24-CMR/video_platform?style=flat-square"></a>
    <a href="href="https://github.com/ID24-CMR/video_platform/LICENSE" title="Open License"><img src="https://img.shields.io/github/license/ID24-CMR/video_platform"></a>
<a href="href="https://github.com/ID24-CMR/video_platform/BUILD" title="Open build"><img src="https://img.shields.io/github/v/release/ID24-CMR/video_platform"></a>
<a href="href="https://github.com/ID24-CMR/video_platform/BUILD" title="Open build"><img src="https://img.shields.io/github/v/tag/ID24-CMR/video_platform"></a>
<a href="href="https://github.com/ID24-CMR/video_platform/BUILD" title="Open build"><img src="https://img.shields.io/github/commit-activity/w/ID24-CMR/video_platform"></a>
<a href="href="https://github.com/ID24-CMR/video_platform/BUILD" title="Open build"><img src="https://img.shields.io/github/languages/code-size/ID24-CMR/video_platform"></a>
<a href="href="https://github.com/ID24-CMR/video_platform/BUILD" title="Open build"><img src="https://img.shields.io/github/repo-size/ID24-CMR/video_platform"></a>
<a> <img src="https://img.shields.io/github/issues-closed/ID24-CMR/video_platform"></a>
[![VideoHub CI](https://github.com/ID24-CMR/video_platform/actions/workflows/ci.yml/badge.svg)](https://github.com/ID24-CMR/video_platform/actions/workflows/ci.yml)
</p>
<p align="center">
    <a href="#development">Development</a>.
    <a href="#service-apis">Service APIs</a>.
	<a href="#documentation">Documentation</a>.
	<a href="#support-and-feedback">Support</a>.
	<a href="#how-to-contribute">Contribute</a>.
	<a href="#contributors">Contributors</a>.
	<a href="#repositories">Repositories</a>.
	<a href="#licensing">Licensing</a>
</p>

## Intro

DEMO [link.......](https://video-platform-fort.onrender.com/)

## Architecture Overview
You can find the architecture overview [here](documents/architecture-overview.md), which will give ou a good starting point in how the backend services interact with other services, and purpose the serve.

## Documentation
The full documentation of this software can be found in the [sms-documentation](https://) repository. The documentation repository contains technical documents, architecture information, and whitepapers related to this implementation.

## Support-and-feedback
The following channels are available for discussions, feedback, and support requests:
|Type							| Channels 																|
|-------------------------------|-----------------------------------------------------------------------|
| **General Discussion** | <a href="https://github.com/ID24-CMR/video_platform/issues/new" title="General Discussion"><img src="https://img.shields.io/badge/ID24-CMR-issues-blue"></a></a> |
| **Concept Feedback**	 | <a href="https://github.com/ID24-CMR/video_platform/issues/new"><img src="https://img.shields.io/badge/ID24-CMR-issues-blue"></a></a> |
| **Backend Issue**		 | <a href="https://github.com/ID24-CMR/video_platform/issues/new" title="Open Issues"><img src="https://img.shields.io/github/issues/ID24-CMR/video-platform?style=flat-square "></a> |
| **Other Requests**	 | <a href="idrice.tsafouet@yahoo.com" title="Email ID24-CMR Team"><img src="https://img.shields.io/badge/ID24-CMR-issues-blue"></a></a> |

## How to Contribute
Contributors and feedback are encouraged and welcome. For more information about how to contribute, the project structure, as well as additional contribution information, see our [Contributors Guidelines](./CONTRIBUTING.md). By participating in this project, you agree to abide by its [Code of Conduct](./CODE:OF_CONDUCT.md) at all times.

## Contributors
- ID24-CMR
## Repositories
The following public repositories are currentl available for the School Management System:
| Repository		|Description																		|
| ------------------|-----------------------------------------------------------------------------------|
|[mtp-documentation]| Project overview, general documentation, and white papers (report)				|
|[mtp-server]		| Backend implementation for the Google exposure APIs 								|
|[mtp-verification-server]| Backend Implomentation of the verication process							|

## Liecensing
Copyright (c) 2020 ID24-CMR company.
Licensed under the **Apache License, Version 2.0** (the "License"); you may not use this file except in compliance with the License.
You may obtain a copy of the License at linkhere.
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" basis, without warranties or condition of any kind, either express or implied. see [LICENSE](./LICENSE) for the specific language governing permisssions and limitations under the License.

## Technologies (IDE) client/server
# Server Side
# client Side
## Development
The project is created with Maven, so you just need to import it to your IDE and build the project to resolve the dependencies

## Service-apis

## Repositories

# Project Structure

video_platform/
│
├── manage.py
├── requirements.txt
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── accounts/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
│
├── videos/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── admin.py
│
├── payments/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── webhooks.py
│
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── accounts/
│   └── videos/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
└── media/ 

[![VideoHub CI](https://github.com/ID24-CMR/video_platform/actions/workflows/ci.yml/badge.svg)](https://github.com/ID24-CMR/video_platform/actions/workflows/ci.yml)