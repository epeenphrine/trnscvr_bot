from discord.ext import commands
import discord
import re
import json 
import random
import time 

# local import 
from tokens import dev, prod

with open('companies_filtered.json') as f:
    companies_filtered_json = json.load(f) # this is a list


client = commands.Bot(command_prefix='!')
@client.command()
async def test(ctx):
    await ctx.send('testing')
    pass
message2 = 'strikes marked with * means good value'
@client.command()
async def calliebot(ctx, *arg): # <--- *arg stores arguments as tuples. Check print statements to see how it works

    print('in calliebot')
    print(arg) # <--- tuple. access tuple like a list/array 

    if arg:
        roles = ctx.guild.roles # <--- get server roles
        author_role = ctx.author.roles # <-- all message author roles
        #print(author_role) 

        if arg[0] == '20':
            message = "`this is me helping your dumb ass \n `"
            await ctx.send(message.upper())

        if arg[0] == '14':
            try:
                print('in try')
                print(arg[1])
                if arg[1].lower() == 'er':
                    print('in if')
                    message = ""
                    for company in companies_filtered_json:
                        if "(ER:" in company:
                            message += f"{company} \n"
                    await ctx.send(f'`callie earnings within 14 days | {message2}`')
                    await ctx.send(message)
            except:
                print('in except')
                message = ""
                for company in companies_filtered_json:
                    if "*" in company:
                        message += f"**{company} \n**"
                    else:
                        message += f"{company} \n"
                await ctx.send(f'`callies within 14 days | {message2}`')
                await ctx.send(message)

        #if re.match('\<\@\!\d+\>', arg[0]) and ('administrator' in str(author_role)):
            #print('in re.match')
            #print(author_role)
            #print(arg[0])
            #user_id = arg[0]
            #message = random.choice(shitposts)
            #print(message)
            #await ctx.send(f"{user_id} {message.upper()}")

    else:
        await ctx.send('nada')

# prod
client.run(prod)
# dev
#client.run(dev)