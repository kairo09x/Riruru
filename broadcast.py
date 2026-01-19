import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from database import supabase, get_served_users

log = logging.getLogger(__name__)

# Helper: Agla available slot nikalne ke liye
async def get_next_slot():
    # Hum check karenge ki database mein last entry kis slot ki hai
    res = supabase.table("broadcast_slots").select("slot_id").order("id", desc=True).limit(1).execute()
    if not res.data:
        return 1
    last_slot = res.data[0]["slot_id"]
    return 1 if last_slot >= 3 else last_slot + 1

async def broadcast_send(client, message):
    if not message.reply_to_message:
        return await message.reply("👉 **Reply to a message to broadcast it.**")

    all_users = get_served_users()
    slot = await get_next_slot()
    
    m = await message.reply(f"🚀 **Broadcasting in Slot {slot}...**\nTarget: {len(all_users)} Users")

    # Agar is slot mein pehle se data hai (purana rotation), toh use delete karein
    supabase.table("broadcast_slots").delete().eq("slot_id", slot).execute()

    count = 0
    blocked = 0

    for user_id in all_users:
        try:
            sent_msg = await message.reply_to_message.copy(user_id)
            # Database mein entry save karein delete karne ke liye
            supabase.table("broadcast_slots").insert({
                "slot_id": slot,
                "user_id": user_id,
                "msg_id": sent_msg.id
            }).execute()
            
            count += 1
            # Rate limiting se bachne ke liye (30k users safety)
            if count % 20 == 0:
                await asyncio.sleep(1) 
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except (UserIsBlocked, InputUserDeactivated):
            blocked += 1
        except Exception:
            pass

    await m.edit(f"✅ **Broadcast Completed!**\n\nSlot: `{slot}`\nSent: `{count}`\nBlocked: `{blocked}`\n\n*Note: Agla broadcast Slot {(slot % 3) + 1} mein jayega.*")

async def broadcast_delete(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ **Usage:** `/del_dm 1` (1, 2, or 3)")

    slot = message.command[1]
    if slot not in ["1", "2", "3"]:
        return await message.reply("❌ Sirf Slot 1, 2 ya 3 hi delete ho sakta hai.")

    # Data fetch karein
    res = supabase.table("broadcast_slots").select("user_id", "msg_id").eq("slot_id", int(slot)).execute()
    
    if not res.data:
        return await message.reply(f"📭 Slot {slot} khali hai ya pehle hi delete ho chuka hai.")

    m = await message.reply(f"🗑 **Deleting messages from Slot {slot}...**")
    
    deleted = 0
    for row in res.data:
        try:
            await client.delete_messages(row["user_id"], row["msg_id"])
            deleted += 1
            if deleted % 20 == 0:
                await asyncio.sleep(1)
        except Exception:
            pass

    # DB saaf karein
    supabase.table("broadcast_slots").delete().eq("slot_id", int(slot)).execute()
    await m.edit(f"✅ **Slot {slot} Cleaned!**\nTotal Deleted: `{deleted}`")

async def get_stats(client, message):
    res = supabase.table("users").select("user_id", count="exact").execute()
    total = res.count or 0
    await message.reply(f"📊 **Bot Current Stats:**\n\nTotal Users: `{total}`\nBroadcast Slots: `3` (Rotating)")
