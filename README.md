![Deploy Infra scripts to PI](https://github.com/ackersonde/pi-ops/workflows/Deploy%20Infra%20scripts%20to%20PI/badge.svg)

# pi-ops
This repo is a collection of operation scripts I stub out and use for my various websites, bots and infrastructure.

Be sure to read how I [secure deployments to my home](https://agileweboperations.com/2020/11/29/secure-github-deployments-to-your-home/) using the scripts in this repository.

# Building & Running
Every push will redeploy the scripts & reinstall the [crontab](scripts/crontab.txt) to my raspberry pi device overseeing the secure operations of my DigitalOcean infrastructure. See the [github action workflow](.github/workflows/build.yml)
