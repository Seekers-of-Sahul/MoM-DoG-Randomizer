-- Master of Monsters: Disciples of Gaia rando - BizHawk debug tool (PS1, MainRAM), BizHawk 2.9+
-- Shows the hub state kept in the saved story flags (overlay) and opens a small window with buttons to edit
-- it the way an Archipelago client would. No keyboard hotkeys, so it can't clash with your controls.
-- Unlocks take effect the next time the hub list is built (after a battle or when loading a save).

local HUB_IDS = {}
for b = 1, 22 do HUB_IDS[#HUB_IDS + 1] = b end
for b = 26, 28 do HUB_IDS[#HUB_IDS + 1] = b end

local F_BASE, version, MBOX = nil, "?", nil   -- story flags F[0..99] (byte array), saved with every save
-- MBOX: Archipelago mailbox (8 x id, level; id 255 = empty), only in seeds made with --mailbox
local function detect()
  -- the Map Mode label template "MAP01" sits at a different address on each disc
  if memory.read_u32_le(0x16E34, "MainRAM") == 0x3050414D then return 0x0CE0E8, "PAL", 0x0661A4 end
  if memory.read_u32_le(0x16EA4, "MainRAM") == 0x3050414D then return 0x0CDF38, "US", 0x065FF4 end
  return nil, "?", nil
end
local function has_mbox()
  if not MBOX then return false end
  for k = 0, 7 do
    local id = memory.read_u8(MBOX + 2 * k, "MainRAM")
    if id ~= 255 and id >= 136 then return false end
  end
  return true
end

-- Puts a monster in the first free mailbox entry; the game hands it over at the next post-battle unit
-- screen, hub, or between-battle load. Level first, then the id (the game reads the id).
local function send_monster(id, lv)
  if not has_mbox() then console.log("no mailbox in this seed (make it with --mailbox)"); return end
  for k = 0, 7 do
    if memory.read_u8(MBOX + 2 * k, "MainRAM") == 255 then
      memory.write_u8(MBOX + 2 * k + 1, lv, "MainRAM")
      memory.write_u8(MBOX + 2 * k, id, "MainRAM")
      console.log(string.format("queued monster %d at level %d", id, lv)); return
    end
  end
  console.log("mailbox full")
end
local function pending()
  local n = 0
  if has_mbox() then for k = 0, 7 do if memory.read_u8(MBOX + 2 * k, "MainRAM") ~= 255 then n = n + 1 end end end
  return n
end

local function rd32(o) return memory.read_u32_le(F_BASE + o, "MainRAM") end
local function wr32(o, v) memory.write_u32_le(F_BASE + o, v, "MainRAM") end
local function list(mask)
  local t = {}
  for b = 0, 28 do if (mask >> b) & 1 == 1 then t[#t + 1] = tostring(b) end end
  return table.concat(t, " ")
end

local function unlock_all()
  if not F_BASE then return end
  local m = 0
  for _, b in ipairs(HUB_IDS) do m = m | (1 << b) end
  wr32(60, m)
end
local function unlock_next()
  if not F_BASE then return end
  local unl = rd32(60)
  for _, b in ipairs(HUB_IDS) do
    if (unl >> b) & 1 == 0 then wr32(60, unl | (1 << b)); return end
  end
end
local function lock_all() if F_BASE then wr32(60, 0) end end

-- Writes the whole 2 MB of main RAM to a file next to BizHawk's exe (for map/tower analysis).
local dumps = 0
local function dump_ram()
  dumps = dumps + 1
  local name = string.format("mom_ram_%s_%d_%d.bin", version, emu.framecount(), dumps)
  local f = io.open(name, "wb")
  if not f then console.log("can't write " .. name); return end
  local size, chunk = 0x200000, 0x10000
  for base = 0, size - 1, chunk do
    local t = memory.read_bytes_as_array(base, chunk, "MainRAM")
    local parts = {}
    for i = 1, #t, 4096 do
      parts[#parts + 1] = string.char(table.unpack(t, i, math.min(i + 4095, #t)))
    end
    f:write(table.concat(parts))
  end
  f:close()
  console.log("RAM dumped to " .. name)
end

local form = forms.newform(220, 290, "momrando debug")
forms.button(form, "Unlock next stage", unlock_next, 10, 10, 180, 25)
forms.button(form, "Unlock all stages", unlock_all, 10, 40, 180, 25)
forms.button(form, "Lock all stages", lock_all, 10, 70, 180, 25)
forms.button(form, "Dump RAM to file", dump_ram, 10, 100, 180, 25)
forms.label(form, "monster id / level", 10, 135, 180, 18)
local id_box = forms.textbox(form, "61", 60, 20, "UNSIGNED", 10, 155)
local lv_box = forms.textbox(form, "5", 60, 20, "UNSIGNED", 80, 155)
forms.button(form, "Send monster", function()
  send_monster(tonumber(forms.gettext(id_box)) or 61, tonumber(forms.gettext(lv_box)) or 1)
end, 10, 185, 180, 25)
forms.button(form, "Send random monster", function()
  send_monster(math.random(3, 135), math.random(1, 10))
end, 10, 215, 180, 25)
event.onexit(function() forms.destroy(form) end)

while true do
  if not F_BASE then F_BASE, version, MBOX = detect() end
  if F_BASE then
    local stage = memory.read_u8(F_BASE + 51, "MainRAM")
    local recv = memory.read_u16_le(F_BASE + 68, "MainRAM")
    gui.text(4, 4, string.format("momrando %s  F[51]=%d  monsters recv=%d  pending=%d", version, stage, recv, pending()))
    gui.text(4, 20, "unlocked: " .. list(rd32(60)))
    gui.text(4, 36, "cleared:  " .. list(rd32(64)))
  else
    gui.text(4, 4, "momrando: game not detected yet")
  end
  emu.frameadvance()
end
