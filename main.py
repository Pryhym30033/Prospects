from playwright.sync_api import sync_playwright, Browser
from playwright_stealth import Stealth
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
import os
import uuid

#-----------Core load/save----------------
filepath = "minors.json"

def load(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {"levels":[],"leagues":[], "teams":[], "players":[]}

def save(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def addLevel(filepath, name, id):
    data = load(filepath)
    if any(l["name"] == name for l in data['levels']):
        raise ValueError(f"{name} already exists")
    data["levels"].append({"name":name, "id":id})
    save(filepath, data)
    return data

def addLeague(filepath, name, id, level):
    data = load(filepath)
    if any(l['name']==name for l in data['leagues']):
        raise ValueError(f"{name} already exists")
    data['leagues'].append({"name":name, "id":id, "level":level})
    save(filepath, data)
    return data

def addTeam(filepath, name, aff, league):
    data = load(filepath)
    # if any(l['name']==name for l in data['teams']):
    #     raise ValueError(f"{name} already exists")
    data['teams'].append({"names":name, "aff":aff, "league":league})
    save(filepath, data)
    return data

def getLevels():

    minor = load(filepath)
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.mlb.com/milb/about/teams/by-league')

        section = page.locator(".l-grid__col.l-grid__col--sm-3.l-grid__col--md-3.l-grid__col--lg-3.l-grid__col--xl-3.l-grid__col--transparent")
        count = section.count()


        for i in range(count):
            data.append(section.nth(i).locator("h3").first.inner_text())
        browser.close()

    names = [item.get('name') for item in minor['levels']]
    levels = [item for item in data if item not in names]

    for level in levels:
        match level:
            case "Double-A":
                addLevel(filepath, level, "AA")
            case "High-A":
                addLevel(filepath, level, "A+")
            case "Single-A":
                addLevel(filepath, level, "A")

def getLeagues():
    leagues = []
    minor = load(filepath)
    minor['leagues'] = []
    save(filepath, minor)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.mlb.com/milb/about/teams/by-league')

        section = page.locator(".l-grid__col.l-grid__col--sm-3.l-grid__col--md-3.l-grid__col--lg-3.l-grid__col--xl-3.l-grid__col--transparent")
        panels = section.locator(".l-grid__content")
        pCount = panels.count()
        lvl = {0:"AAA", 1:"AA", 2:"A+", 3:"A"}
        for i in range(pCount):
            headers = panels.nth(i).locator(".p-heading__text--none")
            level = lvl[i]
            count = headers.count()
            for j in range(count):
                leagues.append({"lg":headers.nth(j).inner_text(), "lv":level})

        browser.close()

        for league in leagues:
            addLeague(filepath, league['lg'], "".join([word[0] for word in league['lg'].split()]), league['lv'])

    correct = load(filepath)
    correct['leagues'][9]['id'] = "CrL"
    save(filepath, correct)

def getTeams():
    minor = load(filepath)
    minor['teams'] = []
    save(filepath, minor)
    with open('sym.json', 'r') as f:
        sym = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.mlb.com/milb/about/teams/by-league')



        lg = {
            0:"IL",
            1:"PCL",
            2:"EL",
            3:"SL",
            4:"TL",
            5:"ML",
            6:"NL",
            7:"SAL",
            8:"CL",
            9:"CrL",
            10:"FSL"
        }

        section = page.locator(".p-wysiwyg")
        count = section.count() - 1
        for i in range(count):
            leag = section.nth(i)
            list = leag.get_by_role("listitem")
            lcount = list.count()
            for j in range(lcount):
                team = list.nth(j).get_by_role("link").inner_text()
                addTeam(filepath, team, sym[team], lg[i])

        browser.close()

def fangraphLogin():

    load_dotenv()
    user = os.environ["UserName"]
    pswd = os.environ["PASS"]

    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.fangraphs.com/")
        page.locator("[data-sub='login']").click()
        page.wait_for_selector("#user_login",  timeout=10000).fill(user)
        page.wait_for_selector("#user_pass").fill(pswd)
        page.get_by_role("button", name="Sign In").click()

        context.storage_state(path="auth.json")
        browser.close()


def getFangraphData():

    with Stealth().use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state="auth.json")
        page = context.new_page()
        page.goto("https://www.fangraphs.com/prospects/the-board")
        item = page.locator(".page-item-control")
        item.get_by_role("combobox").nth(1).select_option(label="Infinity")
        page.wait_for_timeout(2000)
        with page.expect_download() as download_info:
            page.locator(".data-export").click()
        download = download_info.value
        download.save_as("/home/pcm30033/Pryhym30033/pycharm/Prospects/data/scout.csv")

        page.goto("https://www.fangraphs.com/leaders/minor-league")
        item2 = page.locator(".page-item-control")
        item2.get_by_role("combobox").nth(1).select_option(label="Infinity")
        page.wait_for_timeout(2000)
        with page.expect_download() as download_info2:
            page.locator(".data-export").click()
            download2 = download_info2.value
            download2.save_as("/home/pcm30033/Pryhym30033/pycharm/Prospects/data/standard.csv")

        page.goto("https://www.fangraphs.com/leaders/minor-league?type=1")
        item3 = page.locator(".page-item-control")
        item3.get_by_role("combobox").nth(1).select_option(label="Infinity")
        page.wait_for_timeout(2000)
        with page.expect_download() as download_info3:
            page.locator(".data-export").click()
            download3 = download_info3.value
            download3.save_as("/home/pcm30033/Pryhym30033/pycharm/Prospects/data/advanced.csv")

        browser.close()

getFangraphData()