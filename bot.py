import datetime
import os
import threading

import discord
import dotenv
import pagerduty as pd
import requests
from discord.ui import View
from flask import Flask, request, jsonify

import account

dotenv.load_dotenv()

pagerduty = pd.RestApiV2Client(os.getenv('PAGERDUTY_API_KEY'), default_from=os.getenv('PAGERDUTY_DEFAULT_EMAIL'))
pagerduty.url = os.getenv('PAGERDUTY_URL')

app = Flask(__name__)
token = str(os.getenv("DISCORD_BOT_TOKEN"))

bot = discord.Bot()

def get_incident_by_id(incident_id: str) -> dict:
    reponse = pagerduty.get(f'incidents/{incident_id}')
    reponse.raise_for_status()

    return reponse.json()['incident']

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    channel = bot.get_channel(int(os.getenv('DISCORD_CHANNEL_ID')))

    event = request.json
    incident_id = event['data']['number']

    incident = get_incident_by_id(incident_id)
    status = incident['status']

    created_at = datetime.datetime.strptime(incident['created_at'], "%Y-%m-%dT%H:%M:%SZ")
    last_action_date = datetime.datetime.strptime(event['occurred_at'], "%Y-%m-%dT%H:%M:%SZ")

    acknowledged_at = "N/A"
    acknowledgement_time = "N/A"

    if len(incident['acknowledgements']) > 0:
        acknowledged_at = datetime.datetime.strptime(incident['acknowledgements'][0]['at'], "%Y-%m-%dT%H:%M:%SZ")
        acknowledgement_time = created_at - acknowledged_at

    if incident['resolved_at'] is not None:
        duration = datetime.datetime.strptime(incident['resolved_at'], "%Y-%m-%dT%H:%M:%SZ")

    embed = discord.Embed()
    embed.url = event['data']['url']
    embed.set_author(
        name="Pagerduty",
        url="https://gladhost.pagerduty.com/incidents",
        icon_url="https://www.pagerduty.com/wp-content/themes/citizens-band/favicon/icons/apple-touch-icon.png"
    )

    acknowledge = discord.ui.Button(label="Acknowledge" if status == "triggered" else "Re-assign")
    resolve = discord.ui.Button(label="Resolve")

    async def acknowledge_callback(interaction):
        try:
            pagerduty.put(f"incidents/{incident_id}", {
                "incident": {
                    "status": "acknowledged",
                }
            }, headers={"From": account.get_pagerduty_account(interaction.user.id)}).raise_for_status()
        except requests.exceptions.HTTPError as exception:
            await interaction.response.send_message(f"unable to acknowledge incident '{incident_id}': {exception.response.text}", ephemeral=True)
        except ValueError as exception:
            await interaction.response.send_message(f"⛔️Your account is not linked to Pagerduty': {exception.response.text}", ephemeral=True)

    async def resolve_callback(interaction):
        try:
            pagerduty.put(f"incidents/{incident_id}", {
                "incident": {
                    "status": "acknowledged",
                }
            }, headers={"From": account.get_pagerduty_account(interaction.user.id)}).raise_for_status()
        except requests.exceptions.HTTPError as exception:
            await interaction.response.send_message(f"unable to acknowledge incident '{incident_id}': {exception.response.text}", ephemeral=True)
        except ValueError as exception:
            await interaction.response.send_message(f"⛔️Your account is not linked to Pagerduty': {exception.response.text}", ephemeral=True)

    acknowledge.callback = acknowledge_callback
    resolve.callback = resolve_callback

    view = View()

    embed.title = f"[#{incident_id}] {incident['status'].title()} - {incident['title']}"

    match event['event_type']:
        case 'incident.triggered':
            embed.colour=0xf50202
            embed.description=(f"""
            Service: Prometheus alertmanager
            Created at: {last_action_date}
            Status: {status}
            """)
            view.add_item(acknowledge)
            view.add_item(resolve)

        case 'incident.acknowledged':
            embed.colour=0xff9e68
            embed.description = (f"""
            Service: Prometheus alertmanager
            Created at: {last_action_date}
            Status: {status}
            Acknowledged by: {incident['acknowledgements'][-1]['acknowledger']['summary']}
            Acknowledged at: {acknowledged_at}
            GTI: {acknowledgement_time}
            """)
            view.add_item(acknowledge)
            view.add_item(resolve)

        case 'incident.resolved':
            embed.colour=0x3cff00
            embed.description = (f"""
                Service: Prometheus alertmanager
                Created at: {last_action_date}
                Status: {status}
                Acknowledged by: {incident['acknowledgements'][-1]['acknowledger']['summary']}
                Acknowledged at: {acknowledged_at}
                GTI: {acknowledgement_time}
                GTR: {duration}
                """)

        case _:
            print("unsupported event: ")

    async def send_to_discord():
        await channel.send(embed=embed, view=view)

    bot.loop.create_task(send_to_discord())

    return jsonify({'status': 'OK'}), 200

@bot.slash_command() # Create a slash command
async def pagerduty_associate_account(ctx, pagerduty_email: str):
    try:
        account.get_pagerduty_account(ctx.author.id)
        await ctx.respond("✅ Your discord account is already associated to a pagerduty account.")
    except ValueError:
        account.create_account(ctx.author.id, pagerduty_email)
        await ctx.respond("✅ Successfully linked your discord account to your pagerduty account")

account.init_accounts_csv()

def run_flask():
    app.run(host='0.0.0.0', port=8000)

threading.Thread(target=run_flask).start()
bot.run(token)
