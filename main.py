from senpy import GogoClient
from InquirerPy import prompt # pip install InquirerPy
from InquirerPy.base.control import Choice
from InquirerPy.validator import PathValidator
from colorama import init, Fore, init # pip install colorama
from senpy import __version__
from plyer import notification # pip install plyer
from pathlib import Path
from io import StringIO
import subprocess
import json
import time
import sys
import re


init(autoreset=True)
client = GogoClient()

def header() -> None:
    """Prints the header of the application. Took a long time to style not gonna lie xD"""
    client.utils.clear()
    print(f"""
    \t\t{Fore.WHITE} _____           {Fore.LIGHTBLUE_EX}________   __
    \t\t{Fore.WHITE}/  ___|          {Fore.LIGHTBLUE_EX}| ___ \ \ / /
    \t\t{Fore.WHITE}\ `--. {Fore.GREEN} ___ {Fore.RED}_ __ {Fore.LIGHTBLUE_EX}| |_/ /\ V / 
    \t\t{Fore.WHITE} `--. \{Fore.GREEN}/ _ \{Fore.RED} '_ \{Fore.YELLOW}|  __/  \ /  
    \t\t{Fore.WHITE}/\__/ /{Fore.GREEN}  __/{Fore.RED} | | {Fore.YELLOW}| |     | |  
    \t\t{Fore.WHITE}\____/ {Fore.GREEN}\___|{Fore.RED}_| |_{Fore.YELLOW}\_|     \_/ {Fore.WHITE}v{__version__}  

\t {Fore.GREEN}Developer: {Fore.WHITE}</Rudransh Joshi> {Fore.YELLOW}(FireHead90544)
{Fore.YELLOW} _____________________________________________________________                             
{Fore.BLUE} _____  ___  _____   {Fore.CYAN}___ _____ _ __  __   ___________ ________ 
{Fore.BLUE} |__||\ |||\/||___   {Fore.CYAN}|  \|  || | ||\ ||   |  ||__||  \|___|__/ 
{Fore.BLUE} |  || \|||  ||___   {Fore.CYAN}|__/|__||_|_|| \||___|__||  ||__/|___|  \ 
{Fore.YELLOW} _____________________________________________________________
                                                                
    """)


def home():
    """
    The home-something of this application, all the cool stuff happens here.
    """
    header()
    questions = [
        {
            "type": "list",
            "name": "action",
            "message": "Select an action: ",
            "choices": [
                            Choice(download_anime, name="Download an Anime"), 
                            Choice(update_configs, name="Update Config File"),
                            Choice(sys.exit, name="Exit")
            ]
        }
    ]
    result = prompt(questions=questions, style=client.config.stylesheet)
    result['action']()

def update_configs() -> None:
    """
    Updates the config file and it's contents in a cool way, sheeeeeeeeesh :)
    """
    header()
    print(f"{Fore.GREEN}>>> Update Config File...")
    questions = [
        {
            "type": "input",
            "message": "Enter your gogoanime-registered email:",
            "name": "user_email",
            "validate": lambda result: bool(re.match(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$", result)),
            "invalid_message": "Invalid email address."
        },
        {
            "type": "password",
            "message": "Enter the password associated with above email:",
            "name": "user_password",
            "transformer": lambda _: "[hidden]",
            "validate": lambda result: len(result) > 0,
            "invalid_message": "Input cannot be empty."
        },
        {
            "type": "filepath",
            "message": "Enter the path to the anime downloads directory:",
            "validate": PathValidator(is_dir=True, message="Input is not a directory"),
            "name": "downloads_dir",
            "only_directories": True,
        },
        {
            "type": "filepath",
            "message": "Enter the path to aria2's executable:",
            "name": "aria_2_path",
            "validate": PathValidator(is_file=True, message="Input is not a file"),
            "only_files": True,
        },
        {
            "type": "confirm",
            "name": "proceed",
            "message": "Are you sure you want to update the config file?",
            "default": True
        }
    ]
    results = prompt(questions=questions, style=client.config.stylesheet)
    new_conf = {
        "EMAIL": results['user_email'],
        "PASSWORD": results['user_password'],
        "DOWNLOADS_DIR": results['downloads_dir'],
        "ARIA_2_PATH": results['aria_2_path']
    }
    if results['proceed']:
        with open(client.config.config_path, "w") as f:
            json.dump(new_conf, f, indent=4, sort_keys=True)
        print(f"{Fore.GREEN}>>> Config file updated successfully. Please restart the application to apply changes.")
        client.utils.sleep(3)
        sys.exit()
    else:
        home()

def do_pre_checks() -> None:
    """
    Just checks to make sure the dependencies are present in the device
    and everything's okay, and prevents the program for running until everything's ok.
    """
    # Checking the aria2 installation
    try:
        old = sys.stdout
        sys.stdout = StringIO()
        subprocess.call([client.config.aria_2_path])
        sys.stdout = old
    except Exception:
        client.config.logger.critical("Aria2 is not found, update the config file, if required.")
        print(f"{Fore.RED}>>> Aria2 Not found, please install it and try again or Update it's path in config file, if haven't.")
        client.utils.sleep(5)
        header()

    # Checking if the downloads directory exists
    try:
        if not client.config.downloads_dir.exists():
            print(f"{Fore.RED}>>> Downloads directory does not exists, please create it, or update the config file.")
            client.config.logger.critical("Downloads directory does not exists, please create it, or update the config file.")
            client.utils.sleep(5)
            header()
    except Exception as e:
        client.config.logger.critical(f"Downloads directory does not exists, an error occured, Error: {e}")
        sys.exit()

def download_using_aria2(links: list, anime_dir: str) -> None:
    """Downloads the episodes using external downloader aria2
    Since the default python downloader (using requests) is tooooo slow as compared to aria2
    and would require me to use my brain tooo much and handle several validations
    because some of you will surely try to break the program.
    Aria2 is wickedly fast and easy to use, read more about it on it's docs.
    Communicates with aria2 using subprocess PIPE :)

    Args:
        links (list): The list of links of episodes to download.
    """
    start = time.perf_counter()
    download_dir = client.config.downloads_dir / anime_dir
    cmd = f"{client.config.aria_2_path} -s 16 -x 16 -j 16 --max-concurrent-downloads=6 -d \"{download_dir}\" -Z " + "\"" + "\" \"".join(links) + "\""
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    for line in p.stdout:
        print(line.decode('utf-8', errors='ignore').rstrip())
    p.wait()
    total_time = f"{round(time.perf_counter() - start, 2)}s"
    client.config.logger.info(f"Downloaded {len(links)} episodes to \"{download_dir.resolve()}\" in {total_time}")
    print(f"{Fore.GREEN}>>> Download Completed in {total_time} {Fore.WHITE}| Downloaded {Fore.GREEN}{len(links)} episodes{Fore.WHITE} to {Fore.RED}\"{download_dir.resolve()}\" {Fore.GREEN}<<<")
    # Some pyinstaller config for --onefile option
    try:
        base_path = Path(sys._MEIPASS)
    except Exception:
        base_path = Path(".")
    app_icon = base_path / "icon.ico"
    try:
        notification.notify(title="SenPY | Download Completed", message=f"Downloaded {len(links)} episode(s) to \"{str(download_dir.resolve())}\" in {total_time}", app_icon=str(app_icon.resolve()), timeout=10)
    except Exception as e:
        client.config.logger.error(f"Unable to send notification | Error: {e}") # silently ignore if unable to show notification
    client.utils.sleep(10)
    home()

def search_anime_and_get_episode_pages_links() -> tuple:
    """
    Searches for an anime, gets it's id, the number of episodes to download.
    And, proceeds to download them.
    """
    header()
    questions = [
        {
            "type": "input",
            "message": "Enter the name of Anime to search for:",
            "name": "anime_name",
            "validate": lambda result: len(result) > 0,
            "invalid_message": "Input cannot be empty."
        }
    ]
    result = prompt(questions=questions, style=client.config.stylesheet)
    results = client.anime_search(result['anime_name'])
    header()
    if len(results) == 0:
        print(f"\n>>> {Fore.RED}No results found. {Fore.WHITE}Please try again with another query.")
        client.utils.sleep(3)
        search_anime_and_get_episode_pages_links()
    else:
        print(f"\n{Fore.GREEN}>>> {Fore.WHITE}Found {Fore.GREEN}{len(results)} {Fore.WHITE}results:")
        questions = [
            {
                "type": "list",
                "name": "anime_id",
                "message": "Select the anime to download:",
                "choices": [Choice(r['id'], name=f"{r['name']} [Released: {r['released']}]") for r in results]
            }
        ]
        result = prompt(questions=questions, style=client.config.stylesheet)
        anime_id = result['anime_id']
        all_eps = client.get_all_episode_numbers(anime_id)
        print("\n")
        questions = [
            {
                "type": "list",
                "name": "episodes",
                "message": "Select the episode(s) to download:",
                "choices": [Choice("all", name=f"All Episodes ({len(all_eps)}, Excluding Bonus Episodes)"), Choice("custom", name=f"Custom (Range, Numbers)")]
            }
        ]
        result = prompt(questions=questions, style=client.config.stylesheet)
        if result['episodes'] == "custom":
            header()
            print(f">>> {Fore.RED}IMPORTANT: {Fore.WHITE}Please make sure that the {Fore.GREEN}episode actually exists{Fore.WHITE}, else you will get {Fore.RED}errors {Fore.WHITE}later.")
            eps = client.utils.string_to_sequence(prompt(questions=[{"type": "input", "message": "Enter the episode number/range to download [Can Include Bonus Episodes, e.g, 14.5] (e.g, 1-6, 6.5, 7, 10-12): ", "name": "episodes", "validate": lambda result: len(result) > 0, "invalid_message": "Input cannot be empty."}], style=client.config.stylesheet)['episodes'])
        else:
            eps = all_eps

        anime_dir = anime_id.replace("-", " ").title()
        return client.get_episode_pages_links(anime_id, eps), anime_dir
        

def download_anime() -> None:
    """
    Searches the anime, selects it and does some highly intellecual stuff
    and downloads the anime to your machine.
    In short, searches anime, fetches it's episodes and quality and downloads it.
    """
    do_pre_checks() # Makes sure everything's okay and program's ready to run.
    ep_pages_links, anime_dir = search_anime_and_get_episode_pages_links()
    header()
    questions = [
        {
            "type": "list",
            "name": "quality",
            "message": "Select the download quality of episodes:",
            "choices": [Choice(360, name="360p"), Choice(480, name="480p"), Choice(720, name="720p"), Choice(1080, name="1080p")]
        }
    ]
    print(f"\n>>> {Fore.RED}IMPORTANT: {Fore.WHITE}Please note that in case the chosen quality is not found for any episode, the next higher quality available will be downloaded. In case, that's not available, one previous available quality will be chosen.")
    result = prompt(questions=questions, style=client.config.stylesheet)
    print(f"\n>>> {Fore.GREEN}Fetching Download Links...")

    download_links = []
    for ep_link in ep_pages_links:
        quality_links = client.get_episode_quality_download_links(ep_link)
        qualities = [int(q.replace("p", "")) for q in quality_links.keys()] # Get the raw integers of the qualities available for easy comparision
        if quality_links == {}: # No links found, probably wrong episode number given, logged in the log file already
            pass

        if f"{result['quality']}p" in quality_links.keys():
            download_links.append(quality_links[f"{result['quality']}p"])
        else:
            try:
                quality = sorted([q for q in qualities if q > result['quality']])[0] # Get the next quality available
                client.config.logger.warning(f"{result['quality']}p quality not found, selected {quality}p instead for episode: {ep_link}.")
            except Exception:
                quality = sorted([q for q in qualities if q < result['quality']])[-1] # Get the previous quality available
                client.config.logger.warning(f"{result['quality']}p quality not found, selected {quality}p instead for episode: {ep_link}.")
            download_links.append(quality_links[f"{quality}p"])

    download_links = client.utils.fix_episode_download_names(download_links)

    client.config.logger.info("Logging the download links for aria2 experiments or other purposes if required.")
    client.config.logger.info(download_links)
    print(f"\n>>> {Fore.GREEN}Fetched Download Links. Starting Download in 10 seconds. Please do not close the window.")
    print(f"\n>>> {Fore.RED}If you are an experienced aria2 user, download links have also been logged in the log file, you can do stuffs with them later.")
    print(f"\n>>> {Fore.GREEN}Downloads a maximum of 6 episodes at a time to maximize speed and downloads.")
    client.utils.sleep(10)
    header()
    download_using_aria2(download_links, anime_dir) # The actual downloading here


if __name__ == "__main__":
    home() # Start all the oogling-boogling here lol :)