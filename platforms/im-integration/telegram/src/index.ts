import { Telegraf } from "telegraf";
import { normalize } from "../../shared/src/message-normalizer";
const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN!);
bot.on("message", async (ctx) => { const msg = normalize("telegram", ctx.update); console.log("Telegram:", msg); await ctx.reply("Message received"); });
bot.launch();
