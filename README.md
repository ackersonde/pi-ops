![Deploy Infra scripts to PI](https://github.com/ackersonde/pi-ops/workflows/Deploy%20Infra%20scripts%20to%20PI/badge.svg)

# pi-ops
This repo is a collection of operation scripts I stub out and use for my various websites, bots and infrastructure.

Be sure to read how I [secure deployments to my home](https://agileweboperations.com/2020/11/29/secure-github-deployments-to-your-home/) using the scripts in this repository.

# Building & Running
Every push will redeploy the scripts & reinstall the [crontab](scripts/crontab.txt) to my raspberry pi <img src="https://upload.wikimedia.org/wikipedia/en/thumb/c/cb/Raspberry_Pi_Logo.svg/100px-Raspberry_Pi_Logo.svg.png" width="16"> overseeing the secure operations of my DigitalOcean infrastructure. See the [github action workflow](.github/workflows/build.yml)

# Secret Management: Vault -> Github
It all starts from this [crontab](./scripts/crontab.txt#L8) entry:
`32 * * * * /home/ubuntu/my-ca/update_github_secrets.sh`

After ingesting the requisite environment variables, it calls [vault_update_secrets.py](./scripts/secrets/vault_update_secrets.py) which initially gets the last-modified dates of all my Vault application secrets. Then it goes over to Github and grabs the same data in order to compare which secrets are out-of-sync (meaning updated in Vault where I now manage my secrets).

Updated (or created) secrets are highlighted via Slackbot message with a super helpful pointer to which repos use those secrets (and may need to be redeployed) via `https://api.github.com/search/code?q=org%3Aackersonde+{secret_name}&type=Code`.

Check out the blog post here: XYZ
