from telegram import ForceReply, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from player_list import PlayerList
from OFB import Role, Team, MAX_SCORE
import numpy as np
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

TOKEN = '6719307383:AAFdBCyEXu_Rp5fP9yWF6INQeK0PCX0-cJA'
PLAYERLIST = PlayerList()
LOG = logging.getLogger(__name__)

MATCH_DATA = []
ATK_1, DEF_1, ATK_2, DEF_2, SCORE_1, SCORE_2 = range(6)

def generate_player_buttons() -> ReplyKeyboardMarkup:
    # Create a list of InlineKeyboardButtons
    keyboard = [[p.name] for p in PLAYERLIST.DATA]
    # Create the reply markup with InlineKeyboardMarkup
    reply_markup = ReplyKeyboardMarkup(keyboard)
    return reply_markup


async def match_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    LOG.info("User %s initiated a match registration.", update.effective_user.first_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Sure. Let's add a new match.")
    MATCH_DATA.clear()
    await update.message.reply_text('Who was the attacker on the first team?', reply_markup=generate_player_buttons())
    return ATK_1

async def atk_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_DATA.append(PLAYERLIST.search_by_name(response))
    await update.message.reply_text('Who was the defender on the first team?', reply_markup=generate_player_buttons())
    return DEF_1

async def def_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_DATA.append(PLAYERLIST.search_by_name(response))
    await update.message.reply_text('Who was the attacker on the second team?', reply_markup=generate_player_buttons())
    return ATK_2

async def atk_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_DATA.append(PLAYERLIST.search_by_name(response))
    await update.message.reply_text('Who was the defender on the second team?', reply_markup=generate_player_buttons())
    return DEF_2

async def def_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_DATA.append(PLAYERLIST.search_by_name(response))
    await update.message.reply_text('How much did the first team score?')
    return SCORE_1

async def score_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_DATA.append(int(response))
    await update.message.reply_text('How much did the second team score?')
    return SCORE_2

async def score_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_DATA.append(int(response))
    
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Match added successfully. Calculating new Elo scores...")
        PLAYERLIST.resolve_match(Team(MATCH_DATA[0], MATCH_DATA[1]), Team(MATCH_DATA[2], MATCH_DATA[3]), MATCH_DATA[4], MATCH_DATA[5])
        LOG.info("User %s successfully registered a match.", update.effective_user.first_name)
        await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Here are the new Elo scores:")
        message = f"{MATCH_DATA[0].name}'s ATK Elo: {int(MATCH_DATA[0].atk_elo)}\n" + \
                f"{MATCH_DATA[1].name}'s DEF Elo: {int(MATCH_DATA[1].def_elo)}\n" + \
                f"{MATCH_DATA[2].name}'s ATK Elo: {int(MATCH_DATA[2].atk_elo)}\n" + \
                f"{MATCH_DATA[3].name}'s DEF Elo: {int(MATCH_DATA[3].def_elo)}\n"
        PLAYERLIST.save_file()
        await context.bot.send_message(chat_id=update.effective_chat.id, text = message)
    except:
        LOG.error("User %s encountered an error while registering a match.", update.effective_user.first_name)
        await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"There was a problem while adding your match. No data was stored.")
    return ConversationHandler.END

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    role_dict = {"ATK": Role.ATK,
                 "DEF": Role.DEF}
    
    role = ''.join(context.args)
    if role not in role_dict:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f"The 'leaderboard' command accepts ATK or DEF as arguments. Try this:\n/leaderboard ATK\n/leaderboard DEF")
        return
    
    LOG.info(f"User {update.effective_user.first_name} requested the leaderboard for role {role}.")
    board = PLAYERLIST.leaderboard(role_dict[role])
    if not board:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f'The board is empty!')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f"Here's the leaderboard for the {role} role:")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f'\n'.join([f"{p.name}: {int(p.elo(role_dict[role]))}" for p in board]))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Greet user and load playerlist
    user = update.effective_user
    await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Hi {user.full_name}!")
    await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Loading Player List...")
    PLAYERLIST.load_file()
    await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Player List loaded.")


async def playerlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Print playerlist
    player_list = PLAYERLIST.DATA
    if not player_list:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f'The player list is empty!')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f"Here's the list of players:")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f'\n'.join([p.name for p in player_list]))


async def addplayer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Add a player. Argument needs to follow the command call i.e.
    # /addplayer New Player Name
    player_name = ' '.join(context.args)
    LOG.info(f"User {update.effective_user.first_name} added player {player_name} to the playerlist.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=rf"Adding player {player_name}...")
    PLAYERLIST.add_new_player(player_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=rf"Player {player_name} was added.")
    PLAYERLIST.save_file()


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    LOG.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Match registration has been canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I don't understand that command.")


def main():
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()
    
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("match", match_start))
    application.add_handler(CommandHandler("addplayer", addplayer))
    application.add_handler(CommandHandler("playerlist", playerlist))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    
    match_convo = ConversationHandler(
        entry_points=[CommandHandler("addmatch", match_start)],
        states={
            ATK_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, atk_1)],
            DEF_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, def_1)],
            ATK_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, atk_2)],
            DEF_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, def_2)],
            SCORE_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, score_1)],
            SCORE_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, score_2)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(match_convo)
    
    # These MUST be the last handlers added or they will trigger before other commands.
    application.add_handler(MessageHandler(filters.COMMAND, unknown))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()