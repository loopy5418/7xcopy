import asyncio
import base64
import json
import os
import random
import string
from datetime import datetime
from typing import Optional

import discord
from discord.channel import TextChannel
import openai
import requests
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument, has_any_role
# from discord_slash.utils.manage_commands import create_choice, create_option
from interactions.ext.hybrid_commands import hybrid_slash_command
from replit import db

bot_start_time = datetime.now()

def get_uptime():
    delta = datetime.now() - bot_start_time
    return str(delta)  

def days_until_christmas():
  today = datetime.now()
  christmas = datetime(today.year, 12, 25)
  if today > christmas:
    christmas = datetime(today.year + 1, 12, 25)

  delta = christmas - today
  return delta.days

status_hold = False
temporary_status = None
temporary_status_time = None
ecancel = False
shutdown_in_progress = False
status_queue = []
new_status = f"{days_until_christmas()} Days until Christmas!"
status_hold = False
my_secret = os.environ['BOT_KEY']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
ND_API_KEY = os.environ['ND_API_KEY']
openai.api_key = os.getenv(OPENAI_API_KEY)
nd_api_key = os.getenv(ND_API_KEY)
fallback_model = "gpt-3.5-turbo-1106"
openai.api_key = OPENAI_API_KEY
def get_build_id():
  # This could be a Git commit hash, tag, or a simple counter
  return "v1.0.123"
os.system('cls' if os.name == 'nt' else 'clear')

tips = [
    "Did you know? Of course you didn't.", "Run 7/help for help", "Made by UN7X",
    "Thank you to 7x's beta testers!", "Want your message on here? Ping @UN7X",
    "Hiya!", "Blaze_is_Tiny = True", "Hello, world!", ":3", "I'm alive!", "You", "For 7/ commands", "awa"
]

intents = discord.Intents.default()
intents.message_content = True  # Ensure this is set to True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("7/"),
                   intents=intents,
                   case_insensitive=True,
                   help_command=None)

@bot.group(invoke_without_command=True)
async def beta(ctx, option: str = None):
    if option is None:
        await ctx.send("Please provide a valid option: tester, info")
    elif option == "info":
        await ctx.send(f"Build ID: {get_build_id()} | Uptime: {get_uptime()}")
    elif option == "tester":
        await ctx.invoke(bot.get_command('beta tester'))

@bot.group(name="tester", invoke_without_command=True)
@commands.is_owner()
async def beta_tester(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("Valid subcommands are: add, remove, list")
@beta_tester.command(name="add")
async def beta_tester_add(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Please specify a member to add as a beta tester.")
        return
    role = discord.utils.get(ctx.guild.roles, name="7x Waitlist")
    if role:
        await member.add_roles(role)
        await ctx.send(f"Added {member.mention} as a beta tester.")
    else:
        await ctx.send("Role '7x Waitlist' not found.")

@beta_tester.command(name="remove")
async def beta_tester_remove(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Please specify a member to remove from beta testers.")
        return
    role = discord.utils.get(ctx.guild.roles, name="7x Waitlist")
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"Removed {member.mention} from beta testers.")
    else:
        await ctx.send(f"{member.mention} is not a tester.")

@beta_tester.command(name="list")
async def beta_tester_list(ctx):
    role = discord.utils.get(ctx.guild.roles, name="7x Waitlist")
    if role:
        testers = [member.mention for member in role.members]
        await ctx.send("Beta Testers: " + ", ".join(testers))
    else:
        await ctx.send("No beta testers found.")

@bot.command(name="query-status")
@has_any_role("7xControlPass", "Canis", "Xar")
async def query_status(ctx, *, messages: str):
    global status_queue

    # Split the messages by quotes and filter out any empty strings
    messages_list = [msg for msg in messages.split('"') if msg.strip()]
    status_queue.extend(messages_list)

    await ctx.send(f"Queued {len(messages_list)} statuses.")

@bot.command(name="force-status")
@has_any_role("7xControlPass", "Canis", "Xar")
async def force_status(ctx, *, status: str):
  global status_hold, temporary_status, temporary_status_time

  # Check for the '-indf' flag
  if '-indf' in status:
    status_hold = True  # Hold this status indefinitely
    status = status.replace('-indf', '').strip()  # Clean the status message
  else:
    status_hold = False  # Do not hold status indefinitely

  # Update the bot's presence
  await bot.change_presence(activity=discord.Activity(
      type=discord.ActivityType.watching, name=status))

  # If not indefinite, set a temporary status and record the time
  if not status_hold:
    temporary_status = status
    temporary_status_time = datetime.now()
    await asyncio.sleep(10)  # Wait for 10 seconds before clearing the temporary status
    temporary_status = None
    temporary_status_time = None

  await ctx.send(f"Status changed to: {status}")


async def change_status_task():
  global status_hold, temporary_status, temporary_status_time, status_queue
  last_status = None

  while True:
    if temporary_status and (datetime.now() - temporary_status_time).seconds > 10:
      temporary_status = None

    if status_hold:
      await asyncio.sleep(10)
    elif temporary_status:
      await bot.change_presence(activity=discord.Activity(
          type=discord.ActivityType.watching, name=temporary_status))
      await asyncio.sleep(10)
    elif status_queue:
      next_status = status_queue.pop(0)
      await bot.change_presence(activity=discord.Activity(
          type=discord.ActivityType.watching, name=next_status))
      await asyncio.sleep(10)
    else:
      new_status = random.choice(tips)
      while new_status == last_status:
        new_status = random.choice(tips)
      await bot.change_presence(activity=discord.Activity(
          type=discord.ActivityType.watching, name=new_status))
      last_status = new_status
      await asyncio.sleep(10)


shop_items = {
    'item1': {
        'price': 100,
        'description': 'Item 1 Description'
    },
    'item2': {
        'price': 200,
        'description': 'Item 2 Description'
    },
    # Add more items as needed
}


@bot.command(name="shop")
async def shop(ctx):
  embed = discord.Embed(title="7x Shop",
                        description="Available items to purchase with points:",
                        color=0x00ff00)
  for item_id, details in shop_items.items():
    embed.add_field(name=f"{item_id} - {details['price']} points",
                    value=details['description'],
                    inline=False)
  await ctx.send(embed=embed)

###@hybrid_slash_command(
  #name="whisper",
  #description="Whisper a message to a user or accept a whisper.",
  #options=[
   # Option(
  #    name="action",
   #   description="Choose to send or accept a whisper.",
  #    type=OptionType.STRING,
   #   required=True,
    #  choices=[
     #   OptionChoice(name="send", value="send"),
     #   OptionChoice(name="accept", value="accept")
  #    ]
   # ),
  #  Option(
  #    name="message",
  #    description="The message to whisper if action is send.",
  #    type=OptionType.STRING,
   #   required=False
   # ),
  #  Option(
  #    name="member",
  #    description="The member to send the whisper to if action is send.",
  #    type=OptionType.USER,
  #    required=False
 #   )
 # ]
#)
#async def whisper(ctx, action: str, message: Optional[str] = None, member: Optional[discord.Member] = None):
 # bot_channel = discord.utils.get(ctx.guild.text_channels, name='bot-channel')
  #if action == 'send' and message and member:
     # await bot_channel.send(f'{member.mention}, you have a pending whisper message! Use `/whisper accept` to view it.')
     # db[f'whisper-{member.id}'] = {'author': ctx.author.display_name, 'message': message}
     # await ctx.send(f'Whisper message to {member.display_name} sent successfully.')
#  elif action == 'accept':
    #  whisper_data = db.get(f'whisper-{ctx.author.id}')
    #  if whisper_data:
       #   await ctx.send(f"*{whisper_data['author']} whispers to you: {whisper_data['message']}*")
      #    del db[f'whisper-{ctx.author.id}']
     # else:
     #     await ctx.send('You have no pending whisper messages.')
#  else:
    #  await ctx.send('Invalid action or missing parameters. Use `/whisper send <message> <member>` to send a whisper or `/whisper accept` to accept a whisper.')
#@whisper.error
#async def whisper_error(ctx, error):
#  if isinstance(error, commands.MissingPermissions):
    #  await ctx.send("You don't have permission to use this command.")
#  else:
  #    raise error
    
@bot.command(
    name="fillerspam",
    aliases=["fs"],
    help="Creates a channel and generates spam test messages. DEVS ONLY")
@has_any_role("7xControlPass", "Canis", "Xar")
async def filler_spam(ctx):

  new_channel = await ctx.guild.create_text_channel("test-http-channel")

  for _ in range(10):
    gibberish = ''.join(
        random.choices(string.ascii_letters + string.digits, k=20))
    await new_channel.send(gibberish)

  await ctx.send(
      f"Channel {new_channel.mention} created and filled with test messages.")


@bot.command(name="spamping",
             help="Spam pings a user a specfied amount.",
             usage="7/spam-ping <user> <amount>")
@has_any_role("7xControlPass", "Canis", "Xar", "7x Waitlist")
async def spamping(ctx,
                   member: Optional[discord.Member] = None,
                   *,
                   ping_count: Optional[int] = None):
  await ctx.message.delete()

  if member is None:
    await ctx.send("Please specify a user to ping.")
    return

  if ping_count is None:
    ping_count = 5
  if ping_count > 25:
    ping_count = 25
  for i in range(ping_count):
    if ecancel is False:
      await ctx.send(f"{member.mention} | {i+1}/{ping_count} Pings left")
      await asyncio.sleep(1)
    else:
      await ctx.send("Spam pings cancelled.")
      return


@bot.command()
async def cancel(ctx, ecancel: bool = False):
  if ecancel is True:
    ecancel = False
  elif ecancel is False:
    ecancel = True
  else:
    await ctx.send("Invalid option.")
    return
  await ctx.send(f"ecancel set to {ecancel}")


@bot.command(name="help")
async def help_command(ctx):
  embed = discord.Embed(title="7x Command List",
                        description="List of available commands:",
                        color=0x00ff00)
  for command in bot.commands:
    command_usage = f"7/{command.name} {' ' + command.usage if command.usage else ''}"  # Correct command usage display
    embed.add_field(name=command_usage,
                    value=command.help or "No description provided.",
                    inline=False)
  await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, MissingRequiredArgument):
    command = ctx.command
    await ctx.send(f"""
        Missing required argument for {command.name}: {error.param.name}. Usage: {command.usage}
        """)


tc_explanation = """
***Info:***
This will make 7x send a "Success" message to check 
if 7x can send a message in that channel.

**Usage:** 
`7/tc {end}`

**Example:**
`7/tc`

***Tip:***
- Don't try to add any arguments, none, except help, are supported.
"""


@bot.command(name='TC',
             ignore_extra=False,
             help="This command tests if 7x can send a message in a channel.",
             usage="7/tc")
async def tc_command(ctx, *args):
  if 'help' in args or not args:
    embed = discord.Embed(title="TC Command Help",
                          description=tc_explanation,
                          color=0x00ff00)
    await ctx.send(embed=embed)
  else:
    await ctx.send("Success")


@bot.command()
@commands.is_owner()
async def shutdown(ctx, *args):
  global shutdown_in_progress

  if '-e' in args:
    await ctx.send("Shutting down...")
    await bot.close()

  if shutdown_in_progress:
    shutdown_in_progress = False
    await ctx.send("Shutdown sequence halted.")
    return

  shutdown_in_progress = True
  countdown_message = await ctx.send(
      "! - Shutdown Sequence Initiated: (--s) Run 7/shutdown again to cancel.")

  for i in range(10, 0, -1):
    if not shutdown_in_progress:
      return
    await countdown_message.edit(
        content=
        f"! - Shutdown Sequence Initiated: ({i}s) Run 7/shutdown again to cancel."
    )
    await asyncio.sleep(1)

  if shutdown_in_progress:
    await countdown_message.edit(
        content="! - Shutdown Sequence Initiated: (0s)")
    await asyncio.sleep(0.5)
    await countdown_message.edit(
        content="! - Shutdown Sequence Finished - 7x Shut Down.")
    await bot.close()

  shutdown_in_progress = False


@bot.event
async def on_ready():
  print(f'Logged in as {bot.user.name}')
  print(f'With ID: {bot.user.id}')
  print('------')
  bot.loop.create_task(change_status_task())
  channel = bot.get_channel(1177466194677202964)
  if channel and channel == TextChannel:
    await channel.send("""
      7x - Now listening for commands! 
    """)


# Function to encode images in Base64
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    print(f"Encoding image {image_path}")
    return base64.b64encode(image_file.read()).decode("utf-8")


# Function to save messages to Replit Database
def save_message(guild_id, user_id, message):
  key = f"{guild_id}-{user_id}"
  messages = db.get(key, [])
  messages.append(message)
  db[key] = messages
  print(messages)


# Function to retrieve messages from Replit Database
def get_messages(guild_id, user_id):
  key = f"{guild_id}-{user_id}"
  print(f"Key: {key}")
  return db.get(key, [])


# Function to call OpenAI's API
def call_openai(prompt, model):
  response = openai.Completion.create(engine=model,
                                      prompt=prompt,
                                      max_tokens=150,
                                      temperature=0.7,
                                      top_p=1,
                                      frequency_penalty=0,
                                      presence_penalty=0)
  print(response)
  return response.choices[0].text.strip()


# Function to call OpenAI's API
def call_openai(prompt, model):
  response = openai.Completion.create(engine=model, prompt=prompt, max_tokens=150,
                                          temperature=0.7, top_p=1, frequency_penalty=0, presence_penalty=0)
  return response.choices[0].text.strip()

# Main function to process queries
async def process_query(messages, image_path=None):
  if image_path:
    # If there's an image, encode it and prepare the message
    encoded_image = encode_image(image_path)
    messages.append({"role": "system", "content": f"data:image/jpeg;base64,{encoded_image}"})

  # Prepare payload for ND API
  payload = json.dumps({"messages": messages, "fallback_model": "gpt-3.5-turbo"})
  headers = {"Authorization": f"Bearer {ND_API_KEY}", "Content-Type": "application/json"}

  # Make request to ND API
  response = requests.post("https://not-diamond-backend.onrender.com/modelSelector/", headers=headers, data=payload).json()
  model = response.get("model", "gpt-3.5-turbo")
  response.get("token_estimate")

  # Select the appropriate model based on the ND API's response
  openai_model = "gpt-3.5-turbo-1106"  # default
  if model == "gpt-3.5":
    openai_model = "gpt-3.5-turbo-1106"  # GPT-3.5 (Standard)
  elif model == "gpt-4" and image_path is None:
    openai_model = "gpt-4-1106-preview"  # GPT-4 (Turbo)
  elif model == "gpt-4" and image_path is not None:
    openai_model = "gpt-4-1106-vision-preview"  # GPT-4 Vision (Turbo Vision)

  # Retrieve the current conversation from the database
  guild_id = messages[0]['guild_id']
  user_id = messages[0]['user_id']
  get_messages(guild_id, user_id)

  # Add the new message to the conversation and save it
  save_message(guild_id, user_id, messages[-1])

  # Create the prompt from the conversation history
  prompt = " ".join(msg['content'] for msg in messages)
  response_text = call_openai(prompt, openai_model)

  return response_text, openai_model


def check_points(user_id):
  print("Checking points...")
  return db.get(f"points_{user_id}", 0)


def update_points(user_id, points):
  current_points = check_points(user_id)
  new_points = max(current_points + points, 0)
  db[f"points_{user_id}"] = new_points
  print("Updated points for user", user_id, "to", new_points)

ai_explanation = """
***Info:***
Interacts with an advanced AI to simulate conversation or answer queries. Costs points based on the complexity and model used.
Your queries will be processed based on its complexity, then sent to an approriate model.
If an image is sent, it will automatically use the Turbo GPT-4 Vision model.
- Normal conversation maintains context for a more coherent interaction.
- Optional flag `-s` for a standalone query without context, which costs fewer points.

**Usage:** 
`7/ai "<message>"` (Engages in a contextual conversation. Costs more points based on the AI model used.)
`7/ai "<message>" -s` (Engages in a standalone query without considering conversation history. Costs fewer points.)

**Examples:**
`7/ai "What is the capital of France?"` (Contextual conversation)
`7/ai "What is the capital of France?" -s` (Standalone query)

***Cost:***
- **GPT-3.5 (Standard)**: 10 points per use.
- **GPT-4 (Turbo)**: 20 points per use.
- **GPT-4 Vision (Turbo Vision)**: 30 points per use.
- **Discount for '-s' flag**: 50% off the above prices.

***Tips:***
- Use the `-s` flag for quick queries when you don't need the context of a conversation. It saves your points.
- Ensure you have enough points before using the command. You can earn points by participating in the server and using other features.
- The AI's response quality and understanding may vary based on the auto-selected model by the complexity of your query.
"""

@bot.command(name="ai", usage="7/ai <message> <optional flag: -s>", aliases=["ai_bot"], help=ai_explanation)
async def ai_command(ctx, *, message: str):
  print(message)
  user_id = str(ctx.author.id)
  guild_id = str(ctx.guild.id)
  standalone = '-s' in message
  message_content = message.replace('-s', '').strip()
  if message is None:
    await ctx.send("Invalid usage. For detailed help, type: `7/ai help`")
  elif message.lower() == "help":
    embed = discord.Embed(title="AI Command",
                          description=ai_explanation,
                          color=0x00ff00)
    await ctx.send(embed=embed)
  # Define the base cost for each model
  model_costs = {
      'text-davinci-003': 10,  # GPT-3.5 cost
      'gpt-4-1106-preview': 20,  # GPT-4 cost
      'gpt-4-1106-vision-preview': 30  # GPT-4 Vision cost
  }

  conversation = get_messages(guild_id, user_id)

  if standalone:
    # If standalone, don't consider historical context
    response, model_used = await process_query([{
    "role": "user",
    "content": message_content
  }])
    print("s")
  else:
    print("n-s")
    conversation.append({"role": "user", "content": message_content})
    save_message(guild_id, user_id, {
      "role": "user",
      "content": message_content
    })

    response, model_used = await process_query(conversation)
    print(response)
  # Determine the cost based on the model used
  cost = model_costs.get(model_used,
                         10)  # Default to 10 points if the model isn't found

  # Discount for standalone queries
  if standalone:
    cost = int(cost * 0.5)  # 50% discount for standalone queries

  user_points = check_points(user_id)

  if user_points >= cost:
    update_points(user_id, -cost)  # Deduct the cost from the user's points
    await ctx.send(response)
  else:
    await ctx.send(
        f"You don't have enough points for this operation. This operation costs {cost} points, but you only have {user_points}."
    )


http_explanation = """
***Info:***
Deletes messages or entire channels based on flags.
- `-rm` deletes the channel.
- `-rmc` deletes and recreates the channel.
- `-num` deletes a specified number of recent messages.

**Usage:** 
`7/http -rm` (Deletes the channel)
`7/http -rmc` (Deletes and recreates the channel)
`7/http -num <number>` (Deletes the specified number of messages)

**Examples:**
`7/http -rm`
`7/http -rmc`
`7/http -num 10`

***Tips:***
- Use `-rm` with caution; it can't be undone.
- The `-num` flag is useful for bulk message deletion.
"""


@bot.command(help="This command deletes messages or entire channels.",
             usage="7/http -rm / -rmc / -num <number>")
@has_any_role('7xControlPass', 'Canis', 'Xar')
async def http(ctx, *args):
  # Initialization of the flag
  http_ap_ip = True

  # Check for no flags - default action with confirmation
  if not args:
    confirmation_msg = await ctx.send(
        "This will delete all messages in this channel. Are you sure? (Y/N) (--s)"
    )
    for i in range(30, 0, -1):
      if not http_ap_ip:
        return
      await confirmation_msg.edit(
          content=
          f"This will delete all messages in this channel. Are you sure? (Y/N) ({i}s)"
      )
      await asyncio.sleep(1)

    def check(m):
      return m.author == ctx.author and m.channel == ctx.channel

    try:
      confirmation = await bot.wait_for('message', timeout=30.0, check=check)
    except asyncio.TimeoutError:
      await ctx.send("Operation canceled due to timeout.")
      return
    if confirmation.content.lower() not in ["y", "yes"]:
      await ctx.send("Operation canceled.")
      http_ap_ip = False
      return

    # Proceed with the default action (e.g., delete all messages)
    await ctx.channel.purge(limit=None)
    await ctx.send("All messages deleted.")

  # Check for specific flags and malformed command
  elif ("-rm" not in args and "-rmc" not in args and "-num" not in args):
    await ctx.send("Invalid usage. For detailed help, type: `7/http help`")
    return

  if "-rm" in args or "-rmc" in args:
    channel = ctx.channel
    channel_category = channel.category
    channel_name = channel.name
    channel_position = channel.position
    channel_topic = channel.topic

    # Delete the original channel
    await channel.delete(reason="7/http command with -rm or -rmc flag")

    # Create a copy of the channel if -rmc flag is used
    if "-rmc" in args:
      await channel_category.create_text_channel(
          name=channel_name,
          topic=channel_topic,
          position=channel_position,
          reason="7/http command with -rmc flag")

    return

  # Check for '-num' flag and get the number of messages to delete
  if "-num" in args:
    try:
      num_index = args.index("-num") + 1
      num_messages = int(args[num_index])
      await ctx.channel.purge(limit=num_messages + 1)
    except (ValueError, IndexError):
      await ctx.send("No Number Specified, please try again.")
    return

  # Default action: delete all messages in the channel
  await ctx.channel.purge(limit=None)
  await ctx.send("All messages deleted.")


sudo_explanation = """
***Info:***
This will copy the display name and the profile picture of a 
mentioned user and make it into a fake bot account 
that sends a custom specified message.

**Usage:** 
`7/sudo <@username> <custom message> {end}`

**Example:**
`7/sudo @7x Hello World!`

***Tip:***
- Don't use a role in place of @username, it will not work.
"""


@bot.command(help="This command impersonates someone",
             usage="7/sudo @username <message>")
@has_any_role('7xControlPass', 'Canis', 'Xar', "7x Waitlist")
async def sudo(ctx,
               member: Optional[discord.Member] = None,
               *,
               message: Optional[str] = None):
  if message and message.lower() == "help":
    embed = discord.Embed(title="Sudo Command",
                          description=sudo_explanation,
                          color=0x00ff00)
    await ctx.send(embed=embed)
  elif member is None or message is None:
    await ctx.send(
        "Usage: `7/sudo @user <message>` or `7/sudo help` for more info.")
  elif member and message:
    try:
      # Delete the command message first
      await ctx.message.delete()

      # Create a webhook
      webhook = await ctx.channel.create_webhook(name="SudoWebhook")

      # Check if the member has an avatar and get the URL
      avatar_url = member.avatar.url if member.avatar else None

      # Send the message through the webhook
      await webhook.send(content=message,
                         username=member.display_name,
                         avatar_url=avatar_url)

      # Delete the webhook immediately after sending the message
      await webhook.delete()

    except Exception as e:
      await ctx.send(f"An error occurred: {e}")


poll_explanation = """
***Info:***
This will create poll that will only accept responses 
within a specified amount of time, either with Yes/No or 
Multiple Choice questions.

**Usage:** 
`7/poll <duration: in seconds> "<custom question>" -yn {end} `
`7/poll <duration: in seconds> "<custom question>" -mc <options 1-10> {end}`

**Example:**
`7/sudo 25 "Dogs, Cats, or neither?" -mc dogs cats neither`

***Tip:***
- Don't try to ping a role in the question, 
  it will not work, do it beforehand.
"""


@bot.command(help="This command creates a poll",
             usage="7/poll <duration> <question> -yn / -mc <options 1-10>")
@has_any_role('7xControlPass', 'Canis', 'Xar', "7x Waitlist")
async def poll(ctx, *args):
  if args and args[0].lower() == "help":
    embed = discord.Embed(title="Poll Command",
                          description=poll_explanation,
                          color=0x00ff00)
    await ctx.send(embed=embed)
    return

  if len(args) < 2:
    await ctx.send("Incorrect usage. For detailed help, type: `7/poll help`")
    return

  try:
    duration = int(args[0])
    question = args[1]
  except (ValueError, IndexError):
    await ctx.send("Invalid usage. Please specify a duration and a question.")
    return

  if "-yn" in args:
    options = ["Yes", "No"]
    reactions = ['✅', '❌']
    await ctx.message.delete()
  elif "-mc" in args:
    try:
      mc_index = args.index("-mc") + 1
      question = ' '.join(args[:mc_index - 1])
      options = args[mc_index:]
      if len(options) < 2:
        raise ValueError("Multiple choice polls require at least two options.")
      reactions = [
          '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'
      ][:len(options)]
    except ValueError as e:
      await ctx.send(str(e))
      return
    await ctx.message.delete()
  else:
    await ctx.send("Invalid usage. For detailed help, type: `7/poll help`")
    return

  description = []
  for x, option in enumerate(options):
    description += f'\n{reactions[x]} {option}'
  embed = discord.Embed(title=question, description=''.join(description))
  react_message = await ctx.send(embed=embed)
  for reaction in reactions[:len(options)]:
    await react_message.add_reaction(reaction)

  await asyncio.sleep(duration)
  react_message = await ctx.channel.fetch_message(react_message.id)

  results = {}
  for reaction in react_message.reactions:
    if str(reaction.emoji) in reactions:
      results[str(reaction.emoji)] = reaction.count - 1

  winner = max(results.items(), key=lambda x: x[1])[0] if results else None
  results_description = '\n'.join(
      [f'{emoji} - {count} votes' for emoji, count in results.items()])
  results_embed = discord.Embed(
      title=f"The winning option is: {winner} with {results[winner]} votes!",
      description=results_description)
  await ctx.send(embed=results_embed)


bot.run(my_secret)
