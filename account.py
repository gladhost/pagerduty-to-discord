"""
This module maintain relation between discord user and pagerduty email address
"""
import csv
import os


def init_accounts_csv():
    if not os.path.exists('accounts.csv'):
        print('initializing empty accounts.csv')
        with open("accounts.csv", mode='w') as file:
            writer = csv.DictWriter(file, fieldnames=['discord_account', 'pagerduty_email'])
            writer.writeheader()

def open_csv(file_name) -> list:
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def get_pagerduty_account(discord_account: str) -> str:
    accounts = open_csv("accounts.csv")
    for account in accounts:
        if account['discord_account'] == discord_account:
            return account['pagerduty_email']

    raise ValueError(f"No pagerduty account linked with discord account: '{discord_account}'")

def create_account(discord_account: str, pagerduty_email: str):
    accounts = open_csv("accounts.csv")
    accounts.append({
        'discord_account': discord_account,
        'pagerduty_email': pagerduty_email
    })
    with open("accounts.csv", mode='w') as file:
        writer = csv.DictWriter(file, fieldnames=['discord_account', 'pagerduty_email'])
        writer.writeheader()
        writer.writerows(accounts)
