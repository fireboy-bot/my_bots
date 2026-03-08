# handlers/dev_bosses.py
from telegram import Update
from telegram.ext import ContextTypes
from handlers.bosses import start_boss_battle
from handlers.true_lord_battle import start_battle as start_true_lord_battle

async def dev_boss_null(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "null_void")

async def dev_boss_minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "minus_shadow")

async def dev_boss_multiply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "evil_multiplier")

async def dev_boss_fracosaur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "fracosaur")

async def dev_boss_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "final_boss")

async def dev_boss_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "time_keeper")

async def dev_boss_measure(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "measure_keeper")

async def dev_boss_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_boss_battle(update, context, "logic_keeper")

async def dev_boss_true_lord(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_true_lord_battle(update, context)