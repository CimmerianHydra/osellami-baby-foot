from telegram import ForceReply, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from player_list import PlayerList
from OFB import Role, Team, MAX_SCORE
from bot_token import TOKEN
from datetime import datetime
from functools import wraps
import pickle as pk
import os
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filemode='a'
)
logging.getLogger("httpx").setLevel(logging.WARNING)

PLAYERLIST = PlayerList()
LOG = logging.getLogger(__name__)

MATCH_CONVO_DICT = {}
ATK_1, DEF_1, ATK_2, DEF_2, SCORE_1, SCORE_2 = range(6)

WHITELIST_PATH = "whitelist.bin"
WHITELIST = {'admin':[145267299],'user':[]}

def generate_player_buttons() -> ReplyKeyboardMarkup:
    # Create a list of InlineKeyboardButtons
    keyboard = [[p.name] for p in PLAYERLIST.DATA]
    # Create the reply markup with InlineKeyboardMarkup
    reply_markup = ReplyKeyboardMarkup(keyboard)
    return reply_markup

def start_log() -> None:
    # Create a log folder if it doesn't exist
    log_folder = 'logs'
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # Generate log file name using the current date and time
    log_file_name = datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '_log.txt'
    log_file_path = os.path.join(log_folder, log_file_name)

    # Create a file handler and set the level to DEBUG
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)

    # Create a formatter and set the formatter for the handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add the file handler to the logger
    LOG.addHandler(file_handler)

def user_restricted(func):
    @wraps(func)
    def wrapped(update: Update, context: ContextTypes, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in WHITELIST['user']:
            LOG.info("User with ID %s attempted to run a user restricted command. User was denied access.", update.effective_user.id)
            return restricted_msg(update, context)
        return func(update, context, *args, **kwargs)
    return wrapped

def admin_restricted(func):
    @wraps(func)
    def wrapped(update: Update, context: ContextTypes, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in WHITELIST['admin']:
            LOG.info("User with ID %s attempted to run an admin restricted command. User was denied access.", update.effective_user.id)
            return restricted_msg(update, context)
        return func(update, context, *args, **kwargs)
    return wrapped

def load_whitelist():
    global WHITELIST
    with open(WHITELIST_PATH, 'rb') as f:
        WHITELIST = pk.load(f)

@admin_restricted
async def add_user_to_whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    userid = ''.join(context.args)
    LOG.info(f"User {update.effective_user.first_name} added user {userid} to the playerlist.")
    WHITELIST["user"].append(int(userid))
    with open(WHITELIST_PATH, 'wb') as f:
        pk.dump(WHITELIST, f)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=rf"User with ID {userid} was added to the users list.")

@user_restricted
async def match_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    LOG.info("User %s initiated a match registration.", update.effective_user.first_name)
    
    if not PLAYERLIST.DATA:
        await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"The player list is empty. Please run the /start command!")
        return ConversationHandler.END
        
    await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Sure. Let's add a new match.")
    MATCH_CONVO_DICT[update.effective_user.id] = []
    await update.message.reply_text('Who was the attacker on the green team?', reply_markup=generate_player_buttons())
    return ATK_1

async def atk_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_CONVO_DICT[update.effective_user.id].append(PLAYERLIST.search_by_name(response))
    await update.message.reply_text('Who was the defender on the green team?', reply_markup=generate_player_buttons())
    return DEF_1

async def def_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_CONVO_DICT[update.effective_user.id].append(PLAYERLIST.search_by_name(response))
    await update.message.reply_text('Who was the attacker on the yellow team?', reply_markup=generate_player_buttons())
    return ATK_2

async def atk_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_CONVO_DICT[update.effective_user.id].append(PLAYERLIST.search_by_name(response))
    await update.message.reply_text('Who was the defender on the yellow team?', reply_markup=generate_player_buttons())
    return DEF_2

async def def_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_CONVO_DICT[update.effective_user.id].append(PLAYERLIST.search_by_name(response))
    await update.message.reply_text('How much did the green team score?')
    return SCORE_1

async def score_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_CONVO_DICT[update.effective_user.id].append(int(response))
    await update.message.reply_text('How much did the yellow team score?')
    return SCORE_2

async def score_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    response = update.message.text
    MATCH_CONVO_DICT[update.effective_user.id].append(int(response))
    
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Match added successfully. Calculating new Elo scores...")
        PLAYERLIST.resolve_match(Team(MATCH_CONVO_DICT[update.effective_user.id][0], MATCH_CONVO_DICT[update.effective_user.id][1]),
                                 Team(MATCH_CONVO_DICT[update.effective_user.id][2], MATCH_CONVO_DICT[update.effective_user.id][3]),
                                 MATCH_CONVO_DICT[update.effective_user.id][4],
                                 MATCH_CONVO_DICT[update.effective_user.id][5])
        data = MATCH_CONVO_DICT[update.effective_user.id]
        MATCH_CONVO_DICT[update.effective_user.id] = []
        LOG.info("User %s successfully registered a match.", update.effective_user.first_name)
        await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Here are the new Elo scores:")
        message = f"{data[0].name}'s ATK Elo: {int(data[0].atk_elo)}\n" + \
                  f"{data[1].name}'s DEF Elo: {int(data[1].def_elo)}\n" + \
                  f"{data[2].name}'s ATK Elo: {int(data[2].atk_elo)}\n" + \
                  f"{data[3].name}'s DEF Elo: {int(data[3].def_elo)}\n"
        PLAYERLIST.save_file()
        await context.bot.send_message(chat_id=update.effective_chat.id, text = message)
    except:
        MATCH_CONVO_DICT[update.effective_user.id] = []
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


@admin_restricted
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Greet user and load playerlist
    user = update.effective_user
    await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Hi {user.full_name}!")
    await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Loading data...")
    PLAYERLIST.load_file()
    start_log()
    await context.bot.send_message(chat_id=update.effective_chat.id, text = rf"Data loaded.")


async def playerlist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Print playerlist
    player_list = PLAYERLIST.DATA
    LOG.info(f"User {update.effective_user.first_name} requested the playerlist.")
    if not player_list:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f'The player list is empty. Please run the /start command!')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f"Here's the list of players:")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                        text = f'\n'.join([p.name for p in player_list]))


@admin_restricted
async def addplayer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Add a player. Argument needs to follow the command call i.e.
    # /addplayer New Player Name
    player_name = ' '.join(context.args)
    LOG.info(f"User {update.effective_user.first_name} added player {player_name} to the playerlist.")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=rf"Adding player {player_name}...")
    PLAYERLIST.add_new_player(player_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=rf"Player {player_name} was added.")
    PLAYERLIST.save_file()


@user_restricted
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    MATCH_CONVO_DICT[update.effective_user.id] = []
    LOG.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text("Match registration has been canceled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I don't understand that command.")

async def restricted_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, you don't have the permission to use that command.")


def main():
    # Loading data
    load_whitelist()
    PLAYERLIST.load_file()
    start_log()
    
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()
    
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("restart", restart))
    application.add_handler(CommandHandler("match", match_start))
    application.add_handler(CommandHandler("addplayer", addplayer))
    application.add_handler(CommandHandler("playerlist", playerlist))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    application.add_handler(CommandHandler("adduser", add_user_to_whitelist))
    
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