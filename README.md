# PagerDuty to Discord

This repository permit to convert PagerDuty webhook v3 into Discord webhook

## Usage

1. Configure your `.env` file
2. Configure your `compose.yml` to use `gladhost/
3. Run the containers

## Volumes

- accounts.csv contains an association f

## Requirements

- Python >= 3.13
- Docker

## Contribution

Feel free to contribute on this project.

Some webhooks are not yet handled such as escalation, but when a not hanlded webhook is recieved, they printed to
the console.

## Screenshots

![Screenshot of notifications](screenshots/discord-messages.png "Screenshots of notifications")

## Licence

Creative Commons Attribution-NonCommercial 4.0 International License
