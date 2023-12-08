# <img src="https://github.com/BaCa2-project/.github/blob/main/profile/baca2_logo.png" alt="BaCa2 Logo" width="200"/>

Welcome to the [BaCa2](https://github.com/BaCa2-project) project web application component. This Django-based web app is designed to provide an online platform for creating and managing programming tasks, as well as submitting solutions for automatic evaluation. The system revolves around the concept of courses which are used to organize groups of users into roles and provide them with access to a curated list of tasks designed by course leaders.

Currently developed for the [Institute of Computer Science and Mathematics](https://ii.uj.edu.pl/en_GB/start) at the Jagiellonian University

## Overview

This repository represents the web application component of the BaCa2 Project, a collaborative effort to develop a comprehensive online system for creating programming tasks and automating the validation of submitted solutions. For a broader understanding of the project and its goals, please refer to the [project README](https://github.com/BaCa2-project/.github/blob/main/profile/README.md).

## Project Structure

The Django project is organized into three main apps:

1. **`main`** - responsible for authentication, user data and settings, management of courses and their members

2. **`course`** - responsible for management of tasks, submissions and other data and functionalities internal to any given course

3. **`package`** - used to represent to communicate with BaCa2-package-manager and represent its packages within the web app

## Contributors

The BaCa2 web application component is currently being developed by 2 members of the project team:

<a href="https://github.com/k-kalita">
  <img src="https://avatars.githubusercontent.com/u/116686132?v=4" width="70" height="70" align="left" alt="krzysztof-kalita-pfp"/>
</a>

**`Krzysztof Kalita`**<br>
Main team member responsible for BaCa2 web app development, working on both backend and frontend. Responsible for the `main` app, views, widgets and backend-frontend communication.

<a href="https://github.com/ZyndramZM">
  <img src="https://avatars.githubusercontent.com/u/71557281?v=4" width="70" height="70" align="left" alt="bartosz-deptula-pfp"/>
</a>

**`Bartosz Deptuła`**<br>
Responsible for the `course` and `package` app backend, as well as custom database router used to dynamically create databases for new courses and route between them.

## License

The BaCa2 Project is licensed under the [GPL-3.0 license](LICENSE).
