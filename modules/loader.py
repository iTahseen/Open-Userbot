import os
import shutil
import subprocess
import sys
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import restart

BASE_PATH = os.path.abspath(os.getcwd())
MODULES_PATH = os.path.join(BASE_PATH, 'modules', 'custom_modules')

def fetch_url(url: str):
    """Fetch content from a URL with error handling."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        return None

def save_file(path: str, content: bytes):
    """Save content to a file."""
    with open(path, 'wb') as f:
        f.write(content)

@Client.on_message(filters.command(["modhash", "mh"], prefix) & filters.me)
async def get_mod_hash(_, message: Message):
    if len(message.command) != 2:
        await message.edit("<b>Usage: /modhash <URL></b>")
        return

    url = message.command[1].lower()
    resp = fetch_url(url)
    if not resp:
        await message.edit(f"<b>Unable to fetch module from <code>{url}</code></b>")
        return

    module_hash = hashlib.sha256(resp.content).hexdigest()
    file_name = url.split('/')[-1]
    await message.edit(
        f"<b>Module hash: <code>{module_hash}</code>\nLink: <code>{url}</code>\nFile: <code>{file_name}</code></b>"
    )

@Client.on_message(filters.command(["loadmod", "lm"], prefix) & filters.me)
async def load_mod(_, message: Message):
    if not (message.reply_to_message and message.reply_to_message.document and message.reply_to_message.document.file_name.endswith(".py")) and len(message.command) == 1:
        await message.edit("<b>Specify module to download or reply to a .py file</b>")
        return

    if len(message.command) > 1:
        url = message.command[1].lower()
        if url.startswith("https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/"):
            module_name = url.split("/")[-1].split(".")[0]
        elif "/" not in url and "." not in url:
            module_name = url.lower()
            url = f"https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/{module_name}.py"
        else:
            resp = fetch_url(url)
            if not resp:
                await message.edit(f"<b>Module <code>{module_name}</code> is not found</b>")
                return
            module_name = url.split("/")[-1].split(".")[0]

        resp = fetch_url(url)
        if not resp:
            await message.edit(f"<b>Module <code>{module_name}</code> is not found</b>")
            return

        os.makedirs(MODULES_PATH, exist_ok=True)
        save_file(os.path.join(MODULES_PATH, f"{module_name}.py"), resp.content)
    else:
        file_name = await message.reply_to_message.download()
        module_name = message.reply_to_message.document.file_name[:-3]
        os.rename(file_name, os.path.join(MODULES_PATH, f"{module_name}.py"))

    await message.edit(f"<b>The module <code>{module_name}</code> is loaded!</b>")
    restart()

@Client.on_message(filters.command(["unloadmod", "ulm"], prefix) & filters.me)
async def unload_mod(_, message: Message):
    if len(message.command) <= 1:
        await message.edit("<b>Usage: /unloadmod <module_name></b>")
        return

    module_name = message.command[1].lower()
    module_path = os.path.join(MODULES_PATH, f"{module_name}.py")

    if os.path.exists(module_path):
        os.remove(module_path)
        if module_name == "musicbot":
            subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "requirements.txt"], cwd=os.path.join(BASE_PATH, "musicbot"))
            shutil.rmtree(os.path.join(BASE_PATH, "musicbot"))
        await message.edit(f"<b>The module <code>{module_name}</code> removed!</b>")
        restart()
    else:
        await message.edit(f"<b>Module <code>{module_name}</code> is not found or is a built-in module</b>")

@Client.on_message(filters.command(["loadallmods"], prefix) & filters.me)
async def load_all_mods(_, message: Message):
    await message.edit("<b>Fetching info...</b>")
    os.makedirs(MODULES_PATH, exist_ok=True)

    modules_list_url = "https://api.github.com/repos/The-MoonTg-project/custom_modules/contents/"
    modules_list = fetch_url(modules_list_url)
    if not modules_list:
        await message.edit("<b>Failed to fetch module list</b>")
        return

    modules_list = modules_list.json()
    new_modules = {}
    for module_info in modules_list:
        if module_info["name"].endswith(".py") and not os.path.exists(os.path.join(MODULES_PATH, module_info["name"])):
            new_modules[module_info["name"][:-3]] = module_info["download_url"]

    if not new_modules:
        await message.edit("<b>All modules are already loaded</b>")
        return

    await message.edit(f'<b>Loading new modules: {" ".join(new_modules.keys())}</b>')
    for name, url in new_modules.items():
        resp = fetch_url(url)
        if resp:
            save_file(os.path.join(MODULES_PATH, f"{name}.py"), resp.content)

    await message.edit(f'<b>Successfully loaded new modules: {" ".join(new_modules.keys())}</b>')
    restart()

@Client.on_message(filters.command(["updateallmods"], prefix) & filters.me)
async def update_all_mods(_, message: Message):
    await message.edit("<b>Updating modules...</b>")
    os.makedirs(MODULES_PATH, exist_ok=True)

    modules_installed = [f for f in os.listdir(MODULES_PATH) if f.endswith(".py")]
    if not modules_installed:
        await message.edit("<b>No modules installed</b>")
        return

    for module_name in modules_installed:
        url = f"https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/{module_name}"
        resp = fetch_url(url)
        if resp:
            save_file(os.path.join(MODULES_PATH, module_name), resp.content)

    await message.edit(f"<b>Successfully updated {len(modules_installed)} modules</b>")

modules_help["loader"] = {
    "loadmod [module_name]*": "Download module from URL or reply to a .py file.",
    "unloadmod [module_name]*": "Delete specified module.",
    "modhash [link]*": "Get SHA-256 hash of the file at the specified URL.",
    "loadallmods": "Load all available custom modules from the repository.",
    "updateallmods": "Update all installed custom modules from the repository.",
}
